from collections import deque
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.metrics import pairwise_distances
from scipy.optimize import linear_sum_assignment
#import tensorflow as tf
from PySide2.QtCore import QThread, Signal
from scipy.spatial import distance

min_body_dots = 10

from macroControl import DEBUG_AI_INPUT_CONVERSION, SEQ_SIZE, MODEL_PATH, MAX_SEQ_NOISE_LEN, MODEL_SEQ_SIZE, CLUST_MIN_SAMPLES, CLUST_EPS

NO_CLUSTER = (False, [])
# format of Preditction : (T/F, [ [(x,y,z), clust_num, state], ... ])

# Class meant to store the fall detection results of all the tracks
class FallDetection:
    def __init__(self, peopleTrack):
        self.seq_size = SEQ_SIZE
        self.seq_list = []
        self.data = []
        self.peopleTrack = peopleTrack

        # AI model
        self.model = self._load_model()

        # to prevent inference load
        self.isSlotRunning = False

        self.output = NO_CLUSTER

        # to check noise count
        self.noise_cnt = 0

    #모델 로드
    def _load_model(self):
        model = tf.keras.models.load_model(MODEL_PATH)
        print("Model loaded successfully.")
        return model
    
    def cluster_single_frame(self, frame_df):
        group_data = frame_df[['xPos', 'yPos']]

        dbscan = DBSCAN(eps=CLUST_EPS, min_samples=CLUST_MIN_SAMPLES)
        clusters = dbscan.fit_predict(group_data)
        frame_df['cluster'] = clusters
        clustered_data = frame_df[frame_df['cluster'] != -1]

        means_df = clustered_data.groupby('cluster')[['xPos', 'yPos']].mean()
        means = means_df.values.tolist()

        return (True, means)

    # Update the fall detection results for every track in the frame
    def step(self, outputDict):
        for key in ['numDetectedPoints', 'pointCloud']:
            key_check = outputDict.get(key)
            if key_check is None:
                return NO_CLUSTER
        num = outputDict['numDetectedPoints']
        if num <= 0:
            return NO_CLUSTER
        if len(self.seq_list) < self.seq_size:
            # append only
            self.seq_list.append(outputDict)

            frame_list = []
            for pointNum in range(num):
                point = [
                    outputDict['pointCloud'][pointNum][0], # Xpos
                    outputDict['pointCloud'][pointNum][1], # Ypos
                    # outputDict['pointCloud'][pointNum][2], # Zpos
                ]
                frame_list.append(point)

            frame_df = pd.DataFrame(frame_list, columns=['xPos','yPos'])

            return self.cluster_single_frame(frame_df)
        else:
            self.seq_list.append(outputDict)
            self.seq_list.pop(0)

        queue_list = []
        
        try:
            for idx, elem in enumerate(self.seq_list):
                num = elem['numDetectedPoints'] # pointNum
                if num <= 0:    # just in case
                    return NO_CLUSTER
                for pointNum in range(num):
                    point = [
                        idx + 1,    # frameNum
                        pointNum,  # pointNum
                        elem['pointCloud'][pointNum][0], # Xpos
                        elem['pointCloud'][pointNum][1], # Ypos
                        elem['pointCloud'][pointNum][2], # Zpos
                        elem['pointCloud'][pointNum][3], # Doppler
                        elem['pointCloud'][pointNum][4]  # SNR
                    ]
                    # point coordinate conversion : cartesian to spherical
                    # to support old AI model
                    if DEBUG_AI_INPUT_CONVERSION:
                        point[2:5] = cartesian_to_spherical(point[2], point[3], point[4])
                    queue_list.append(point)

            self.data = pd.DataFrame(queue_list, columns=['frameNum','pointNum','xPos','yPos','zPos','Doppler','SNR'])
                    
            # if self.isSlotRunning:
            #     print("locked")
            # 동시 추론 방지 위한 lock (성능에 따른 선택 필요)
            if self.isSlotRunning == False:
                self.isSlotRunning = True
                self.inferThread = InferThread(self.data, self.model)
                self.inferThread.infer_signal.connect(self.peopleTrack.stateTransition)
                self.inferThread.slot_signal.connect(self.release_slot)
                self.inferThread.no_noise_signal.connect(self.no_noise)
                self.inferThread.noise_update_signal.connect(self.noise_update)
                self.inferThread.start()

            # return cluster info
            max_val = self.data['frameNum'].max()
            frame_df = self.data.loc[self.data['frameNum'] == max_val]
            frame_df = frame_df.drop(columns=['frameNum', 'pointNum', 'zPos', 'Doppler', 'SNR'])
            return self.cluster_single_frame(frame_df)

        except KeyError:
            return NO_CLUSTER
        
    def release_slot(self):
        self.isSlotRunning = False

    def no_noise(self):
        self.noise_cnt = 0
    
    def noise_update(self, ret):
        idx_list = ret[0]
        new_list = []
        for idx, elem in enumerate(self.seq_list):
            if idx in idx_list:
                self.noise_cnt += 1
                if self.noise_cnt > MAX_SEQ_NOISE_LEN:
                    # noise make big gap between sequence data
                    self.seq_list.clear()  # make deque clean
                    self.noise_cnt = 0
                    return
            else:
                new_list.append(elem)
        self.seq_list = new_list


