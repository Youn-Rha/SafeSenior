### 새로 개발한 함수

#### def update_fall_status

낙상 감지 여부를 낙상 감지 패널에 표시하는 함수로, 최대 5명까지 표시할 수 있으며, 낙상이 감지된 경우 빨간색으로 아닌 경우 초록색으로 표시하며 일정 시간 후 꺼지도록 한다.\
\
var panel: def initFallDetectPane에서 생성한 fall_panels를 저장하는 변수

### 수정한 함수

#### def updateGraph

매 프레임마다 사람을 감지하여 그래프를 업데이트하는 함수로, 낙상감지와 관련된 코드를 수정했으며, updateQTTargetThread3D를 호출하는 부분을 수정함.\
\
var fallDetectionDisplayResults: self.fallDetection.step(outputDict)를 통해 낙상 관련 정보를 받아와서 저장하는 변수로 [0]은 targetID, [1]은 state를 나타낸다.\
self.plot_3d_thread: updateQTTargetThread3D를 호출할 때 첫 번째 매개변수로 self를 넘겨줘서 class PeopleTracking을 상속할 수 있도록 한다.

#### def initFallDetectPane

낙상 감지 패널을 생성하는 함수로, 왼쪽 패널은 라벨, 오른쪽 패널은 낙상 감지 여부를 표시한다.\
\
var self.left_panel: 왼쪽 패널 전체를 저장하는 위젯\
var self.right_panel: 오른쪽 패널 전체를 저장하는 위젯\
var self.fall_panels: def update_fall_status에서 패널을 업데이트할 수 있게 하는 변수\
var horizontal_layout: 왼쪽 패널과 오른쪽 패널을 수평으로 묶는 변수

#### def fallDetDisplayChanged

낙상 감지를 체크한 경우 낙상 감지 패널들이 보이도록 하는 함수
