## 🧭 개요

`addCluster.py`는 mmWave 레이더 센서에서 수집된 포인트 클라우드 데이터를 입력받아, **3차원 클러스터링 + 프레임 간 트래킹**을 수행하는 전처리 모듈입니다. 주요 목적은 사람 단위의 객체 추적을 가능하게 하여, 후속 낙상 감지 및 행동 인식 모델의 입력으로 사용할 수 있는 정제된 데이터셋을 생성하는 것입니다.

---

## ⚙️ 주요 기능

### ✅ 1. DBSCAN 클러스터링

* 입력: 한 프레임의 point cloud (3D 좌표 + 속도 + SNR)
* 출력: 클러스터 ID가 부여된 점들의 그룹
* 파라미터: `EPS`, `MIN_SAMPLE`

### ✅ 2. Kalman 필터 기반 클러스터 예측

* 클러스터 중심점의 위치 및 속도 추정을 위한 Kalman 필터 적용
* 상태 벡터: 위치 (x, y, z) + 속도 (vx, vy, vz)

### ✅ 3. Hungarian 매칭 알고리즘

* 프레임 간 클러스터 매칭을 위한 최적 할당
* Mahalanobis 거리 + Gating 조건 기반 필터링
* 글로벌 클러스터 ID (`global_cluster`) 부여

### ✅ 4. 전처리된 CSV 출력

* 클러스터 및 트래킹 결과를 포함하는 DataFrame 반환
* `frameNum`, `xPos`, `yPos`, `zPos`, `Doppler`, `SNR`, `cluster`, `global_cluster` 컬럼 포함

---

## 🧩 주요 클래스 설명

| 클래스명           | 역할                        |
| -------------- | ------------------------- |
| `Cluster`      | 전체 클러스터링 및 트래킹 프로세스 제어    |
| `TrackBuffer`  | 트랙 리스트 관리, 클러스터-트랙 매칭 수행  |
| `ClusterTrack` | Kalman 필터와 함께 트랙 단위 상태 유지 |
| `PointCluster` | 클러스터 중심/속도/공분산 등 계산       |
| `KalmanState`  | Kalman 필터 상태 정의 (6D 상태)   |
| `BatchedData`  | 트랙별 과거 프레임 누적 관리 (deque)  |

---

## 📥 반환 포맷 예시

```csv
frameNum,xPos,yPos,zPos,Doppler,SNR,cluster,global_cluster
1,0.53,0.71,1.2,0.84,12.1,2,1
1,0.55,0.72,1.1,0.85,11.7,2,1
...
```

---

## 🔧 참고 설정 값

```python
EPS = 0.7
MIN_SAMPLE = 20
GATING_THRESHOLD = 15.0
SEQ_SIZE = 5
```

---

## 📝 참고 사항

* Gating 조건이 완화되어 있어 3명 이상 추적 상황에서도 robust하게 동작
* 잘못된 예측 시 fallback으로 새 트랙 생성됨
* 클러스터 중심과 트랙 중심의 거리 차이가 기준보다 클 경우 새 ID 부여

---

## 📎 관련 문서

* [`README.md`](README.md): 전체 enhancedVisualizer 모듈 개요
* [`fall_detection.md`](fall_detection.md): 추적된 데이터 기반 행동 분석 모듈
