## 🧭 개요

`enhancedVisualizer`는 SafeSenior 프로젝트 내에서 핵심적인 시각화 및 클러스터 트래킹, 낙상 감지 기능을 담당하는 모듈입니다. 기존 TI Visualizer 기반 시스템을 확장하여 Kalman 필터 기반 트래킹, Hungarian 매칭, 딥러닝 낙상 감지 모델 등을 통합합니다.

본 폴더는 해당 모듈에 대한 문서화를 목적으로 하며, 각 주요 구성 요소에 대한 상세 문서를 함께 제공합니다.

---

## 📂 구성 파일 및 설명

| 파일 / 폴더              | 설명                                                  |
| -------------------- | --------------------------------------------------- |
| `addCluster.py`      | DBSCAN + Kalman 필터 + Hungarian 알고리즘을 통한 클러스터 트래킹 구현 |
| `fall_detection.py`  | CNN-LSTM 기반 낙상 감지 모델과 실시간 추론 처리 모듈                  |
| `core.py`            | GUI 메인 흐름을 제어하는 핵심 진입점 코드                           |
| `macroControl.py`    | 그래프 UI 및 제어 유틸리티 함수 정의                              |
| `graph_utilities.py` | 시각화를 위한 보조 함수들 (예: 3D plotting 등)                   |
| `parseTLVs.py`       | TLV 타입 데이터 파싱을 위한 함수 정의                             |
| `tlv_defines.py`     | TLV 타입 상수 정의 및 매핑                                   |
| `plot_3d.py`         | 포인트 클라우드 및 객체를 3D로 시각화하는 함수 정의                      |
| `img/`               | GUI에 사용되는 아이콘 및 인물 이미지 리소스                          |
| `model/`             | 낙상 감지에 사용되는 학습된 모델 파일들 (H5 format)                  |
| `test/`              | 기능 검증용 테스트 스크립트 및 샘플 데이터 포함                         |

---

## 🔧 실행 조건 및 요구 사항

* Python 3.8+
* 주요 의존성은 `requirements.txt` 파일 참고
* 모델 파일은 사전 학습된 `.h5` 포맷을 사용

---

## 📌 문서 구성

* [`addCluster.md`](addCluster.md) : 클러스터링 및 트래킹 기능 설명
* [`fall_detection.md`](fall_detection.md) : 낙상 감지 모델 및 처리 흐름 설명
* [`core.md`](core.md) : GUI 흐름 및 전체 시스템 컨트롤 구조

> 추가 문서는 점진적으로 작성 및 반영 예정입니다.

---
