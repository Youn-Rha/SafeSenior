## 🧭 개요

`parseTLVs.py`는 mmWave 센서로부터 수신한 바이너리 데이터를 **TLV (Type-Length-Value)** 구조로 파싱하여, 사용 가능한 포인트 클라우드 데이터로 변환하는 기능을 수행합니다. 이 모듈은 `UARTParser` 또는 `DataReceiverThread`에서 호출되어 **프레임 단위 데이터 처리의 핵심**을 담당합니다.

---

## 🗂️ 주요 함수

### `parse_frame(frame_bytes: bytes) -> dict`
- 수신된 raw binary 데이터를 TLV 단위로 파싱
- frame header를 읽고, TLV 수 만큼 루프를 돌며 데이터를 해석
- 반환값: `outputDict` (e.g., pointCloud, numDetectedPoints 등 포함)

### `parse_detected_points(data: bytes) -> List[Tuple]`
- TLV type이 point cloud일 때 호출
- 포맷에 맞춰 각 포인트의 `x, y, z, Doppler, SNR` 등을 추출

### `parse_classification(data: bytes) -> Dict`
- TLV에 객체 분류 정보가 포함된 경우 처리
- 딥러닝 결과 혹은 레이블 정보 포함 가능

---

## 📦 TLV 구조 처리 방식

```
[Frame Header][TLV Header][TLV Payload]...[TLV Header][TLV Payload]
```

- **Frame Header**: 마법 넘버, frameLength, numTLVs 등 포함
- **TLV Header**: Type, Length
- **TLV Payload**: 타입에 따라 포맷 다름 (Point Cloud, Classification 등)

---

## 📥 입력 데이터 예시

```python
b'\x02\x01\x04\x03...'  # binary stream from UART
```

---

## 📤 출력 데이터 예시 (outputDict)

```json
{
  "numDetectedPoints": 28,
  "pointCloud": [
    [0.1, -0.2, 1.4, -3.2, 10.1],
    ...
  ]
}
```

---

## 🔧 의존 모듈

- `tlv_defines.py`: TLV 타입 번호와 의미 매핑
- `struct`: 바이너리 해석
- `numpy`, `math`: 데이터 정규화 및 수치 처리

---

## 📝 참고 문서

- [`gui_threads.md`](gui_threads.md): 이 모듈을 호출하는 센서 수신 스레드
- [`core.md`](core.md): 전체 흐름에서 데이터 파싱 호출 위치 확인 가능
