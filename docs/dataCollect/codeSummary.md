# mmWave Data Visualizer - Code Summary

TI Visualizer 기반으로 제작되었으며, **데이터 수집 및 후처리**에 필요한 기능만 선택적으로 구현한 프로젝트입니다.

---

## 📁 파일 구성

| 파일명            | 설명 |
|------------------|------|
| `converter.py`   | GUI 및 주요 기능 구현 (센서 연결, cfg 전송, ini 저장, csv 변환 등) |
| `bm_icon.ico`    | 프로그램 아이콘 |
| `parseTLVs.py`   | TLV 파싱 메서드 정의 (Demo에 맞는 TLV format 처리) |
| `tlv_defines.py` | TLV type 구분용 상수 정의 |
| `addCluster.py`  | CSV 저장 시 자동 클러스터링 및 전역 추적 기능 수행 (DBSCAN + Kalman Filter + Hungarian 매칭 통합) |

---

## 🧩 주요 클래스 구성 (`converter.py`)

### `Window`
- PyQt 기반 UI 클래스
- 버튼과 기능 연결 담당
- 실제 기능은 `Core` 클래스에서 수행

### `Core`
- 센서 포트 연결
- cfg 파일 전송
- 파일 선택 및 ini 설정 저장
- CSV 변환 등 주요 기능 담당

### `UARTParser`
- UART 시리얼 데이터를 파싱하여 frame 생성
- TLV 프레임 완성 및 TLV 단위 데이터 조합 처리

### `TableConvert`
- `outputDict`를 CSV로 변환
- Demo에 따라 새로운 변환 로직 추가 필요

### `parseUartThread`, `saveTimerThread`
- 데이터 수신 및 저장 타이머를 위한 스레드 클래스

---

## ➕ `addCluster.py` – 클러스터링 및 전역 추적

### ✅ 실행 조건
- GUI 내 `Add auto Cluster Information` 체크 시 `.csv` 저장과 함께 자동 실행

### ✅ 주요 처리 과정
1. 프레임별 포인트 클라우드 데이터를 읽어옴
2. `DBSCAN`으로 3D 클러스터링 수행
3. 각 클러스터를 `Kalman Filter`로 추적
4. `Mahalanobis 거리 + Gating` + `Hungarian 매칭`으로 트랙-클러스터 매칭
5. 전역 `global_cluster` ID 부여 및 결과 저장

### ✅ 클래스 구성
- `Cluster` : 전체 프로세스 실행 담당
- `TrackBuffer` : 트랙 상태 관리, 거리 계산 및 매칭
- `ClusterTrack` : 개별 트랙에 Kalman 필터 적용
- `PointCluster` : 클러스터 특성 계산
- `KalmanState` : 6D 위치-속도 상태 필터 정의
- `BatchedData` : 트랙별 시계열 누적 데이터 관리

### ✅ 출력 포맷 (`clust_*.csv`)
| 컬럼명          | 설명 |
|----------------|------|
| `frameNum`     | 프레임 번호 |
| `xPos`, `yPos`, `zPos` | 3차원 위치 |
| `Doppler`      | 속도 크기 (vx, vy, vz norm) |
| `SNR`          | 신호 대 잡음비 |
| `cluster`      | DBSCAN 클러스터 ID |
| `global_cluster` | 프레임 간 추적을 통해 유지되는 전역 클러스터 ID |

### ✅ 주요 파라미터
- `EPS`: DBSCAN 반경 (기본값: `0.7`)
- `MIN_SAMPLE`: 클러스터 최소 포인트 수 (기본값: `20`)
- `GATING_THRESHOLD`: 트랙-클러스터 연결 허용 거리 (기본값: `15.0`)
- `SEQ_SIZE`: 프레임 누적 수 (기본값: `5`)

---

## 🔧 사용자 커스터마이징
- `addCluster.py`는 독립적 전처리 모듈로, 사용자가 직접 알고리즘 수정 및 확장 가능
- 다양한 후처리 로직 추가 및 조건 조정 가능

---
