from collections import deque
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.metrics import pairwise_distances
from scipy.optimize import linear_sum_assignment
import tensorflow as tf
from PySide2.QtCore import QThread
from scipy.spatial import distance

default_ret = [-1, 3, None]
min_body_dots = 10

from macroControl import DEBUG_AI_INPUT_CONVERSION, SEQ_SIZE, MODEL_PATH, MAX_SEQ_NOISE_LEN

# Class meant to store the fall detection results of all the tracks
class FallDetection:
    def __init__(self):
        self.seq_size = SEQ_SIZE
        self.seq_list = []
        self.data = []

        # AI model
        self.model = self._load_model()

        # to prevent inference load
        self.isSlotRunning = False

        # for caching state
        self.old_state = default_ret
        self.output = self.old_state

        # to check noise count
        self.noise_cnt = 0

    #모델 로드
    def _load_model(self):
        model = tf.keras.models.load_model(MODEL_PATH)
        print("Model loaded successfully.")
        return model

    #프레임별 데이터 클러스터링
    def cluster_data(self):
        data = self.data
        unique_frame_numbers = {frame: idx + 1 for idx, frame in enumerate(data['frameNum'].unique())}
        data['frameNum'] = data['frameNum'].map(unique_frame_numbers)

        clustered_data = pd.DataFrame(columns=data.columns)

        for frame, group in data.groupby('frameNum'):
            group_data = group[['Range', 'Azimuth', 'Elevation']]
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(group_data)

            dbscan = DBSCAN(eps=1, min_samples=3)
            clusters = dbscan.fit_predict(scaled_data)
            group['cluster'] = clusters
            group = group.sort_values(by='cluster')
            # group = group.dropna(how="all", axis=1)
            # clustered_data = pd.concat([clustered_data,group])
            clustered_data = pd.concat([clustered_data.dropna(axis=1, how='all'), group.dropna(axis=1, how='all')])

        clustered_data = clustered_data[clustered_data['cluster'] != -1].reset_index().drop(columns='index')
        # if DEBUG_AI_INPUT_CONVERSION:
        #     clustered_data['x'] = clustered_data['Range'] * np.cos(clustered_data['Elevation']) * np.cos(
        #         clustered_data['Azimuth'])
        #     clustered_data['y'] = clustered_data['Range'] * np.cos(clustered_data['Elevation']) * np.sin(
        #         clustered_data['Azimuth'])
        #     clustered_data['z'] = clustered_data['Range'] * np.sin(clustered_data['Elevation'])
        return list(set([1,2,3,4,5]) - set(clustered_data['frameNum'].unique())), clustered_data  

    # Update the fall detection results for every track in the frame
    def step(self, outputDict):
        if len(self.seq_list) < self.seq_size:
            # append only
            self.seq_list.append(outputDict)
            return
        else:
            self.seq_list.append(outputDict)
            self.seq_list.pop(0)

        queue_list = []
        
        try:
            for idx, elem in enumerate(self.seq_list):
                num = elem['numDetectedPoints'] # pointNum
                if num <= 0:
                    return
                # TODO 리턴할때 스테이터스를 처리하는 방안 고안 필요
                for pointNum in range(num):
                    point = [
                        idx + 1,    # frameNum
                        pointNum,  # pointNum
                        outputDict['pointCloud'][pointNum][0], # Xpos
                        outputDict['pointCloud'][pointNum][1], # Ypos
                        outputDict['pointCloud'][pointNum][2], # Zpos
                        outputDict['pointCloud'][pointNum][3], # Doppler
                        outputDict['pointCloud'][pointNum][4]  # SNR
                    ]
                    # point coordinate conversion : cartesian to spherical
                    # to support old AI model
                    if DEBUG_AI_INPUT_CONVERSION:
                        point[2:5] = cartesian_to_spherical(point[2], point[3], point[4])
                    queue_list.append(point)

            self.data = pd.DataFrame(queue_list, columns=['frameNum','pointNum','Range','Azimuth','Elevation','Doppler','SNR'])

            ret = self.cluster_data()
            # if cluster cannot found cluster in any frame
            if len(ret[0]) > 0:
                for idx in ret[0]:
                    # droup frame with no cluster
                    self.seq_list.pop(idx)
                    self.noise_cnt += 1
                    if self.noise_cnt > MAX_SEQ_NOISE_LEN:
                        # noise make big gap between sequence data
                        self.seq_list.clear()  # make deque clean
                        self.noise_cnt = 0
                        return
                return

            if self.isSlotRunning == True:
                return self.old_state
            else:
                self.isSlotRunning = True
                self.inferThread = InferThread(ret[1], self.model, self.output)
                self.inferThread.start()
                self.old_state = self.output
                self.isSlotRunning = False
                return self.output

        except KeyError:
            pass


