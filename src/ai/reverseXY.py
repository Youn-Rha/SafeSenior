import os
import pandas as pd

# ──────────────────────────────────────────────────────────────────────────────
# Data Augmentation Code
# ──────────────────────────────────────────────────────────────────────────────

# 1) 원본 CSV들이 들어있는 폴더 경로
input_dir = "walking"

# 2) 증강된(플리핑된) 파일을 저장할 새 폴더 경로
output_dir = "walking_flipped"
os.makedirs(output_dir, exist_ok=True)

# 3) x, y 축 부호 반전 설정 (True/False)
flip_x = True   # x축 부호를 반전할지 여부
flip_y = False  # y축 부호를 반전할지 여부

# ──────────────────────────────────────────────────────────────────────────────
# 1) 입력 폴더 내 모든 CSV 파일 목록 가져오기
# ──────────────────────────────────────────────────────────────────────────────

csv_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".csv")]
if not csv_files:
    raise FileNotFoundError(f"폴더 '{input_dir}' 내에 .csv 파일이 없습니다.")

# ──────────────────────────────────────────────────────────────────────────────
# 2) 각 파일마다 반복하면서 부호 반전 적용 및 저장
# ──────────────────────────────────────────────────────────────────────────────

for filename in csv_files:
    input_path = os.path.join(input_dir, filename)
    df = pd.read_csv(input_path)
    df_aug = df.copy()
    
    # (1) x축 반전
    if flip_x:
        if "xPos" not in df_aug.columns:
            raise KeyError(f"'{filename}' 파일에 'xPos' 컬럼이 없습니다.")
        df_aug["xPos"] = -df_aug["xPos"].astype(float)
    
    # (2) y축 반전
    if flip_y:
        if "yPos" not in df_aug.columns:
            raise KeyError(f"'{filename}' 파일에 'yPos' 컬럼이 없습니다.")
        df_aug["yPos"] = -df_aug["yPos"].astype(float)
    
    # (3) 저장할 파일명 생성: 원본 이름에 "_flipped" 붙이기
    name, ext = os.path.splitext(filename)
    new_name = f"{name}_flipped{ext}"
    output_path = os.path.join(output_dir, new_name)
    
    # (4) 플리핑된 DataFrame을 새 폴더에 저장
    df_aug.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")

print("폴더 내 모든 파일에 대해 부호 반전을 적용하여 저장 완료했습니다.")