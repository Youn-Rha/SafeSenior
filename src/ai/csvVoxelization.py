import os
import glob
import numpy as np
import pandas as pd

# =========================
# 1. voxelization 함수 (원본과 동일)
# =========================
def voxalize(x_points, y_points, z_points, x, y, z, velocity=None):
    """
    3D 점군 (x, y, z)을 (x_points, y_points, z_points) 해상도의 voxel 격자로 변환하여,
    각 voxel 셀에 속한 점 개수를 세어서 리턴합니다.
    """
    x_min, x_max = np.min(x), np.max(x)
    y_min, y_max = np.min(y), np.max(y)
    z_min, z_max = np.min(z), np.max(z)

    # 셀 크기 계산
    x_res = (x_max - x_min) / x_points
    y_res = (y_max - y_min) / y_points
    z_res = (z_max - z_min) / z_points

    # voxel grid 초기화
    pixel = np.zeros((x_points, y_points, z_points), dtype=np.float32)

    # 각 점을 해당 셀에 배치
    for i in range(x.shape[0]):
        xi, yi, zi = x[i], y[i], z[i]
        # 셀 인덱스 계산
        idx = int(np.floor((xi - x_min) / (x_max - x_min + 1e-8) * x_points))
        idy = int(np.floor((yi - y_min) / (y_max - y_min + 1e-8) * y_points))
        idz = int(np.floor((zi - z_min) / (z_max - z_min + 1e-8) * z_points))
        # 경계(==max)일 때 overflow 방지
        if idx == x_points:
            idx = x_points - 1
        if idy == y_points:
            idy = y_points - 1
        if idz == z_points:
            idz = z_points - 1

        pixel[idx, idy, idz] += 1.0

    return pixel

# =========================
# 2. CSV 파일 하나를 읽어서 voxel 시퀀스 생성하는 함수
# =========================
def get_data_csv(csv_path):
    """
    단일 CSV 파일을 읽어, frameNum 기준으로 그룹핑한 뒤
    각 프레임에 대해 voxalize()를 수행하고, 
    60프레임씩 묶어서 슬라이딩 윈도우 시퀀스를 생성하여 리턴합니다.

    - 반환값: train_data (shape = [N_sequences, 60, 10, 32, 32])
    """
    df = pd.read_csv(csv_path)
    # CSV 컬럼: 최소한 'frameNum', 'xPos', 'yPos', 'zPos', 'Doppler'가 있어야 합니다.

    # 1) 고유한 frameNum을 오름차순으로 추출
    unique_frames = np.sort(df['frameNum'].unique())
    num_frames = unique_frames.shape[0]

    # 2) 프레임별 voxel 배열 저장 리스트
    voxels_per_frame = []
    for f in unique_frames:
        sub = df[df['frameNum'] == f]
        # 이 프레임의 점이 하나도 없으면 빈 voxel 배열(모두 0) 생성
        if sub.shape[0] == 0:
            vox = np.zeros((10, 32, 32), dtype=np.float32)
        else:
            x = sub['xPos'].values.astype(np.float32)
            y = sub['yPos'].values.astype(np.float32)
            z = sub['zPos'].values.astype(np.float32)
            vel = sub['Doppler'].values.astype(np.float32)
            vox = voxalize(10, 32, 32, x, y, z, vel)
        voxels_per_frame.append(vox)

    voxels_per_frame = np.stack(voxels_per_frame, axis=0)
    # voxels_per_frame.shape == (num_frames, 10, 32, 32)

    # 3) 슬라이딩 윈도우: 60프레임씩 묶되, 간격은 10프레임
    frames_together = 60
    sliding = 10
    train_data = []
    i = 0
    while i + frames_together <= num_frames:
        seq = voxels_per_frame[i : i + frames_together]  # (60, 10, 32, 32)
        train_data.append(seq)
        i += sliding

    train_data = np.array(train_data, dtype=np.float32)
    # train_data.shape = (N_sequences, 60, 10, 32, 32)
    return train_data


