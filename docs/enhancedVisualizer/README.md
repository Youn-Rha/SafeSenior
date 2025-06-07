
# 🛰 SafeSenior - Enhanced mmWave Fall Detection System

## 🧭 프로젝트 개요
SafeSenior는 **mmWave 레이더 센서를 기반으로 낙상(Fall), 걷기(Walk), 일어서기(Stand Up)** 등의 움직임을 감지하고, **딥러닝 모델을 통해 실시간 추론**을 수행하는 시스템입니다. 고령자의 안전을 위한 낙상 모니터링 솔루션으로서, 객체 트래킹, 클러스터링, 시각화, 데이터 수집, 그리고 CNN-LSTM 기반 AI 추론까지 통합되어 있습니다.

---

## 📁 디렉토리 구조
```
SafeSenior/
├── src/
│   └── enhancedVisualizer/
│       ├── addCluster.py         # Kalman 필터 기반 트래킹 및 클러스터 ID 부여
│       ├── core.py               # Qt 기반 GUI 제어 및 시스템 연동
│       ├── fall_detection.py     # CNN-LSTM 기반 낙상 예측 처리
│       ├── graph_utilities.py    # Qt 시각화용 2D 그래프 유틸
│       ├── gui_threads.py        # PySide2 기반 시각화 및 시리얼 통신 쓰레드
│       ├── macroControl.py       # 전역 설정 매크로 및 모델 파라미터 관리
│       ├── parseTLVs.py          # TLV 데이터 구조 파싱
│       ├── plot_3d.py            # 3D 포인트 클라우드 시각화
│       └── tlv_defines.py        # TLV 타입 상수 정의
└── docs/
    └── enhancedVisualizer/
        └── *.md                  # 각 파일 별 문서 설명
```

---

## 🧠 핵심 기능

### 🔍 1. mmWave PointCloud 처리
- 레이더 센서로부터 **x, y, z, Doppler, SNR** 데이터를 수신
- `parseTLVs.py`, `tlv_defines.py`를 이용해 TLV 구조 해석 및 변환

### 👣 2. 객체 클러스터링 및 트래킹
- `addCluster.py`에서 **DBSCAN**을 이용한 프레임별 클러스터링
- Kalman Filter로 클러스터의 위치를 추정하여 **ID 일관성 유지**
- `fall_detection.py`에서는 클러스터 간 연속성 분석

### 🤖 3. 행동 인식 (AI 기반)
- CNN + LSTM 기반 모델을 통해 움직임 시퀀스를 분석
- 60프레임 단위 슬라이딩 윈도우 입력으로 `Fall`, `Stand Up`, `Walk` 예측
- `fall_detection.py` 내부의 `InferThread`에서 실시간 추론

### 🖥 4. 실시간 시각화 (2D/3D)
- `graph_utilities.py`: Qt 기반 2D 도플러/좌표 시각화
- `plot_3d.py`: Matplotlib 기반의 3D 포인트 시각화 지원

### 💾 5. 데이터 수집 및 변환
- `core.py`를 중심으로, 사용자 조작에 따라 데이터를 csv로 저장
- `TableConvert`, `UARTParser` 등을 통해 센서 데이터 전처리 및 저장 가능

---

## 🔁 실행 흐름 요약
1. `converter.py` or GUI 실행 → 센서 연결
2. UART 포트를 통해 mmWave 데이터 수신 → TLV 파싱
3. 프레임별 클러스터링 → Kalman 필터 기반 트래킹
4. 클러스터별 시퀀스 구성 → CNN-LSTM 추론
5. 실시간 결과 시각화 및 CSV 저장

---

## ⚙️ 사용 기술 스택
- **Python 3.8+**
- **PySide2 (Qt 기반 GUI)**
- **scikit-learn** (DBSCAN, StandardScaler)
- **TensorFlow / Keras** (딥러닝 추론)
- **matplotlib** (3D 플롯)
- **pandas / numpy / scipy**

---

## 🧪 향후 발전 방향
- [ ] 멀티 인원 동시 낙상 인식 개선
- [ ] BLE 기반 웨어러블 연동
- [ ] 영상 기반 AI 모델과의 하이브리드 처리
- [ ] 웹 기반 실시간 낙상 알림 서비스 연계

---

## 📄 참고 문서
각 모듈별 문서는 `docs/enhancedVisualizer/` 폴더에 포함되어 있습니다:

- [`addCluster.md`](addCluster.md)
- [`core.md`](core.md)
- [`fall_detection.md`](fall_detection.md)
- [`graph_utilities.md`](graph_utilities.md)
- [`gui_threads.md`](gui_threads.md)
- [`macroControl.md`](macroControl.md)
- [`parseTLVs.md`](parseTLVs.md)
- [`plot_3d.md`](plot_3d.md)
- [`tlv_defines.md`](tlv_defines.md)

---
