from collections import deque
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.metrics import pairwise_distances
from scipy.optimize import linear_sum_assignment
import tensorflow as tf
from PySide2 import QtCore, QtWidgets

model_path = r"src\AI\final_model.h5"

# Class meant to store the fall detection results of all the tracks
class FallDetection:
    def __init__(self, model_path, seqSize = 5, target_eps=1.2, scale_factor=0.6, one_person_threshold=0.8, min_frame_ratio=0.1):
        self.seqSize = seqSize
        self.dictQ = deque(maxlen=(self.seqSize + 1))

        self.model_path = model_path
        self.target_eps = target_eps
        self.scale_factor = scale_factor
        self.one_person_threshold = one_person_threshold
        self.min_frame_ratio = min_frame_ratio
        self.model = self._load_model()

    #모델 로드
    def _load_model(self):
        model = tf.keras.models.load_model(self.model_path)
        print("Model loaded successfully.")
        return model

    #동적 eps 준비
    @staticmethod
    def calculate_dynamic_eps(data, target_eps=1.2, scale_factor=0.6):
        if len(data) < 2:
            return target_eps
        distances = pairwise_distances(data)
        if distances.size == 0:
            return target_eps
        distances = distances[np.triu_indices_from(distances, k=1)]
        if len(distances) == 0:
            return target_eps
        percentile_distance = np.percentile(distances, 90)
        scaled_eps = percentile_distance * scale_factor
        return max(0.1, min(target_eps, scaled_eps))

    #프레임별 데이터 클러스터링
    def cluster_data(self):
        data = self.data
        unique_frame_numbers = {frame: idx + 1 for idx, frame in enumerate(data['frameNum'].unique())}
        data['frameNum'] = data['frameNum'].map(unique_frame_numbers)

        clustered_frames = []
        one_person_frames = 0
        total_frames = len(data['frameNum'].unique())

        for frame, group in data.groupby('frameNum'):
            frame_data = group[['Range', 'Azimuth', 'Elevation']]
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(frame_data)

            if len(scaled_data) < 1:
                group['cluster'] = -1
                clustered_frames.append(group)
                continue

            dynamic_eps = self.calculate_dynamic_eps(scaled_data, self.target_eps, self.scale_factor)
            final_eps = min(dynamic_eps, self.target_eps)
            dbscan = DBSCAN(eps=final_eps, min_samples=1) #min_samples 수정 O

            clusters = dbscan.fit_predict(scaled_data)
            group['cluster'] = clusters

            cluster_counts = group['cluster'].value_counts(normalize=True)
            if cluster_counts.iloc[0] >= 0.9:
                one_person_frames += 1
            else:
                clustered_frames.append(group)

        one_person_ratio = one_person_frames / total_frames
        if one_person_ratio >= self.one_person_threshold:
            print("전체 데이터의 80% 이상이 1인 데이터입니다. 클러스터링을 건너뜁니다.")
            return None
        else:
            if clustered_frames:
                final_clustered_data = pd.concat(clustered_frames).reset_index(drop=True)
                return final_clustered_data
            else:
                print("유효한 클러스터링 결과가 없습니다.")
                return None

    #클러스터링 된 데이터 간 궤적 추적
    def track_clusters(self, data):
        total_frames = data['frameNum'].nunique()
        global_cluster_ids = list(range(data[data['cluster'] != -1]['cluster'].nunique()))
        clustered_frames = []
        for frame, group in data.groupby('frameNum'):
            clustered_frames.append(group)

        cluster_mapping = {}
        previous_centroids = None

        for frame_idx, frame_data in enumerate(clustered_frames):
            centroids = (
                frame_data[frame_data['cluster'] != -1]
                .groupby('cluster')[['Range', 'Azimuth', 'Elevation']]
                .mean()
            ).reset_index()

            if previous_centroids is not None and not centroids.empty:
                distance_matrix = pairwise_distances(
                    previous_centroids[['Range', 'Azimuth', 'Elevation']],
                    centroids[['Range', 'Azimuth', 'Elevation']]
                )
                row_ind, col_ind = linear_sum_assignment(distance_matrix)

                matched_current_clusters = set()
                for prev_idx, curr_idx in zip(row_ind, col_ind):
                    if (
                        distance_matrix[prev_idx, curr_idx] < 1.5 and
                        curr_idx not in matched_current_clusters
                    ):
                        cluster_mapping[(frame_idx, centroids.iloc[curr_idx]['cluster'])] = cluster_mapping.get(
                            (frame_idx - 1, previous_centroids.iloc[prev_idx]['cluster']),
                            global_cluster_ids[prev_idx % len(global_cluster_ids)]
                        )
                        matched_current_clusters.add(curr_idx)

            else:
                for idx, cluster_id in enumerate(centroids['cluster'].unique()):
                    cluster_mapping[(frame_idx, cluster_id)] = global_cluster_ids[idx % len(global_cluster_ids)]

            previous_centroids = centroids

        for frame_idx, frame_data in enumerate(clustered_frames):
            frame_data['global_cluster'] = frame_data['cluster'].map(
                lambda x: cluster_mapping.get((frame_idx, x), -1) if x != -1 else -1
            )

        final_data_sorted = pd.concat(clustered_frames).sort_values(by=['frameNum', 'global_cluster']).reset_index(drop=True)

        cluster_dataframes = {}
        for cluster_id, group in final_data_sorted.groupby('global_cluster'):
            if cluster_id == -1:
                continue
            num_frames = group['frameNum'].nunique()
            if num_frames / total_frames <= self.min_frame_ratio:
                print(f"Global Cluster {cluster_id}: 프레임 수가 전체의 10% 이하로 건너뜁니다.")
                continue
            cluster_dataframes[cluster_id] = group

        return cluster_dataframes

    #데이터 전처리(슬라이딩 윈도우)
    def prepare_data(self, data, window_size=5):
        sequences = []
        for i in range(len(data) - window_size + 1):
            window = data.iloc[i:i+window_size][['Range', 'Azimuth', 'Elevation', 'Doppler', 'SNR']].values
            sequences.append(window)
        return np.array(sequences)

    #모델 실행
    def run_model(self, cluster_dataframes):
        for cluster_id, cluster_df in cluster_dataframes.items():
            sequences = self.prepare_data(cluster_df)
            if sequences.size == 0:
                print(f"Cluster {cluster_id}: No valid sequences. Skipping.")
                continue

            print(f"Processing Cluster {cluster_id}, Data Shape: {sequences.shape}")

            # aggregation frome here
            avg_seq = np.mean(sequences, axis=0)
            avg_matched = np.expand_dims(avg_seq, axis=0)

            predictions = self.model.predict(sequences)
            print(f"Predictions for Cluster {cluster_id}: {(np.argmax(predictions, axis=1))[0]}")

    def run_pipeline(self):
        clustered_data = self.cluster_data()
        if clustered_data is not None:
            cluster_dataframes = self.track_clusters(clustered_data)
            if cluster_dataframes:
                self.run_model(cluster_dataframes)
            else:
                print("No valid clusters for prediction.")
        else:
            print("Using naive data for prediction.")
            data = self.data
            self.run_model({0: data})

    # Update the fall detection results for every track in the frame
    def step(self, outputDict):
        if len(self.dictQ) < self.seqSize:
            # append only
            self.dictQ.append(outputDict)
        else:
            self.dictQ.append(outputDict)
            self.dictQ.popleft()

        queue_list = []
        for idx, elem in enumerate(self.dictQ):
            num = elem["numDetectedPoints"] # pointNum
            for point in range(num):
                point = [
                    idx + 1,    # frameNum
                    point,  # pointNum
                    outputDict["pointCloud"][point][0], # Range
                    outputDict["pointCloud"][point][1], # Azimuth
                    outputDict["pointCloud"][point][2], # Elevation
                    outputDict["pointCloud"][point][3], # Doppler
                    outputDict["pointCloud"][point][4]  # SNR
                ]
                queue_list.append(point)

        self.data = pd.DataFrame(queue_list, columns=['frameNum','pointNum','Range','Azimuth','Elevation','Doppler','SNR'])

        self.run_pipeline()