# =========================
# 3. 폴더 내 모든 CSV → .npy로 저장하고, 최종 모든 .npy를 합쳐서 하나의 .npz 생성
# =========================
def convert_folder_csv_to_combined_npz(parent_dir, output_npz_path, label, file_pattern='*.csv'):
    """
    1) parent_dir 내의 모든 CSV 파일을 찾고,
    2) 각 CSV마다 get_data_csv() 호출 → train_data (NumPy 배열) 생성
    3) train_data를 <원본_파일명>.npy로 parent_dir/npy_temp/ 폴더에 저장
    4) 모든 .npy 파일을 불러와 np.concatenate → 하나의 큰 배열로 합침
    5) 합쳐진 큰 배열을 output_npz_path (.npz)로 저장
    """
    # 1) 임시로 .npy를 저장할 폴더 생성
    npy_temp_dir = os.path.join(parent_dir, 'npy_temp')
    os.makedirs(npy_temp_dir, exist_ok=True)

    # 2) parent_dir 내의 모든 CSV 파일 목록
    csv_files = sorted(glob.glob(os.path.join(parent_dir, file_pattern)))
    if not csv_files:
        print(f"[Warning] '{parent_dir}' 아래에 '{file_pattern}' 파일이 없습니다.")
        return

    npy_paths = []
    label_list = []

    for csv_path in csv_files:
        basename = os.path.basename(csv_path)
        name_wo_ext = os.path.splitext(basename)[0]
        print(f"▶ Processing CSV: {basename}")

        # a) CSV → NumPy 배열 (shape = [N_i, 60, 10, 32, 32])
        train_data = get_data_csv(csv_path)
        if train_data.size == 0:
            print(f"   [Info] '{basename}'에 대해 생성된 시퀀스가 없어 건너뜁니다.")
            continue

        # b) 임시 .npy 파일로 저장
        npy_filename = f"{name_wo_ext}.npy"
        npy_path = os.path.join(npy_temp_dir, npy_filename)
        np.save(npy_path, train_data)
        npy_paths.append(npy_path)
        print(f"   → Saved temporary NPY: {npy_filename} (shape = {train_data.shape})")

        num_seq = train_data.shape[0]
        labels = np.array([label] * num_seq, dtype='<U50')  # 문자열 배열
        label_list.append(labels)

        # 메모리 해제
        del train_data

    # 3) 모든 .npy 파일을 불러와서 하나로 합침
    if len(npy_paths) == 0:
        print("[Error] 유효한 NPY 파일이 하나도 생성되지 않았습니다.")
        return

    print("\n Combining all .npy files into one big array ...")
    combined_list = []
    for npy_path in npy_paths:
        arr = np.load(npy_path)  # arr.shape = (N_i, 60, 10, 32, 32)
        combined_list.append(arr)
        print(f"   · Loaded '{os.path.basename(npy_path)}', shape = {arr.shape}")

    # 4) axis=0 방향으로 결합
    combined_array = np.concatenate(combined_list, axis=0)
    print(f"\n▶ Combined shape: {combined_array.shape}  (총 시퀀스 개수 = {combined_array.shape[0]})")

    # 4) 라벨 리스트 합쳐서 하나의 문자열 배열로
    combined_labels = np.concatenate(label_list, axis=0)
    print(f"▶ Combined labels shape: {combined_labels.shape}")

    # 5) 최종 .npz 파일로 저장
    #    키 이름은 'all_train_data'로 지정
    os.makedirs(os.path.dirname(output_npz_path), exist_ok=True)
    np.savez(
        output_npz_path,
        all_train_data=combined_array,
        all_train_labels=combined_labels
    )
    print(f"\n Saved final combined NPZ: '{output_npz_path}'\n")

    # (선택) 임시 .npy 파일 삭제를 원한다면 아래 주석을 풀어 주세요.
    for npy_path in npy_paths:
        os.remove(npy_path)
    os.rmdir(npy_temp_dir)


# =========================
# 4. 메인 실행부: 경로만 수정해서 사용
# =========================
if __name__ == "__main__":
    # =========================================
    # ★ 자신의 환경에 맞게 아래 경로들을 수정 ★
    # =========================================
    parent_dir = 'data/StandUp_Data'  
    #   └ 이 폴더 안에서 모든 '*.csv' 파일을 읽습니다.

    # 최종으로 저장할 NPZ 파일 경로 (폴더가 없으면 자동 생성됨)
    output_npz_path = './standup'
    label           = 'standup'   # 모든 시퀀스를 지정된 클래스의 문자열로 라벨링
    # =========================================
    #            실행
    # =========================================
    convert_folder_csv_to_combined_npz(parent_dir, output_npz_path, label, file_pattern='*.csv')


