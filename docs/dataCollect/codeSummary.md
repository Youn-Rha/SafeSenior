# Code Summary
* Ti Visualizer 기반, 데이터 수집에 필요한 기능만 선택하여 구현

## 파일 구성
* converter.py
    * GUI와 주 기능을 구현
* bm_icon.ico
    * 프로그램 아이콘
* parseTLVs.py
    * TLV 파싱에 필요한 메서드 정의
    * demo에서 사용하는 TLV에 대응하는 각 parsing 메서드 정의가 필요
* tlv_defines.py
    * TLV type 구분에 필요한 매크로 상수 정의

## converter.py
### class 구성
* Window : Qt Window 구현, layout과 연결된 기능을 정의, 세부 구현은 Core 통해 구현
* Core : 주요 기능을 구현
* UARTParser : USB UART 통신을 통해 받은 frame을 파싱하는 기능, 포트 연결, cfg 전송을 담당
* TableConvert : demo에 대응하는 TLV를 csv 테이블로 변환하는 기능을 구현
    * demo 추가에 맞추어 변환 기능 구현이 필요
* parseUartThread, saveTimerThread : thread 정의