class InferThread(QThread):

    def __init__(self, point_data, model, output, target_eps=1.2, scale_factor=0.6, one_person_threshold=0.8, min_frame_ratio=0.1):
            QThread.__init__(self)
            # self.faldt = faldt
            self.data = point_data
            self.output = output

            # self.seqSize = SEQ_SIZE
            self.model = model
            self.target_eps = target_eps
            self.scale_factor = scale_factor
            self.one_person_threshold = one_person_threshold
            self.min_frame_ratio = min_frame_ratio

    def kth_smallest_value(self, matrix, k):
        flattened = np.ravel(matrix)
        sorted_values = np.sort(flattened)
        return sorted_values[k]

    #클러스터링 된 데이터 간 궤적 추적
    def track_clusters(self, clustered_data):
        # print(clustered_data, end='\n\n')
        clustered_data_agg = clustered_data.groupby(['frameNum', 'cluster']).agg({'frameNum': 'first',
                                                                                  'cluster': 'first',
                                                                                  'Range': 'mean',
                                                                                  'Azimuth': 'mean',
                                                                                  'Elevation': 'mean',
                                                                                  'Doppler' : 'mean',
                                                                                  'SNR' : 'mean',
                                                                                  }).reset_index(drop=True)
        global_clustered_data = clustered_data_agg[clustered_data_agg['frameNum'] == 1].copy()
        global_clustered_data.loc[:,'global_cluster'] = global_clustered_data['cluster'].copy()
        frame_len = len(clustered_data_agg['frameNum'].unique())
        generated_cluster_n = int(global_clustered_data['global_cluster'].max()) + 1

        for i in range(1, frame_len):
            current_f = global_clustered_data[global_clustered_data['frameNum'] == i].reset_index().drop(
                columns='index')
            next_f = clustered_data_agg[clustered_data_agg['frameNum'] == i + 1].reset_index().drop(columns='index')
            used_current_f = [0 for i in range(len(current_f))]
            distance_matrix = distance.cdist(current_f[['Range', 'Azimuth', 'Elevation']], next_f[['Range', 'Azimuth', 'Elevation']], metric='euclidean')
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
            max_global_cluster = global_clustered_data['global_cluster'].max() if not global_clustered_data.empty else 0
            # g_arr = [i for i in range(max_global_cluster + 1, max_global_cluster + 1 + next_f.loc['global_cluster'].isna().sum())]
            cnt = 0
            for i in next_f['global_cluster']:
                if pd.isna(i):
                    cnt += 1
            # if cnt > 0:
            #     cnt -= 1
            g_arr = [i for i in range(generated_cluster_n, generated_cluster_n + cnt)]
            generated_cluster_n = generated_cluster_n + cnt
            next_f.loc[next_f['global_cluster'].isna(), 'global_cluster'] = g_arr[:]
            global_clustered_data = pd.concat([global_clustered_data, next_f]).reset_index().drop(columns='index')
            # global_clustered_data = pd.concat([global_clustered_data, next_f]).reset_index(drop=True)
        return global_clustered_data

    #데이터 전처리(슬라이딩 윈도우)
    def prepare_data(self, data, window_size=5):
        sequences = []
        for i in range(len(data) - window_size + 1):
            window = data.iloc[i:i+window_size][['Range', 'Azimuth', 'Elevation', 'Doppler', 'SNR']].values
            sequences.append(window)
        return np.array(sequences)

    #모델 실행
    def run_model(self, cluster_dataframes):
        outputList = default_ret
        cnt = 0
        for cluster_id, cluster_df in cluster_dataframes.groupby("global_cluster"):
            sequences = self.prepare_data(cluster_df)
            if sequences.size == 0:
                print(f"Cluster {cluster_id}: No valid sequences. Skipping.")
                continue
            
            # skip small movement
            if sequences.shape[0] < min_body_dots:
                continue

            print(f"Processing Cluster {cluster_id}, Data Shape: {sequences.shape}")

            # aggregation frome here
            avg_seq = np.mean(sequences, axis=0)
            avg_matched = np.expand_dims(avg_seq, axis=0)

            predictions = self.model.predict(avg_matched)
            # print(predictions.shape)
            # print((np.argmax(predictions, axis=1)))
            print(f"Predictions for Cluster {cluster_id}, {cnt}: {(np.argmax(predictions, axis=1))[0]}")
            answer = (np.argmax(predictions, axis=1))[0]
            outputList[0] = cnt
            outputList[1] = answer
            outputList[2] = avg_matched
            cnt += 1
            # outputList[cluster_id] = answer

        print("=Frame Processed=\n")

        return outputList

    def run(self):
        if self.data.empty:
            return
        
        global_clustered_data = self.track_clusters(self.data)
        self.output = self.run_model(global_clustered_data)

    def stop(self):
        self.terminate()

# helper method
def cartesian_to_spherical(x, y, z):
    r = np.sqrt(x**2 + y**2 + z**2)
    theta = np.arctan2(y, x)
    phi = np.arccos(z / r)
    return r, theta, phi

# step에서 outputDict를 point로 변환할때 호출 필요