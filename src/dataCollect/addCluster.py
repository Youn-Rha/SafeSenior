# cluster_tracking_adapter.py (Tracking 통합 + Hungarian 매칭 + Mahalanobis + Gating)

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from filterpy.kalman import KalmanFilter
from collections import deque
from scipy.optimize import linear_sum_assignment

SEQ_SIZE = 5
EPS = 0.7  # 완화: DBSCAN 클러스터 분할 방지, 한 사람의 팔-몸 분리 줄임
MIN_SAMPLE = 20
KF_DIM_X = 6
KF_DIM_Z = 3
GATING_THRESHOLD = 15.0  # 완화: 3명 이상일 때 트랙-클러스터 연결률 향상  # chi-squared 3D gating threshold (~3σ)

class BatchedData:
    def __init__(self, init_data=np.empty((0, 8)), size=5):
        self.size = size
        self.buffer = deque(maxlen=size)
        if init_data.shape[0] > 0:
            self.buffer.append(init_data)
        self.effective_data = np.concatenate(list(self.buffer), axis=0) if self.buffer else np.empty((0, 8))

    def add_frame(self, new_data: np.ndarray):
        self.buffer.append(new_data)
        self.effective_data = np.concatenate(list(self.buffer), axis=0)

class KalmanState(KalmanFilter):
    def __init__(self, centroid):
        super().__init__(dim_x=KF_DIM_X, dim_z=KF_DIM_Z)
        dt = 1.0
        self.F = np.array([[1,0,0,dt,0,0],
                           [0,1,0,0,dt,0],
                           [0,0,1,0,0,dt],
                           [0,0,0,1,0,0],
                           [0,0,0,0,1,0],
                           [0,0,0,0,0,1]])
        self.H = np.array([[1,0,0,0,0,0],
                           [0,1,0,0,0,0],
                           [0,0,1,0,0,0]])
        self.R *= 0.1
        self.P *= 500.
        self.Q *= 0.01
        self.x[:3] = np.array(centroid[:3]).reshape(3, 1)

class PointCluster:
    def __init__(self, pointcloud: np.ndarray):
        self.pointcloud = pointcloud
        self.point_num = pointcloud.shape[0]
        self.centroid = np.mean(pointcloud[:, :3], axis=0)
        self.velocity = np.mean(pointcloud[:, 3:6], axis=0)
        self.cov = np.cov(pointcloud[:, :3].T) if pointcloud.shape[0] > 1 else np.eye(3) * 0.1
        self.doppler = np.mean(np.linalg.norm(pointcloud[:, 3:6], axis=1))
        self.snr = np.mean(pointcloud[:, 7])

class ClusterTrack:
    def __init__(self, cluster: PointCluster, track_id: int):
        self.cluster = cluster
        self.kf = KalmanState(cluster.centroid)
        self.id = track_id
        self.lifetime = 0
        self.batch = BatchedData(cluster.pointcloud)

    def predict(self):
        self.kf.predict()

    def update(self, cluster: PointCluster):
        self.cluster = cluster
        self.kf.update(cluster.centroid)
        self.batch.add_frame(cluster.pointcloud)
        self.lifetime = 0

    def get_predicted_state(self):
        return self.kf.x[:3].flatten(), self.kf.x[3:6].flatten()

