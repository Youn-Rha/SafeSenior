# Data Collector
* IWR7843ISK(이하 센서)의 신호를 csv table로 변환하는 프로그램
* 센서에 업로드한 demo와 센서에 전송할 cfg 파일을 선택 가능

## 주요기능
* UART 통신을 통해 센서와 통신
* cfg 값의 전송
    * 정상 리셋되지 않은 센서와의 통신에서 프로그램 멈추는 현상 방지
* 센서 처리 데이터를 수신
* 수신한 데이터를 csv table로 변환
* 이전에 사용한 값 ini 파일에 캐싱

## 구동환경
* [센서 연결에 필요한 드라이버 설치](./driver%20install.md)
* requirements.txt 참조하여 패키지 설치
```cmd
pip install -r requirements.txt
```
* python 3.5 ~ python 3.10 사용가능, 3.10 추천, conda와 같은 venv 사용가능

## 사용법
* decode.py 실행
* 센서에 업로드한 demo를 선택
    * 리스트에 없는 경우 해당 demo에 대응하는 코드 작성 필요함
    * [센서에 demo falshing 하는 방법](./UniFlash.md)
    * 프로그램 구동 시, 센서 MUX switch가 functional mode에 위치하여야 한다
* 적절한 포트 기입후 Connect
    * 장치 관리자에서 대응하는 포트 찾아서 기입
    * 레이블에 커서 올려놓으면 세부설명 표시됨
    * 연결 실패 시 [센서 리셋](./reference.md) 또는 케이블 변경 필요
* 미리 작성한 cfg 파일 선택
    * cfg 값 설정에 따라 수집 데이터 정확도가 결정되므로, 데이터 수집 공간에 맞는 cfg 설정이 필요
        * 설정 방법은 [해당 자료](./cfgTunning.md) 참조 (demo에 따른 설정 방법이 상이함)
* Start with config로 데이터 수집 시작
    * 지정시간(기본 10초)마다 별도의 파일로 데모에 대응하는 데이터가 수집
    * 중단 후 재시작 할 경우, 물리 버튼 통한 센서 리셋 필요

## 빌드
* exe 파일로 빌드가능
* [빌드하는 방법](./howtoBuild.md)

## 코드 구현
* [해당 파일 참조](./codeSummary.md)