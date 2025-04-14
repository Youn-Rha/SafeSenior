# Visualizer
<img src="../../img/enhanced Visualizer.gif">

|enhancedVisualizer|visualizer|
|:---:|:---:|
|차기 AI 탑재용|기존 프로젝트 결과물|
|plotting 오류 해결, 무시가능한 scatter 문제|그래픽 plotting 오류 존재 : 장기 구동 불가능|
|비지도 클러스터링 기반 좌표출력(불안정)|센서 출력 기반 좌표출력|
|정확한 추론 매핑|추론과 사람좌표 불일치 문제|
|Visualizer에서 사람의 이동을 제한|센서에서 사람의 자연스러운 움직임 표현|
|더 긴 시퀸스에서 데이터 모으는 시도|길이 5 시퀸스 통한 상태 판별|
|매크로 상수 통한 파라미터 변경|직접 코드 수정 통한 파라미터 변경|

* 해당 문서는 enhanced Visualizer 기준으로 작성됨
* enhanced Visualizer는 개선될 AI를 고려하여 기능 변경사항을 추가하였기에 AI 구동 성능은 매우 낮음
* 개선될 AI는 RNN 기반 지도 클러스터링과 긴 시퀸스 사용하는 자세 추론 모델을 사용할 것으로 기대함
* 그래픽 plotting 오류의 원인인 타이머 overflow 문제 해결을 위해 상태 표시 컬러 레이블 관리를 위한 ticket system 존재
* 주석처리된 코드는 기존 Visualizer의 코드 또는 신기능 탑재 시도하다 남은 코드이기에 무시하여도 무방함
* 그래픽 관련 내용은 [별도문서](./guideForUI.md) 참조
* 실시간 구동을 위하여 멀티 스레딩 환경에서 동작한다
    * 인원 좌표 출력을 위한 클러스터링의 경우 매 프레임마다 수행되기에 x, y 좌표만 사용한다
    * AI 통한 인원의 상태 판별하는 스레드의 경우 동시에 여러 스레드가 동작하지 않도록 제한한 상태이다
        * semaphore와 같이 시스템에 적합한 구동 스레드 수를 조정하도록 구현하는 것을 추천함
* AI 모델과 데이터 전처리 방식, 또는 펌웨어 변경 등이 이루어 진다면 Visualizer 또한 변경이 필요하다

## 파일 구분

### core.py
* UI Layout과 버튼 연결을 정의
* ini 파싱기능을 정의
    * dataCollect Programming Guidance 참고
* cfg 파싱 및 전송 기능을 정의
* 센서 연결과 프레임 파싱, 그리고 이를 위한 스레드를 정의

### macroControl.py
* Visualizer나 AI의 파라미터 변경과 기능 변경 등을 위해 일부 매크로 상수를 정의한 파일
* 세부 내용은 밑의 macroControl 참고

### gui_threads.py
* 센서에서 outputDict가 생성된 후 이를 처리하는 방식을 정의
* core에서 PeopleTracking 클래스의 updateGraph 호출을 통해 outputDict를 처리하게 되며, updateQTTargetThread3D 클래스를 통해 그래픽 plotting이 수행된다
    * updateGraph에서 'trackData'가 존재 시 (센서가 인식한 사람이 존재 시) fallDetection.step(outputDict)를 통해 상태를 추론하게 된다
    * 위 'trackData'는 이전 visualizer 구조의 잔재로, 지도 클러스터링이 완성되면 cloudPoint여부만 검사후 진행 가능하도록 변경이 필요하다
    * step을 통해 fall_detection.py의 FallDetection 클래스의 step이 호출되며, 그 결과에 따라 updateClusterCache가 수행된다
    * updateClusterCache에 따라서 Visualizer에서 표시되는 좌하단 레이블과 3D 모델 plotting이 결정된다

