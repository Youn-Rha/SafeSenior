import pandas as pd
from sklearn.cluster import DBSCAN
from scipy.spatial import distance
import numpy as np
import os

FILE_PATH = r"src\dataCollect\data\cloud_2025_01_09_14_45_4.csv"
SAVE_DIR = r"src\csvAddCluster"
SEQ_SIZE = 5
EPS = 0.6
MIN_SAMPLE = 20

def cluster_data(data):
    seq_size = SEQ_SIZE
    unique_frame_numbers = {frame: idx + 1 for idx, frame in enumerate(data['frameNum'].unique())}
    data['frameNum'] = data['frameNum'].map(unique_frame_numbers)

    clustered_data = pd.DataFrame(columns=data.columns)

    for frame, group in data.groupby('frameNum'):
        group_data = group[['xPos', 'yPos', 'zPos']]

        dbscan = DBSCAN(eps=EPS, min_samples=MIN_SAMPLE)
        clusters = dbscan.fit_predict(group_data)
        group['cluster'] = clusters
        clustered_data = pd.concat([clustered_data.dropna(axis=1, how='all'), group.dropna(axis=1, how='all')])

    clustered_data = clustered_data[clustered_data['cluster'] != -1].reset_index().drop(columns='index')
    return list(set([i for i in range(1, seq_size + 1)]) - set(clustered_data['frameNum'].unique())), clustered_data

def kth_smallest_value(matrix, k):
        flattened = np.ravel(matrix)
        sorted_values = np.sort(flattened)
        return sorted_values[k]

def track_clusters(clustered_data, glob_clust_start):
        clustered_data_agg = clustered_data.groupby(['frameNum', 'cluster']).agg({'frameNum': 'first','cluster': 'first','xPos': 'mean','yPos': 'mean','zPos': 'mean'}).reset_index(drop=True)
        first_frame_num = clustered_data_agg['frameNum'].min()
        global_clustered_data = clustered_data_agg[clustered_data_agg['frameNum'] == first_frame_num].copy()  # 제일 처음 프레임을 찾겠다
        global_clustered_data.loc[:,'global_cluster'] = global_clustered_data['cluster'].copy()

        frame_len = len(clustered_data_agg['frameNum'].unique())
        generated_cluster_n = int(global_clustered_data['global_cluster'].max()) + 1

        for i in range(first_frame_num, first_frame_num + frame_len - 1):
            current_f = global_clustered_data[global_clustered_data['frameNum'] == i].reset_index().drop(
                columns='index')
            next_f = clustered_data_agg[clustered_data_agg['frameNum'] == i + 1].reset_index().drop(columns='index')
            used_current_f = [0 for i in range(len(current_f))]
            distance_matrix = distance.cdist(current_f[['xPos', 'yPos', 'zPos']], next_f[['xPos', 'yPos', 'zPos']], metric='euclidean')
            for j in range(distance_matrix.size):
                min_value = kth_smallest_value(distance_matrix, j)
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
        # global cluster의 시작 번호를 적용
        global_clustered_data["global_cluster"] = global_clustered_data["global_cluster"].fillna(-1 * glob_clust_start - 1) + glob_clust_start

        # 원래 데이터와 합산
        global_clustered_data = global_clustered_data.drop(columns=["xPos","yPos","zPos"])
        # ret = pd.merge(clustered_data, global_clustered_data, on=["frameNum","cluster"], how="left")
        ret = pd.merge(clustered_data, global_clustered_data[['cluster','frameNum','global_cluster']], on=['cluster','frameNum'], how='left')
        return ret

if __name__ == "__main__":
    data = pd.read_csv(FILE_PATH)

    clustered_data = cluster_data(data)[1]
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
            if prevNum + 1 != curNum:   # 연속성 끊기면 시퀸스를 처리
                # glob clust
                df = pd.DataFrame(seq)
                if seq_cnt > 1:
                    df = track_clusters(df, glob_clust_mem) # 연속 시퀸스 존재 시 글로벌 클러스터
                    glob_clust_mem = df['global_cluster'].max() + 1
                global_clustered = pd.concat([global_clustered, df])
                seq = []
                seq_cnt = 0
            prevNum = curNum
        seq.append(elem)
    # add remainings
    df = pd.DataFrame(seq)
    if seq_cnt > 1:
        df = track_clusters(df, glob_clust_mem) # 연속 시퀸스 존재 시 글로벌 클러스터
    global_clustered = pd.concat([global_clustered, df])

    global_clustered["global_cluster"] = global_clustered["global_cluster"].fillna(-1)

    dir = os.path.join(SAVE_DIR, "test.csv")
    global_clustered.to_csv(dir)
    print(global_clustered)