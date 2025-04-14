# dataCollect - Programming Guidance
<img src="..\..\img\dataCollect.jpg">

* 3D people tracking demo를 올린 IWR6843 계열 센서의 UART 통신 데이터를 수집하고, 이를 csv 형태로 저장하는 프로그램
    * out of box의 정보도 일부 해석 가능할것으로 예상
    * 필요에 따라 추가 구현으로 demo를 쉽게 지원 가능
* csv 형태로 데이터 저장하여 기계학습 및 replay 등에 사용이 가능
* 체크박스 사용하여 데이터 전처리 완료된 파일도 저장 가능
* 10초마다 주기적으로 자료 저장하며, TLV type과 저장 시각에 맞춰 파일 이름이 결정된다
    * 저장 간격 별도 지정 가능

## 파일 구분
### converter.py
* UI와 UART 기반 센서 통신 스레딩, csv 변환 및, ini 저장 기능 등 프로그램의 핵심 파트
* Window 클래스에 UI와 버튼 시그널 연결이 정의됨
* Core 클래스는 파일 선택, cfg 전송, 센서 연결, ini 파일 관리등을 담당한다
    * ini 파일을 통해 이전 세션의 정보 기록하여 UX 향상
* UARTParser 클래스에서는 UART serial 통신에서 얻은 bit를 조합하여 frame 완성하고, frame을 모아 TLV 데이터를 완성한다
* TableConvert 클래스에서는 outputDict를 csv 파일로 변환하는 내용에 대해 정의한다
* parseUartThread 클래스는 UARTParser 기능을 사용하는 별도 스레드를 정의한다

### addCluster.py
* Add auto Cluster Information 체크박스 체크 시, 파일 저장과 함께 수행되는 메서드를 정의한다
* DBSCAN과 Hungarian 기반한 global clustering을 통한 데이터 전처리를 수행한다
    * 해당 결과는 clust로 시작하는 csv 파일로 저장하게 된다
* DBSCAN의 parameter인 EPS와 min samples를 설정 가능하다
* 전처리 기능은 해당 파일 편집을 통해 추가하거나 수정 가능하다

### parseTLVs.py
* 3D people tracking demo에 사용되는 TLV type에 대한 parsing 메서드를 정의
* frame으로부터 TLV 완성되면, TLV type에 맞는 메서드 호출되어 struct unpack 하고, outputDict에 저장하는 형식
* cloud point의 경우 spherical 좌표계에서 cartesian 좌표계로 변환 연산이 수행된다

### tlv_defines.py
* TLV type 확인을 위한 상수 정의

## 기능별 flow 설명
### ini 기능
1. Window의 생성자에서 self.iniParser로 ConfigParser 생성
2. INI_PATH에 정의된 경로 확인 후, 파일 없다면 ini_create로 생성
3. ini 파일 읽고, get 함수로 변수 초기값 설정
4. Window의 closeEvent에서 ini_save 호출하여 사용한 값을 저장한 후 프로세스 종료

### connect 버튼 누르는 경우
1. clicked.connect로 startConnect 호출
2. 연결 상태를 QLabel의 text 비교 통해 확인
    * 신규 연결 시 connectCom 통해 연결 시도, 성공 여부에 따라 버튼 및 텍스트 변경
        1. 입력 값 기반 포트 지정
        2. uart_thread와 parseTimer 선언
        3. connectComPort로 각 시리얼 포트 연결 및 버퍼 리셋
    * 기존 연결 존재 시 gracefulReset 통해 연결 해제
        * parser 스레드와 uart 스레드를 정지
        * 파일 저장용 스레드 및 타이머 정지
        * 통신용 포트 닫기

### Send config and start 버튼 누르는 경우
1. sendCfg 호출
2. parseCfg 통해 cfg 파일 내용 기록하고 uartSendCfg 통해 cli com port로 내용 전송
3. parseTimer와 saveTimer 시작하게 되며, parseTimer는 SingleShot(False) 이므로 주기적으로 parseData 계속 호출하게 된다
4. parseData는 uart_thread 시작하여 parseUartThread의 readAndParseUartCOMPort 통해 outputDict 생성하게 된다
5. readAndParseUartCOMPort에서는 serial data communication 통해 frame에서 TLV 조립하고, 딕셔너리 형태인 outputDict를 리턴하게 된다
6. 스레드 fin 신호 통해 데모에 대응하는(선택된 데모의 문자에 매칭하는 메서드 호출) demoConvertDict의 메서드를 호출한다
7. outputDict 값을 dict_list_track에 append한다
8. saveTimer에 따라 dict_list_track을 저장하는 saveTable이 호출된다
9. demo_match에 기록된 메서드를 순차 호출하는 형식으로 saveTable이 작동된다
10. peopleTrackSaveCloud에서는 convCheckBox의 체크 상태를 기반으로 addCluster.py의 클러스터링을 수행 여부를 결정하게 된다