class TrackBuffer:
    def __init__(self):
        self.effective_tracks = []
        self.next_track_id = 0

    def mahalanobis_distance(self, x, mean, cov):
        delta = x - mean
        try:
            inv_cov = np.linalg.inv(cov + np.eye(3) * 1e-3)
        except np.linalg.LinAlgError:
            inv_cov = np.eye(3)
        return float(delta.T @ inv_cov @ delta)

    def compute_cost_matrix(self, tracks, clusters):
        cost_matrix = np.full((len(tracks), len(clusters)), np.inf)
        for i, track in enumerate(tracks):
            pred_pos, _ = track.get_predicted_state()
            P = track.kf.P[:3, :3]
            for j, cluster in enumerate(clusters):
                d2 = self.mahalanobis_distance(cluster.centroid, pred_pos, P + cluster.cov)
                if d2 < GATING_THRESHOLD:
                    cost_matrix[i, j] = d2
        return cost_matrix

    def track(self, pointcloud: np.ndarray, batch: BatchedData):
        clusters = DBSCAN(eps=EPS, min_samples=MIN_SAMPLE).fit_predict(pointcloud[:, :3])
        cluster_ids = np.unique(clusters[clusters != -1])

        new_clusters = [PointCluster(pointcloud[clusters == cid]) for cid in cluster_ids]

        for track in self.effective_tracks:
            track.predict()
            track.lifetime += 1

        unmatched_clusters = set(range(len(new_clusters)))

        if self.effective_tracks and new_clusters:
            cost_matrix = self.compute_cost_matrix(self.effective_tracks, new_clusters)
            if not np.isfinite(cost_matrix).any():
                print(f"[⚠️ Gating 실패] 모든 매칭 실패 → fallback 트랙 생성")
                for j in range(len(new_clusters)):
                    new_track = ClusterTrack(new_clusters[j], self.next_track_id)
                    self.effective_tracks.append(new_track)
                    self.next_track_id += 1
                return clusters  # 조기 종료
            else:
                row_idx, col_idx = linear_sum_assignment(cost_matrix)

            for i, j in zip(row_idx, col_idx):
                if cost_matrix[i, j] < GATING_THRESHOLD:
                    self.effective_tracks[i].update(new_clusters[j])
                    unmatched_clusters.discard(j)

        for j in unmatched_clusters:
            new_track = ClusterTrack(new_clusters[j], self.next_track_id)
            self.effective_tracks.append(new_track)
            self.next_track_id += 1

        self.effective_tracks = [t for t in self.effective_tracks if t.lifetime < 7]  # 유연하게: 순간 튐에도 트랙 유지

        return clusters

class Cluster:
    def __init__(self):
        self.track_buffer = TrackBuffer()
        self.batch = BatchedData()
        self.frame_counter = 0

    def addCluster(self, data):
        results = []

        for f_id in sorted(data['frameNum'].unique()):
            self.frame_counter += 1
            frame_num = f_id

            frame_df = data[data['frameNum'] == f_id]

            try:
                pointcloud = frame_df[['xPos', 'yPos', 'zPos', 'vx', 'vy', 'vz', 'r', 's']].to_numpy()
            except KeyError:
                pointcloud = frame_df[['xPos', 'yPos', 'zPos']].to_numpy()
                pointcloud = np.hstack([pointcloud, np.zeros((pointcloud.shape[0], 3)), np.ones((pointcloud.shape[0], 2))])

            clusters = self.track_buffer.track(pointcloud, self.batch)
            self.batch.add_frame(pointcloud)

            cluster_centroids = {tuple(np.round(t.cluster.centroid, 2)): t.id for t in self.track_buffer.effective_tracks}

            for cid in np.unique(clusters):
                if cid == -1:
                    continue
                cluster_pts = pointcloud[clusters == cid]
                cluster_centroid = np.mean(cluster_pts[:, :3], axis=0)
                min_dist = float('inf')
                global_id = -1
                for prev_c, gid in cluster_centroids.items():
                    dist = np.linalg.norm(cluster_centroid - np.array(prev_c))
                    if dist < min_dist and dist < 1.5:
                        min_dist = dist
                        global_id = gid

                for pt in cluster_pts:
                    results.append({
                        'frameNum': frame_num,
                        'pointNum': 1,
                        'xPos': pt[0],
                        'yPos': pt[1],
                        'zPos': pt[2],
                        'Doppler': np.linalg.norm(pt[3:6]),
                        'SNR': pt[7],
                        'cluster': cid,
                        'global_cluster': global_id
                    })

        return pd.DataFrame(results)