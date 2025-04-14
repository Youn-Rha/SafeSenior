### 수정한 클래스 및 함수

#### class updateQTTargetThread3D

people_tracking.py에서 객체를 UI에 표시할 때 사용하는 클래스로 매개변수로 par를 추가해 class PeopleTracking을 상속하도록 수정함.\
\
param par: class PeopleTracking을 상속한다.\
var self.man_plt: class PeopleTracking의 man_plt 변수를 저장\
var self.state: class PeopleTracking의 state 변수를 저장

#### def drawTrack

AI모델을 적용한 경우 UI가 정상 작동하지 않아서 UI가 표시되도록 임시로 수정한 함수\
\
var self.track: 원래는 people_tracking.py에서 class updateQTTargetThread3D를 호출할 때 매개변수로 gl.GLLinePlotItem()을 담은 변수를 넘기는데, 이것이 정상 작동하지 않아서 함수 내부에서 직접 만들어서 표시하도록 하는 변수이며 self.man_plt에 저장한다.
