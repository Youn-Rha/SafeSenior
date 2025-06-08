## 🧭 개요

`gui_threads.py`는 mmWave 시각화 시스템에서 **실시간 데이터 수신 및 재생 처리**를 위해 설계된 비동기 스레드 로직을 포함합니다. 센서 수신, 파일 재생, 프레임 emit 등 GUI에 영향을 주는 연산을 독립적으로 처리하여 **UI 프리징 현상 방지**를 목적으로 합니다.

---

## 🧩 주요 클래스 및 메서드

### 1. `DataReceiverThread(QThread)`
- UART 기반 센서 연결 상태에서 실행되는 스레드
- `run()` 메서드:
  1. 센서 포트에서 TLV 데이터 수신
  2. `parseTLVs.parse_frame()`을 호출해 `outputDict` 생성
  3. `update_frame` 시그널을 emit하여 UI에 데이터 전달
- 예시:
  ```python
  self.update_frame.emit(outputDict)
  ```

---

### 2. `ReplayThread(QThread)`
- `.csv` 파일을 프레임 단위로 읽어 재생하는 스레드
- `run()` 메서드:
  1. 파일을 DataFrame으로 읽고 `frameNum` 기준으로 정렬
  2. 주어진 `interval`마다 `update_frame` 시그널 emit
  3. 끝까지 재생되면 `replay_done` 시그널 발생
- 사용 예:
  ```python
  self.update_frame.emit(outputDict)
  self.replay_done.emit()
  ```

---

### 3. `GUIThreadController`
- `start_sensor()`, `start_replay()` 등의 요청을 받아 스레드를 생성 및 관리
- 중복 실행 방지, 종료 처리, 모드 전환(센서/재생)을 조율함
- 예시:
  ```python
  self.sensor_thread = DataReceiverThread(...)
  self.sensor_thread.update_frame.connect(self.update_plot)
  ```

---

## 🔄 Signal-Slot 구조 요약

| Signal | 설명 | 연결 대상 예시 |
|--------|------|----------------|
| `update_frame` | 새 프레임 수신 시 emit | `VisualizerCore.update_plot()` |
| `replay_done` | 파일 재생 종료 | `on_replay_finished()` |
| `error_signal` | 센서 연결 실패 등 오류 시 | `status_bar.showMessage()` 등 |

---

## 📁 연결 흐름 예시

```python
# 센서 시작
self.sensor_thread = DataReceiverThread(serial, parser)
self.sensor_thread.update_frame.connect(self.update_plot)
self.sensor_thread.start()

# 재생 모드
self.replay_thread = ReplayThread(filepath)
self.replay_thread.update_frame.connect(self.update_plot)
self.replay_thread.replay_done.connect(self.replay_finished)
```

---

## 📝 참고 문서

- [`core.md`](core.md): 이 스레드들을 호출하고 통제하는 중심 컨트롤러
- [`parseTLVs.md`](parseTLVs.md): UART 데이터 파싱 처리 구조
- [`plot_3d.py`](plot_3d.md): 시각화와 연결되는 최종 렌더링 처리
