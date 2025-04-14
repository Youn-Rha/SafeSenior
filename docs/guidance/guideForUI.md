# guideForUI

* enhancedVisualizer, replay, labelingTool 프로그램들에 대한 UI 설명을 담은 문서

# enhancedVisualizer

## 관련 실험

### sphere_test.py

* 3D plotting으로 나타내는 사람의 머리 부분을 구로 교체하기 위해 진행한 실험
* 처음에는 구를 직접 만들려고 했지만, 구처럼 보이게 하기 위해 더 많은 점을 사용할수록
리소스를 너무 많이 사용하기에 폐기
* 빌보드 효과를 이용하여 원을 이용하는 방향으로 수정 후 본 코드에 머리 형태를 구와 박스 중
선택할 수 있도록 반영

### image_test.py

* 3D plotting을 2D 이미지로 교체 가능한지 파악하기 위해 진행한 실험
* 이미지를 GLViewWidget에 불러오는 것은 가능하다는 것을 증명
* 하지만 실제 Visualizer에 접목 시 Thread내부에서 이미지를 불러오는 경우 오류가 발생하는데
해결이 어려울 것으로 보여 실제 사용은 포기 (해당 코드는 gui_threads.py파일에 def drawTrackImage 참조)

## 관련 코드

### core.py

#### self.gl_view = Plot3D() !!!매우 중요

* Plot3D는 from plot_3d import Plot3D(즉 plot_3d.py 파일로부터 class Plot3D를 import)를 통해 plot_3d.py 파일로부터 가져와서 쓰는 클래스
* Visualizer의 오른쪽 부분인 3D plotting 부분 전체를 담당하는 클래스로 self.gl_view.plot_3d는 gl.GLViewWidget을 나타내며 해당 위젯에 opengl 그래픽을 추가하는 것으로 3D plotting을 화면에 나타냄
* 해당 파일은 구조는 쉽지만 수정하거나 제거하기 난해하여 plot_3d.py 파일은 거의 수정한 부분이 없으며 gui_threads.py 파일의 경우 self.gl_view를 상속하여 self.gl_view.plot_3d에 객체를 추가하고 삭제할 수 있도록 하였으며 구조를 바꾸지 않는 이상 계속 이렇게 사용 권장

### gui_threads.py

* 기존 Visualizer의 gui_threads.py파일과 people_tracking.py파일을 필요한 함수만 뽑아서 합친 파일
* 파일을 합치는 과정에서 def update_fall_status 함수의 위치를 Thread 내부로 변경하였는데, 원래는
QTimer를 이용해 패널의 색상을 변경하였으나 Thread 내부에서는 QTimer가 정상 작동하지 않는 것으로 판단
티켓을 이용하여 타이머를 대체

#### def parseTrackingCfg

* ellipsoids관련 코드만 사용하기에 다른 코드는 모두 폐기
* head type을 원으로 사용하는 경우 사람 한 명당 ellipsoids가 2개 필요하기 때문에 탐지 가능 인원 * 2
만큼 ellipsoids를 채움

### graph_utilities.py

* gui_threads.py파일에서 3D plotting을 하는 데 사용하는 모든 그래프 관련 함수를 모은 파일

#### class Circle3D & class CircleBillboard3D

* 사람 얼굴을 박스에서 원으로 나타내기 위해 생성한 클래스들
* 사람 얼굴을 구로 나타내면 프로그램의 부하가 너무 커져서 Billboardeffect를 이용하여 카메라 시점을 항상 정면으로 보는 원으로 나타냄
* 입력으로 x, y, z(+ radius)를 받으며, Circle3D가 원을 생성하고 CircleBillboard3D는 def update_orientation을 통해 원의 방향을 카메라 시점으로 계속 보정해주는 역할을 함함
* def update_orientation은 gui_threads.py 파일의 def drawClust 함수에서 사람 모양을 나타낼때마다 호출되어 시점을 보정함

#### def rotate_vertices

* 꼭짓점의 넘파이 배열을 특정 원점을 기준으로 특정 axis로 angle만큼 회전시키는 함수
* 현재는 앉은 자세와 누운 자세를 만드는 데 사용 중
* 후에 걷는 모션을 만들 때 활용할 수 있을 것으로 예상

#### def getBoxLinesCoordsBoxHead

* 3D plotting을 할 때 사용하는 점들을 모두 모아 배열로 return하는 함수
* track_prediction이 state 즉 상태를 나타내며, 0은 낙상, 1은 서 있는 상태, 2는 누운 상태,
3은 앉은 상태를 나타냄
* rotate_vertices 함수를 이용하여 앉은 자세와 누운 자세를 생성하며, 현재 낙상은 누운 자세와
똑같은 형태를 return
* 누운 자세의 경우 서 있는 자세를 만든 후 x축으로 90도 회전하여 생성
* 앉은 자세의 경우 서 있는 자세에서 하체를 x축으로 90도 회전하여 생성
* 파라미터를 조정하여 사람의 크기, 회전의 정도, 회전축을 변경 가능

#### def getBoxLinesCoordsCircleHead

* 위 getBoxLinesCoordsBoxHead와 코드가 거의 같으나 이 함수는 head type이 원일 때 사용하는 함수로
머리를 제외한 모든 점들을 모아 배열로 return하는 함수

# replay_RealTime

* replay프로그램을 만들기 전에 시험용으로 replay를 실시간 Visualizer에 적용해 본 프로그램
* 기본적으로 replay 기능을 제외한 UI는 Visualizer와 동일

