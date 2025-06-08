## 🧭 개요

`tlv_defines.py`는 mmWave 센서에서 수신한 **TLV (Type-Length-Value)** 포맷 데이터를 파싱할 때, TLV 타입을 식별하고 분류하는 데 필요한 **상수 정의 모듈**입니다.  
다양한 TLV Type ID를 정수 상수로 정의하고, 각 ID에 대해 **설명 문자열 매핑**을 제공하여 가독성과 유지보수를 향상시킵니다.

---

## 🔧 주요 상수 정의

```python
TLV_TYPE_DETECTED_POINTS = 1
TLV_TYPE_RANGE_PROFILE = 2
TLV_TYPE_NOISE_PROFILE = 3
...
TLV_TYPE_CLASSIFICATION = 101  # 사용자 정의 타입 (예: fall/sit/walk 분류)
```

---

## 🗂️ TLV 타입 매핑 딕셔너리

```python
TLV_TYPE_MAP = {
    1: "Detected Points",
    2: "Range Profile",
    3: "Noise Profile",
    ...
    101: "Classification Result"
}
```

- 이 매핑은 `parseTLVs.py` 등에서 TLV 타입을 해석할 때 사용됩니다.
- 예:  
  ```python
  tlv_type_name = TLV_TYPE_MAP.get(tlv_type, "Unknown")
  ```

---

## 📌 용도

| 용도 | 설명 |
|------|------|
| TLV 파싱 식별자 정의 | 바이너리 파싱 중 TLV 타입을 매칭하여 해당 처리 함수 결정 |
| UI 디버깅 출력 | TLV 타입을 문자열로 표현하여 디버깅 로그 제공 |
| 사용자 정의 타입 | 100번 이상 ID는 사용자 정의 TLV 확장용으로 사용 가능 |

---

## 📝 참고 문서

- [`parseTLVs.md`](parseTLVs.md): 이 상수를 사용하는 파싱 모듈
- [`gui_threads.md`](gui_threads.md): 센서 수신 후 파싱이 호출되는 구조
- [`core.md`](core.md): 전반적인 데이터 흐름에서 TLV 타입 해석 위치 확인 가능