### fall_detection.py
* FallDetection 클래스는 cloudPoint를 저장한 outputDict로부터 클러스터 정보를 추출하고 sequence 형태로 저장하여 상태 추론 AI에 전달한다
* InferThread는 sequence 형태의 cloudPoint 데이터들을 글로벌 클러스터링 처리하고 AI를 통해 자세를 추론하는 스레드를 정의한다
* Signal 통해 자세에 대한 정보를 전달하여 클러스터 캐쉬 정보를 업데이트하고, 동시 추론 방지를 위한 슬롯 정보와 연속 클러스터의 노이즈 정보를 업데이트한다

### plot_3d.py
* pyqtgraph의 opengl을 사용하여 그래픽적 요소를 출력하는 Plot3D 클래스가 정의
* pointCloud나 boundaryBox를 다루는 메서드 정의
* 센서 위치나 boundaryBox 정보를 파싱하는 함수도 포함됨
    * cfg 읽을 때 호출

### tlv_defines.py
* core의 parseFunctions 딕셔너리에 사용
* frame parsing시 tlvType 매칭 용도

### parseTLVs.py
* parseFunctions에서 tlvType에 따라 매칭되는 파싱 함수를 정의
* 센서에 올린 데모 펌웨어 변경시 추가 사용하는 tlvType에 따라 파싱 함수를 추가 정의할 필요가 있음
    * 함수 추가 시 ti radar toolbox에서 제공하는 industrial visualizer의 코드 참조 필요

## 기능별 flow 설명
### macroControl
* NUM_OF_DETECT_PEOPLE은 탐지할 인원 상한을 지정한다
    * 좌하단에 표시되는 인원수를 결정한다
    * 내부적으로 기록하는 인원의 상한을 결정한다
* HEAD_TYPE는 Visualizer에서 표시되는 3D 모델의 머리 타입을 결정한다
    * CIRCLE_HEAD의 경우 매 plot 마다 윈의 orientation을 카메라 방향을 항하도록 변경한다
    * 3D model의 update 없을 경우 orientation 변경이 없는 상황이다
    * 이는 실험용으로 추가한 기능으로, 편의성을 위해 이와 같이 구현하였으나, 실제로 적용시 별도 타이머를 통해 화면 전환에 따라 매번 orientation update 가 필요하다
* DEBUG_AI_INPUT_CONVERSION은 이전 spherical 좌표계 사용하는 AI 모델을 위한 기능
* STATE 클래스에는 판별할 STATE 종류와 state 표시하는 좌하단 시스템에 사용하는 ticket 값을 정의함
* SEQ_SIZE에 해당하는 수의 프레임을 모아 상태를 추론하게 되며, 추론에서 사용되는 AI 모델의 sequence size가 MODEL_SEQ_SIZE로 정의된다
    * SEQ_SIZE에 해당하는 프레임에 대해 클러스터링한 결과에 MODEL_SEQ_SIZE 이상의 연속 클러스터가 존재할 시 추론을 진행할 수 있다
    * MAX_SEQ_NOISE_LEN 이상의 노이즈 프레임(클러스터가 없는 프레임) 연속으로 들어오면 기존에 모은 sequence를 flush하게 된다
* PATH는 프로그램이 구동되는 path를 지정하며, exe 파일로 제작하는 것을 고려하여 'frozen'여부를 검사한다
* CLUST_MIN_SAMPLES는 DBSCAN에서 한 클러스터의 최소 샘플 수를, CLUST_EPS는 DBSCAN에서의 eps값을 설정한다
* CLUSTER_CACHE는 Visualizer에서 memoization할 클러스터 정보와 특성을 정의한다

### 센서와 connect
1. connectBtn의 클릭은 startConnect로 연결
2. 레이블 텍스트 기반으로 연결 또는 연결 해제를 결정
    * 연결 시 connectCom 호출
    * 해제 시 gracefulReset 호출
3. connectCom은 입력한 텍스트를 기반하여 COM 포트를 지정하고, 스레드를 선언하며 connectComPort를 수행한다
    * uart_thread는 serial communication으로 frame을 만들어 outputDict를 생성하며, fin.connect 통해 updateGraph를 호출한다
    * singleShot 비활성화된 parseTimer 통해 parseData는 cfg에 명시된 정보에 맞추어 버퍼 확인한다
    * 위 두 스레드는 sendCfg 호출에 의해 시작되고, gracefulReset에서 비활성화 된다
