import os
import pandas as pd
import numpy as np

# ──────────────────────────────────────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────────────────────────────────────

# 1) 원본 CSV들이 들어있는 폴더 경로
input_dir = "walking"

# 2) 증강된 파일을 저장할 새 폴더 경로
output_dir = "walking_noise"

# 만약 output_dir이 존재하지 않으면 생성
os.makedirs(output_dir, exist_ok=True)

# 3) 노이즈 강도 비율 (예: 0.2면 해당 컬럼 표준편차 * 0.2 크기의 σ로 노이즈 생성)
noise_std_ratio = 0.2

# ──────────────────────────────────────────────────────────────────────────────
# 1) 입력 폴더 내 모든 CSV 파일 목록 가져오기
# ──────────────────────────────────────────────────────────────────────────────

# 파일명이 .csv로 끝나는 파일만 선택
csv_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".csv")]

if not csv_files:
    raise FileNotFoundError(f"폴더 '{input_dir}' 내에 .csv 파일이 없습니다.")

# ──────────────────────────────────────────────────────────────────────────────
# 2) 각 파일마다 반복하면서 노이즈 추가 및 저장
# ──────────────────────────────────────────────────────────────────────────────

for filename in csv_files:
    input_path = os.path.join(input_dir, filename)
    
    # 2-1) CSV 로드
    df = pd.read_csv(input_path)
    
    # 2-2) xPos, yPos, zPos 컬럼에만 가우시안 노이즈 추가
    for col in ["xPos", "yPos", "zPos"]:
        if col not in df.columns:
            raise KeyError(f"'{col}' 컬럼을 '{filename}'에서 찾을 수 없습니다.")
        data = df[col].astype(float).values
        sigma = np.std(data) * noise_std_ratio
        noise = np.random.normal(loc=0.0, scale=sigma, size=data.shape)
        df[col] = data + noise
    
    # 2-3) 저장할 파일명 생성: 원본 이름에 "_noise" 붙이기
    name, ext = os.path.splitext(filename)
    new_name = f"{name}_noise{ext}"
    output_path = os.path.join(output_dir, new_name)
    
    # 2-4) 노이즈가 추가된 DataFrame을 새 폴더에 저장
    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")

print("모든 파일에 대해 Gaussian noise를 적용하여 저장 완료했습니다.")