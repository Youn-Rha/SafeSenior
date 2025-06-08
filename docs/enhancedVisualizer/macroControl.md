## 🧭 개요
`macroControl.py`는 전체 시스템에서 사용되는 주요 **상수값**, **매크로 정의**, 그리고 **모델 경로 및 시퀀스 파라미터**들을 중앙에서 관리합니다. 이를 통해 각 모듈에서 동일한 기준으로 동작하도록 일관성을 유지합니다.

---

## 📁 주요 상수 목록

| 변수명 | 설명 |
|--------|------|
| `DEBUG_AI_INPUT_CONVERSION` | AI 입력 전처리 과정에서 좌표계 변환 여부 결정 |
| `SEQ_SIZE` | Fall Detection을 위한 시퀀스 프레임 길이 |
| `MODEL_PATH` | 학습된 딥러닝 모델의 경로 |
| `MAX_SEQ_NOISE_LEN` | 노이즈 프레임 허용 최대 개수 |
| `MODEL_SEQ_SIZE` | AI 모델의 입력 시퀀스 길이 |
| `CLUST_MIN_SAMPLES` | DBSCAN 클러스터 최소 샘플 수 |
| `CLUST_EPS` | DBSCAN 클러스터링 반경 거리 |
| `USE_KALMAN` | 칼만 필터 적용 여부 설정 |
| `MAX_TRACK_AGE` | 클러스터 잔류 추적 최대 프레임 수 |
| `MIN_TRACK_AGE` | 추적 유효성 판단 최소 프레임 수 |
| `ASSOCIATION_DISTANCE_THRESHOLD` | 클러스터 간 거리 기반 연결 임계값 |

---

## 🧠 사용 목적
- 전역 설정 파일로써, 다양한 모듈 간 상수 공유
- 실험 및 튜닝 시 반복되는 수정 최소화
- 가독성과 유지보수성 향상

---

## 🔧 관련 파일
- [`fall_detection.py`](fall_detection.md): 모델 시퀀스, 노이즈 제어 관련 상수 사용
- [`addCluster.py`](addCluster.md): 칼만 필터 및 트래킹 관련 상수 사용