4. connectComPort는 2개의 COM port 통한 serial 통신 연결을 수립한다
    * cli_com - baud rate : 115200, no parity
    * data_com - baud rate : 921600, no parity
* serial communication의 값을 parsing하는 것은 parseUartThread 산하의 UARTParser 클래스에 명시됨

### PeopleTracking의 updateGraph
* sendCfg에 의해 시작되는 uart_thread 통해 정기적으로 호출되며, outputDict와 함께 전달되어 시작됨
* outputDict를 파싱하여 정보를 그래픽으로 출력하는 기능에, 자세(상태)를 추론하고 클러스터 정보를 처리하는 step 함수가 추가된 형태
* 클러스터 정보는 updateClusterCache, 자세 정보는 stateTransition을 통해 처리
* updateGraph는 scatter 위해 이전 사용한 previousClouds에 outputDict 정보 합친 cumulativeCloud를 만든다
* 현 시스템은 이전 시스템과 같이 'trackData' 존재하는 경우(센서가 사람 있다고 판단한 경우) fallDetection.step 통해 클러스터 정보 처리 및 자세를 추론하게 된다
    * 향후 개선된 클러스터링 통해 클러스터링 성능 개선이 이루어지면 'trackData' 없이 수행되도록 변경이 필요하다
* step은 (클러스터 존재여부 T/F, [xPos, yPos]) 형태의 리턴값 가지며, 단일 프레임(outputDict)에 대해 클러스터링 된 점들의 평균 값을 리턴하여 준다
    * 클러스터가 존재 시, 위 값을 바탕으로 updateClusterCache가 호출된다

### FallDetection의 step
* PeopleTracking에서 fallDetection.step(outputDict)로 호출된다
* 모델 path 및 다양한 parameter는 macroControl.py에서 변경 가능하다
* step의 구동 방식은 아래와 같다
1. outputDict의 key를 검사한다
    * 해당 프레임이 포인트 없는 빈 프레임인지 여부도 같이 검사한다다
2. outputDict들의 모음집인 seq_list를 모으게 된다
    * seq_list가 꽉 차지 않은 경우 append를 수행하며 해당 outputDict에 대한 single frame clustering 결과를 리턴한다
    * seq_list가 꽉 찬 경우, 오래된 요소 버리고 새로운 요소를 집어넣는다 (Queue)
3. seq_list를 기반으로 pandas DataFrame을 만들어 data에 저장한다
4. 만약 이미 돌아가고 있는 추론 스레드가 없다면 InferThread 통해 추론을 시작한다
    * 값 전달과 신호 연결을 위한 InferThread의 설정을 한다
    * 향후 semaphore와 같이 시스템 사양에 적합한 동시 구동 스레드를 제한하는 시스템으로 변경하는 것을 권장한다
5. InferThread가 start되어 run 메소드가 구동된다
6. cluster_data 사용하여 매 프레임 마다 클러스터가 존재하는지 확인한다
    * 해당 결과를 바탕으로 noise 유무를 판단하고 기록하는 noise_signal을 송신한다
        * FallDetection의 no_noise와 noise_update 참조
        * 시퀸스에 대해 MAX_SEQ_NOISE_LEN 이상의 연속 노이즈 오게 된다면 기존 시퀸스 데이터를 날려 버리게 된다
7. 클러스터 정보에 대해 글로벌 클러스터링을 수행하여, 각 프레임간의 클러스터의 연속성을 검사하고 이를 바탕으로 클러스터 번호를 업데이트한다
    * 연속된다고 판단되는 클러스터의 번호는 같은 번호로 하며, 각 클러스터의 번호는 고유하면서 오름차순으로 구성된다
    * outlier는 없애는 방식으로 구현하였으며, 다른 프로그램에서는 -1로 이상치(min_samples이하의 클러스터: noise)를 지정하였다
    * 실제 글로벌 클러스터의 구동은 Labeling Tool을 통해 확인하는 것을 추천한다
