## 🧭 개요

`core.py`는 `enhancedVisualizer` 모듈의 핵심 컨트롤러로, 사용자 인터페이스(UI), 시각화 모듈, 센서 연결, 추론 기능 등을 통합 관리합니다. Qt 기반 UI 이벤트를 연결하여, 사용자의 입력에 따라 센서 데이터를 수집하고 3D 시각화 및 딥러닝 기반 낙상 감지를 수행합니다.

---

## 🧩 주요 클래스

| 클래스 | 설명 |
|--------|------|
| `VisualizerCore` | UI 및 내부 모듈을 통합 관리하는 중심 클래스 |
| `PlotUpdater` | 시각화 갱신을 위한 주기적 타이머 (3D plot update) |
| `DataHandler` _(optional)_ | 센서 수신 데이터 정리 및 포맷 처리 (있을 경우) |

---

## ⚙️ 주요 기능

### ✅ UI 이벤트 연결
- Qt 버튼 클릭 → 슬롯 함수 연결
- 예시:  
  ```python
  self.ui.btnStart.clicked.connect(self.start_sensor)
  ```

### ✅ 센서 연결 및 데이터 수집
- UART 포트를 통해 mmWave 센서에 연결
- `parseTLVs`를 활용하여 TLV → point cloud 변환 수행

### ✅ 실시간 시각화
- `plot_3d.py`와 연결
- `PlotUpdater`를 통해 실시간 redraw

### ✅ 딥러닝 추론
- `fall_detection.FallDetection` 객체와 연동
- `InferThread` 실행 → 결과 시그널 emit → 상태 업데이트

### ✅ 데이터 저장 및 불러오기
- 센서 수집 데이터를 `.csv`로 저장
- 과거 데이터를 불러와 시각화 가능 (`Replay`)

---

## 🔄 Signal-Slot 구조

| Signal 발생 | 연결된 Slot 함수 |
|-------------|------------------|
| `Start` 버튼 클릭 | `start_sensor()` |
| `Stop` 버튼 클릭 | `stop_sensor()` |
| `Open` 버튼 클릭 | `open_file()` |
| 센서 데이터 수신 완료 | `update_plot()` |
| 추론 결과 발생 | `stateTransition()` |

---

## 🧼 기타 기능

- `.cfg` 파일 선택 후 센서 설정 전송
- 프로그램 설정 저장 (GUI 상태, 센서 정보 등)
- 라벨링 모드/테스트 모드 분기 처리
- 상태 표시 (센서 연결 상태, 포트 정보 등)

---

## 🔧 사용 전제 조건

- `PySide2`, `matplotlib`, `numpy`, `tensorflow` 등 필요 패키지 설치
- `model/` 폴더 내 모델 존재 (`*.h5`)
- 센서 연결을 위한 USB UART 포트가 OS에서 인식되어야 함

---

## 📎 관련 문서

- [`fall_detection.md`](fall_detection.md) – 낙상 감지 모델 설명
- [`addCluster.md`](addCluster.md) – 클러스터 기반 전처리
- [`gui_threads.md`](gui_threads.md) – UI 스레드 구조
- [`parseTLVs.md`](parseTLVs.md) – TLV 파싱 구조 설명

---

