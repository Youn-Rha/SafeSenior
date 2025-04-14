import json
import pandas as pd
from scipy.spatial import distance
import numpy as np

BASE_DIR = r'src/enhancedVisualizer/test/data/'
FILE_NAME = 'clust1.json'
PATH = BASE_DIR + FILE_NAME


def kth_smallest_value(matrix, k):
    flattened = np.ravel(matrix)
    sorted_values = np.sort(flattened)
    return sorted_values[k]


def track_clusters(clustered_data):
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
            min_value = kth_smallest_value(distance_matrix, j)
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

def prepare_data(data, window_size=5):
        sequences = []
        for i in range(len(data) - window_size + 1):
            window = data.iloc[i:i+window_size][['Range', 'Azimuth', 'Elevation', 'Doppler', 'SNR']].values
            sequences.append(window)
        return np.array(sequences)

if __name__ == "__main__":
    with open(PATH) as f:
        load_dict = json.load(f)

    df = pd.DataFrame(load_dict)

    # grouped_df = df.groupby('cluster')

    # for clust_idx in set(df['cluster'].values.tolist()):
    #     clust = grouped_df.get_group(clust_idx)
    #     print(clust)

    global_clustered = track_clusters(df)
    # grouped_global_cluster = global_clustered.groupby('global_cluster')
    # for clust_idx in set(global_clustered['global_cluster'].values.tolist()):
    #     clust = grouped_global_cluster.get_group(clust_idx)
    #     print(clust)


    for cluster_id, cluster_df in global_clustered.groupby("global_cluster"):
        print(cluster_df)
        sequences = prepare_data(cluster_df)
        print(sequences.shape[0], end="\n")