class InferThread(QThread):
    infer_signal = Signal(list)
    slot_signal = Signal()
    no_noise_signal = Signal()
    noise_update_signal = Signal(list)

    def __init__(self, point_data, model, target_eps=1.2, scale_factor=0.6, one_person_threshold=0.8, min_frame_ratio=0.1):
            QThread.__init__(self)
            # self.faldt = faldt
            self.data = point_data

            self.seq_size = SEQ_SIZE
            self.model = model
            self.target_eps = target_eps
            self.scale_factor = scale_factor
            self.one_person_threshold = one_person_threshold
            self.min_frame_ratio = min_frame_ratio

    #프레임별 데이터 클러스터링
    def cluster_data(self):
        data = self.data
        unique_frame_numbers = {frame: idx + 1 for idx, frame in enumerate(data['frameNum'].unique())}
        data['frameNum'] = data['frameNum'].map(unique_frame_numbers)

        clustered_data = pd.DataFrame(columns=data.columns)

        for frame, group in data.groupby('frameNum'):
            group_data = group[['xPos',
                                'yPos',
                                # 'zPos'
                                ]]

            dbscan = DBSCAN(eps=CLUST_EPS, min_samples=CLUST_MIN_SAMPLES)
            clusters = dbscan.fit_predict(group_data)
            group['cluster'] = clusters
            clustered_data = pd.concat([clustered_data.dropna(axis=1, how='all'), group.dropna(axis=1, how='all')])

        clustered_data = clustered_data[clustered_data['cluster'] != -1].reset_index().drop(columns='index')
        return list(set([i for i in range(1, self.seq_size + 1)]) - set(clustered_data['frameNum'].unique())), clustered_data

    
    def kth_smallest_value(self, matrix, k):
        flattened = np.ravel(matrix)
        sorted_values = np.sort(flattened)
        return sorted_values[k]

    #클러스터링 된 데이터 간 궤적 추적
    def track_clusters(self, clustered_data):
        clustered_data_agg = clustered_data.groupby(['frameNum', 'cluster']).agg({'frameNum': 'first','cluster': 'first','xPos': 'mean','yPos': 'mean','zPos': 'mean','Doppler' : 'mean','SNR' : 'mean',}).reset_index(drop=True)
        first_frame_num = clustered_data_agg['frameNum'].min()
        global_clustered_data = clustered_data_agg[clustered_data_agg['frameNum'] == first_frame_num].copy()
        global_clustered_data.loc[:,'global_cluster'] = global_clustered_data['cluster'].copy()

        frame_len = len(clustered_data_agg['frameNum'].unique())
        generated_cluster_n = int(global_clustered_data['global_cluster'].max()) + 1

        for i in range(first_frame_num, first_frame_num + frame_len - 1):
            current_f = global_clustered_data[global_clustered_data['frameNum'] == i].reset_index().drop(columns='index')
            next_f = clustered_data_agg[clustered_data_agg['frameNum'] == i + 1].reset_index().drop(columns='index')
            used_current_f = [0 for i in range(len(current_f))]
            distance_matrix = distance.cdist(current_f[['xPos', 'yPos', 'zPos']], next_f[['xPos', 'yPos', 'zPos']], metric='euclidean')
            for j in range(distance_matrix.size):
                min_value = self.kth_smallest_value(distance_matrix, j)
                # [row], [col] = np.where(distance_matrix == min_value)
                row, col = np.where(distance_matrix == min_value)
                row = row[0]
                col = col[0]
                if used_current_f[row] == 1:
                    continue
                used_current_f[row] = 1
                if min_value >= 3.5:
                    next_f.loc[col, 'global_cluster'] = None
                else:
                    next_f.loc[col, 'global_cluster'] = current_f.loc[row, 'global_cluster']
            g_arr = [i for i in range (generated_cluster_n, generated_cluster_n + next_f['global_cluster'].isna().sum())]
            generated_cluster_n = generated_cluster_n + next_f['global_cluster'].isna().sum()
            next_f.loc[next_f['global_cluster'].isna(), 'global_cluster'] = g_arr[:]
            global_clustered_data = pd.concat([global_clustered_data, next_f]).reset_index().drop(columns='index')
        return global_clustered_data

    #데이터 전처리(슬라이딩 윈도우)
    def prepare_data(self, data, window_size=MODEL_SEQ_SIZE):
        sequences = []
        for i in range(len(data) - window_size + 1):
            window = data.iloc[i:i+window_size][['xPos', 'yPos', 'zPos', 'Doppler', 'SNR']].values
            sequences.append(window)
        return np.array(sequences)

    #모델 실행
    def run_model(self, idx, cluster_dataframes):
        sequences = self.prepare_data(cluster_dataframes)
        print(f"Processing Cluster {idx}, Data Shape: {sequences.shape}")
        predictions = self.model.predict(sequences)
        answer = (np.argmax(predictions, axis=1))[0]
        if answer == 0:
            print("fall")
        elif answer == 1:
            print("sit")
        elif answer == 2:
            print("lie down")
        elif answer == 3:
            print("walk")

        return answer

    def run(self):
        ret = self.cluster_data()
        # if cluster cannot found cluster in any frame
        if len(ret[0]) > 0:
            self.noise_update_signal.emit(ret)
            self.slot_signal.emit()
            return
        else:
            self.no_noise_signal.emit()

        self.infer_list = []
        # Global Clustering
        global_clustered = self.track_clusters(ret[1])
        for cluster_id, cluster_df in global_clustered.groupby("global_cluster"):
            if len(cluster_df) > MODEL_SEQ_SIZE:
                self.infer_list.append((cluster_id, cluster_df))

        output = []
        
        for idx, data in self.infer_list:
            x = data['xPos'].mean()
            y = data['yPos'].mean()
            # z = data['zPos'].mean()

            result = [(x, y), -1] # coord, clust_num, state
            result[1] = self.run_model(idx, data)
            output.append(result)

        # 시그널 연결
        self.infer_signal.emit(output)
        print("=Frame Processed=\n")
        self.slot_signal.emit()

    def stop(self):
        self.slot_signal.emit()
        self.terminate()

# helper method
def cartesian_to_spherical(x, y, z):
    r = np.sqrt(x**2 + y**2 + z**2)
    theta = np.arctan2(y, x)
    phi = np.arccos(z / r)
    return r, theta, phi