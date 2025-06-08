import pandas as pd
import os
import glob

# ▶ CSV 파일들이 들어있는 폴더 경로 (raw string으로 지정)
DATA_DIR = r'C:\Users\moong\Desktop\fall_detect-main_2\src\dataCollect\data'
# ▶ 결과를 저장할 하위 폴더 이름
OUTPUT_SUBDIR = 'filledData'
TARGET_COUNT = 60  # 목표 프레임 개수
MIN_FRAME_THRESHOLD = 30  # 최소 프레임 수

def fill_missing_frames(df: pd.DataFrame,
                        frame_col: str = 'frameNum',
                        target_count: int = TARGET_COUNT):
    """
    - 항상 start 프레임부터 (start + target_count - 1)까지 순회
      • 기존 프레임이 있으면 원본 사용
      • 없으면 직전 데이터를 복제하여 채움
    """
    df = df.copy()
    if 'Unnamed: 0' in df.columns:
        df.drop(columns='Unnamed: 0', inplace=True)

    frames = sorted(df[frame_col].unique())
    start = frames[0]
    new_end = start + target_count - 1

    chunks = []
    for f in range(start, new_end + 1):
        if f in frames:
            chunk = df[df[frame_col] == f].copy()
        else:
            prev = chunks[-1]
            chunk = prev.copy()
            chunk[frame_col] = f
        chunks.append(chunk)

    filled_df = pd.concat(chunks, ignore_index=True)
    return filled_df, start, frames[-1], new_end

def process_all_files(data_dir: str):
    # 입력 파일 패턴
    pattern = os.path.join(data_dir, 'clust_*.csv')
    files = glob.glob(pattern)
    if not files:
        print(f"[WARN] 처리할 파일이 없습니다: {pattern}")
        return

    # 출력 폴더 생성
    output_dir = os.path.join(data_dir, OUTPUT_SUBDIR)
    os.makedirs(output_dir, exist_ok=True)

    for in_path in files:
        name = os.path.basename(in_path)
        print(f"\n[PROCESSING] {name}")

        # 1) CSV 읽기
        try:
            df = pd.read_csv(in_path)
        except Exception as e:
            print(f"[ERROR] {name}: 파일을 읽는 중 오류 발생 -> {e}")
            continue

        # 2) 'frameNum' 컬럼 존재 확인 및 고유 프레임 수 계산
        if 'frameNum' not in df.columns:
            print(f"[WARN] {name}: 'frameNum' 컬럼이 없어 처리하지 않음")
            continue

        unique_frames = sorted(df['frameNum'].unique())
        frame_count = len(unique_frames)

        # 3) 최소 프레임 수 미만 시 파일 삭제 후 스킵
        if frame_count < MIN_FRAME_THRESHOLD:
            try:
                os.remove(in_path)
                print(f"[INFO] {name}: 고유 프레임 수={frame_count}개로 {MIN_FRAME_THRESHOLD}프레임 미만 → 파일 삭제 후 보간 작업 스킵")
            except Exception as e:
                print(f"[ERROR] {name}: 파일 삭제 중 오류 발생 -> {e}")
            continue

        # 4) 프레임 수가 충분하면 보간 작업 수행
        filled_df, start, end, new_end = fill_missing_frames(df)

        orig_count = end - start + 1
        new_count = new_end - start + 1
        action = "잘라냄" if orig_count > TARGET_COUNT else "채움"
        print(f"[INFO] {name}: 원본 프레임 {start}→{end} (count={orig_count}), "
              f"{action} → {new_end} (count={new_count})")

        # 5) 보간된 결과 저장
        out_name = os.path.splitext(name)[0] + '_filled.csv'
        out_path = os.path.join(output_dir, out_name)
        try:
            filled_df.to_csv(out_path, index=False)
            print(f"[SAVED] {os.path.basename(out_path)} → {OUTPUT_SUBDIR}/")
        except Exception as e:
            print(f"[ERROR] {name}: 보간된 파일 저장 중 오류 발생 -> {e}")

if __name__ == '__main__':
    if not os.path.isdir(DATA_DIR):
        raise FileNotFoundError(f"지정된 폴더가 없습니다: {DATA_DIR}")
    process_all_files(DATA_DIR)