## 관련 실험

### replay_test.py

* replay프로그램을 만들기 위해 실험을 진행하며 core.py에 작성한 코드들을 옮긴 파일

## 관련 코드

### core.py

#### def initReplayBox

* replay 관련 UI layout을 저장한 후 불러오는 함수
* QGroupBox안에 QSlider와 QPushButton들을 위치에 맞게 배정
* Button들은 clicked.connect()를 이용하여 알맞은 함수와 연결

#### def frameControl

* 센서가 작동을 시작했을 때 호출되는 함수로 33ms마다 타임아웃을 통해 capture_frame_image 함수를 호출하도록 하는 함수

#### def toggleReplay

* 재생/일시정지 버튼을 눌렀을 때 호출되는 함수로 replayBtn과 연결되어 있음

#### def capture_frame_image

* 현재 화면을 이미지로 저장하여 리스트에 저장하는 함수
* 타이머에 의해서 33ms마다 호출되는 함수로, 초당 30프레임을 캡쳐

#### def restore_leftframe & def restore_rightframe

* 왼쪽/오른쪽 화살표를 누른 경우 호출되는 함수로, 전/후 프레임을 불러오는 역할
* frame_index를 변경하여 restore_image함수를 호출

#### def restore_image

* 리스트에 저장한 이미지를 불러와서 QLabel을 이용해 화면에 덮어씌우는 함수
* QLabel은 show()로 작동하며 다음 라벨을 덮어씌우기 전에 hide()로 숨김

#### def restore_widget_btb

* 원하는 프레임으로 이동하기 위해 입력창에 프레임 넘버를 적고 버튼을 누른 경우 호출되는 함수
* 입력받은 값으로 frame_index를 변경하여 restore_image함수를 호출

# replay

* csv를 리플레이하여 눈으로 볼 수 있게 만든 프로그램
* 기본적으로 UI는 replay_RealTime의 UI를 참조하여 변형

## 관련 실험

### color_test.py

* replay 프로그램에서 점을 찍는데 사용할 색깔을 지정하기 위한 실험
* PySide2는 rgba 포멧을 사용하며 QColor로 바꿔서 사용
* 해당 실험으로부터 선정한 색깔들을 colors_update.png에 저장

## 관련 코드

### core.py

* 프로그램의 대부분의 기능을 포함하고 있는 파일

#### def displayPointCloud

* 읽은 csv 파일을 토대로 frameNum을 받아 해당 프레임에 있는 모든 점을 찍는 함수
* csv에 global_cluster 열이 있는 경우 global_cluster 번호가 똑같은 점끼리는 같은 색으로, 열이 없는 경우 SNR값에 따라 색깔을 다르게 함
* 해당 global_cluster 번호에 맞는 색깔을 colors_qcolor로 부터 가져옴
* toPlot, pointColors, size는 setData함수에 인수로 사용하기 위해 np.array를 이용하여 넘파이 배열로 변경

# highlight_test

* labeling tool에 클러스터 번호에 따라 하이라이트하는 기능을 만들기 위해 만든 실험용 프로그램

## 관련 코드

### core.py

* 프로그램 구조는 replay 프로그램과 동일

#### def displayPointCloudWithCircles

* 기존에 displayPointCloud 함수에 원을 이용하여 하이라이트 하는 기능을 추가한 함수
* 기존에 enhancedVisualizer에서 3D plotting을 하는데 사용한 ellipsoids를 활용하여 하이라이트 기능을 구현
* 원 세개를 이용해 하이라이트를 수행하며, create_circle 함수를 호출하여 원을 만듦

#### def makeEllipsoids

* ellipsoids를 사용하기 위해 GLLinePlotItem을 만들어 ellipsoids에 저장하는 함수
* 프로그램이 시작할 때 자동으로 호출됨

#### def create_circle

* 원 3개를 따로 만들어 한 ellipsoids에 저장하여 3D plotting 하는 함수
* x, y, z 좌표를 이용하여 원 3개를 각각 xy, xz, yz 평면에 평행하게 생성하여 concatenate를 통해 하나의 넘파이 배열로 만든 후 클러스터 색상과 동일한 색상을 적용하여 원을 plotting
* 색상은 원의 경우 standardize(표준화) 해야 하므로 각각의 rgb 값을 255로 나눠줘야 함

# labelingTool

* UI 구조는 replay + highlight_test와 크게 다르지 않음

## 관련 코드

### core.py

#### def initClustCtrlBox

* 클러스터 번호를 바꾸는 데 사용하는 UI를 모아둔 함수
* 프로그램이 시작할 때 자동으로 호출됨
* 클러스터 패널들은 클러스터 번호에 맞는 색상으로 표시되며 클릭할 시 colorBtnClicked 함수를 호출

#### def displayGraphics

* 기존 replay 프로그램의 displayPointCloud 함수를 개조한 함수로 checkCurFrame 함수와 displayGraphics 함수로 기능 분할

#### def highlightCluster

* colorBtnClicked 함수에서 호출하는 함수로 클러스터를 하이라이트 하는 기능을 수행
* highlight_test의 create_circle 함수에서 프로그램에 맞게 수정한 함수로, 기능적인 부분은 동일
* create_circle 에서는 원 3개를 하나의 리스트에 합쳐서 plotting 했으나 highlightCluster 함수에서는 각각의 원을 따로 plotting 하므로 ellipsoids를 세개 사용