8. 글로벌 클러스터링 된 값을 run_model에 넘겨 추론 결과를 받는다
    * MODEL_SEQ_SIZE 이상의 시퀸스 길이를 가진 글로벌 클러스터에 대해서만 추론을 진행하며, MODEL_SEQ_SIZE 크기의 convolutional 연산 통해 생긴 여러 추론 값 중 최빈값을 상태 추론의 결과로 리턴한다
    * MODEL_SEQ_SIZE 이상의 시퀸스 길이 가진 클러스터에 대해 x, y 좌표값과 상태를 연결한 리스트를 시그널의 형태로 리턴하며, 이는 stateTransition을 호출하고 매개변수로 리턴값을 주게 된다
9. slot_signal을 방출하여 isSlotRunning을 False로 변경함으로서 다른 추론 스레드가 생성 가능하게 한다
10. 다시 step으로 돌아온 후, updateGraph에 클러스터 정보를 리턴한다
11. 클러스터 결과를 바탕으로 updateClusterCache가 호출된다

### Cluster Cache
* step의 리턴값에서 클러스터 존재할 시 updateClusterCache를 통해 cluster_cache를 업데이트하게 된다
* 캐싱된 데이터는 ticket이 0이 되면 사라지게 설계하였기에 매 프레임마다 호출되는 updateGraph에서 updateClusterTicket으 호출을 통해 ticket 값이 하나씩 줄어드는 형태로 갱신되게 된다
* updateClusterCache의 구동방식은 아래와 같다
1. cluster_cache에 기록된 각 좌표와 매개변수로 받은 클러스터의 거리를 계산한다
2. 만약 DISTANCE_THRESHOLD 이하의 인접 클러스터를 찾게 된다면, 가장 가까운 클러스터를 찾고, near_clust_flag를 True로 한다
3. near_clust_flag가 True인 경우 가장 가까운 클러스터의 정보를 업데이트한다
4. 만약 near_clust_flag가 False인 경우 새로운 cluster_cache 정보를 업데이트한다
5. 만약 cluster_cache 정보가 NUM_OF_DETECT_PEOPLE을 넘어설 경우 가장 ticket 작은 엔트리 찾아서 대체한다
* cluster_cache는 [xPos, yPos, ticket 수, STATE, cluster id, plotted xPos, plotted yPos, plotted zPos]의 리스트이며 NUM_OF_DETECT_PEOPLE만큼의 엔트리를 가진다

### stateTransition
* InferThread의 상태 추론 결과를 바탕으로 cluster cache의 state 값을 업데이트한다
* 업데이트를 할 클러스터를 찾는 과정에 클러스터 번호를 사용하는 것은 불가능하기에 minimum distance 계산하여 가장 가까운 클러스터에 정보를 업데이트 하는 방식으로 구현하였다
* 만약 MIN_PLOT_CNT 넘지 않아 plotting 되지 않은 클러스터의 경우 상태 정보 업데이트 하여도 무의미하기에 무시하는 방향으로 구현하였으나, 이는 프로토타입인 현재 Visualizer에서 가시적 성능 개선을 위한 것이기에 AI 모델 개선 후에는 변경해야하는 기능이다

### drawClust
* cluster_cache의 정보를 바탕으로 scatter 및 3D model로 GLViewWidget에 표현한다
* drawTrack는 기존 Visualizer, drawImage는 테스트용 기능이므로 무시하면 된다
* cluster_cache에 기록한 plotted 좌표와 업데이트된 좌표를 비교하여 MIN_DISTANCE_TO_MOVE 이상인 경우에만 plotting 위치를 변동하고 plotted 좌표도 업데이트한다
    * 이는 현재 클러스터링의 평균값 사용시 떨림 현상이 심한것을 억제하기 위한 구현 방식이다
    * 별도의 알고리즘 적용을 통해 자연스러운 움직임을 구현하는 것이 가능할 것이다
* 이후 내용은 별도의 그래픽 관련 문서 참조
