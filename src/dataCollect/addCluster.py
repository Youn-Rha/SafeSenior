import pandas as pd
from sklearn.cluster import DBSCAN
from scipy.spatial import distance
from scipy.optimize import linear_sum_assignment
import numpy as np
from filterpy.kalman import KalmanFilter

SEQ_SIZE = 5
EPS = 0.6
MIN_SAMPLE = 20

class ClusterKalman:
    def __init__(self, initial_pos):
        self.kf = KalmanFilter(dim_x=6, dim_z=3)
        dt = 1.0
        self.kf.F = np.array([[1,0,0,dt,0,0],
                              [0,1,0,0,dt,0],
                              [0,0,1,0,0,dt],
                              [0,0,0,1,0,0],
                              [0,0,0,0,1,0],
                              [0,0,0,0,0,1]])
        self.kf.H = np.array([[1,0,0,0,0,0],
                              [0,1,0,0,0,0],
                              [0,0,1,0,0,0]])
        self.kf.R *= 0.1
        self.kf.P *= 1000
        self.kf.Q *= 0.01
        x, y, z = initial_pos
        self.kf.x[:3] = np.array([[x], [y], [z]])

    def predict(self):
        self.kf.predict()
        return self.kf.x[:3].flatten()

    def update(self, measurement):
        self.kf.update(measurement)

class Cluster():        
    def __init__(self):
        self.trackers = {}

    def addCluster(self, data):
        clustered_data = self.cluster_data(data)[1]
        clust_dict = clustered_data.to_dict(orient='records')
        prevNum = clust_dict[0]['frameNum']
        seq = []
        seq_cnt = 0
        glob_clust_mem = 0
        global_clustered = pd.DataFrame()
        for elem in clust_dict:
            curNum = elem['frameNum']
            if prevNum != curNum:
                seq_cnt += 1
                if prevNum + 1 != curNum:
                    df = pd.DataFrame(seq)
                    if seq_cnt > 1:
                        df = self.track_clusters(df, glob_clust_mem)
                        glob_clust_mem = df['global_cluster'].max() + 1
                    global_clustered = pd.concat([global_clustered, df])
                    seq = []
                    seq_cnt = 0
                prevNum = curNum
            seq.append(elem)
        df = pd.DataFrame(seq)
        if seq_cnt > 1:
            df = self.track_clusters(df, glob_clust_mem)
        global_clustered = pd.concat([global_clustered, df])

        global_clustered["global_cluster"] = global_clustered["global_cluster"].fillna(-1)
        return global_clustered

    def cluster_data(self, data):
        seq_size = SEQ_SIZE
        unique_frame_numbers = {frame: idx + 1 for idx, frame in enumerate(data['frameNum'].unique())}
        data['frameNum'] = data['frameNum'].map(unique_frame_numbers)

        clustered_data = pd.DataFrame(columns=data.columns)
        for frame, group in data.groupby('frameNum'):
            group_data = group[['xPos', 'yPos', 'zPos']]
            dbscan = DBSCAN(eps=EPS, min_samples=MIN_SAMPLE)
            clusters = dbscan.fit_predict(group_data)
            group['cluster'] = clusters
            clustered_data = pd.concat([clustered_data, group])

        clustered_data = clustered_data[clustered_data['cluster'] != -1].reset_index().drop(columns='index')
        return list(set([i for i in range(1, seq_size + 1)]) - set(clustered_data['frameNum'].unique())), clustered_data

    def track_clusters(self, clustered_data, glob_clust_start):
        clustered_data_agg = clustered_data.groupby(['frameNum', 'cluster']).agg(
            {'frameNum': 'first','cluster': 'first','xPos': 'mean','yPos': 'mean','zPos': 'mean'}
        ).reset_index(drop=True)

        first_frame_num = clustered_data_agg['frameNum'].min()
        global_clustered_data = clustered_data_agg[clustered_data_agg['frameNum'] == first_frame_num].copy()
        global_clustered_data.loc[:, 'global_cluster'] = global_clustered_data['cluster'].copy()

        for idx, row in global_clustered_data.iterrows():
            g_id = row['global_cluster'] + glob_clust_start
            self.trackers[g_id] = ClusterKalman(row[['xPos','yPos','zPos']].values)

        frame_len = len(clustered_data_agg['frameNum'].unique())
        generated_cluster_n = int(global_clustered_data['global_cluster'].max()) + 1

        for i in range(first_frame_num, first_frame_num + frame_len - 1):
            current_f = global_clustered_data[global_clustered_data['frameNum'] == i].reset_index(drop=True)
            next_f = clustered_data_agg[clustered_data_agg['frameNum'] == i + 1].reset_index(drop=True)
            cost_matrix = np.zeros((len(current_f), len(next_f)))

            for i1, row1 in current_f.iterrows():
                g_id = row1['global_cluster'] + glob_clust_start
                pred = self.trackers[g_id].predict()
                for i2, row2 in next_f.iterrows():
                    obs = row2[['xPos', 'yPos', 'zPos']].values
                    cost_matrix[i1, i2] = np.linalg.norm(pred - obs)

            row_idx, col_idx = linear_sum_assignment(cost_matrix)

            assigned_next = set()
            for r, c in zip(row_idx, col_idx):
                if cost_matrix[r, c] < 3.5:
                    next_f.loc[c, 'global_cluster'] = current_f.loc[r, 'global_cluster']
                    obs = next_f.loc[c, ['xPos', 'yPos', 'zPos']].values
                    g_id = current_f.loc[r, 'global_cluster'] + glob_clust_start
                    self.trackers[g_id].update(obs)
                    assigned_next.add(c)

            for i2, row2 in next_f.iterrows():
                if i2 not in assigned_next:
                    next_f.loc[i2, 'global_cluster'] = generated_cluster_n
                    obs = row2[['xPos', 'yPos', 'zPos']].values
                    self.trackers[generated_cluster_n] = ClusterKalman(obs)
                    generated_cluster_n += 1

            global_clustered_data = pd.concat([global_clustered_data, next_f]).reset_index(drop=True)

        global_clustered_data["global_cluster"] = global_clustered_data["global_cluster"].fillna(-1 * glob_clust_start - 1) + glob_clust_start
        global_clustered_data = global_clustered_data.drop(columns=["xPos","yPos","zPos"])
        ret = pd.merge(clustered_data, global_clustered_data[['cluster','frameNum','global_cluster']], on=['cluster','frameNum'], how='left')
        return ret