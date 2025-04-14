# Replay - Programming Guidance
<img src="../../img/replay.gif">

* dataCollect를 통해 얻은 csv 파일로 부터 cloud point 정보를 시각화하여 확인하는 프로그램
* 읽을 csv 파일과 cfg 파일을 선택하면 자동적으로 첫 프레임 정보가 표출된다
* ini 파일을 통해서 실행과 동시에 이전에 사용한 파일 정보를 읽은 채로 시작이 가능하다
* 버튼, 숫자 입력, 스크롤, 단축키를 사용한 다양한 탐색 방법을 제공한다
* 재생 기능과 속도 제어 기능을 통해 영상 재생하듯 cloud point를 확인할 수 가 있다

## 파일 구분
### core.py
* 편의성 위해 Window 클래스 하나로 모든 기능을 정의함
* 사용하는 색은 생성자의 colors_rgba에서 편집 가능, 색 추가에도 동적으로 작동하도록 설계됨
* 동영상 재생 기능을 위한 QTimer인 frameTimer가 존재
* 단축키 (화살표, Home, End, Ctrl+Q) 정의하였으나, focus에 따라 적용되지 않는 경우 종종 보인다
* 읽을 cfg는 3D People Tracking Demo만 고려한 형태로 제작됨
* 다양한 행동으로 인한 프레임의 변화는 updateFrame 메서드를 통해 화면에 결과를 반영하게 된다
    * signal에 의한 메서드 호출 시, 조건 검사 후 currentFrame을 먼저 지정해주고 updateFrame 호출하는 방식으로 진행

### global_macro.py
* path 설정 및 상수값 정의

### graph_utilities.py
* scatter 사용을 위해 Visualizer와 동일한 Circle3D 클래스를 정의

### plot_3d.py
* boundaryBox 관련 세부사항 제외하고는 Visualizer와 동일한 코드

## 기능별 설명
### frame 관련사항
* currentFrame은 1부터 시작하며, csv 파일 불러오지 못한 초기 상태에는 0으로 설정된다
* 초기 0 세팅을 통해 ini로 csv 불러오지 못한 경우 scatter에서 나는 오류를 방지한다
* currentFrame은 실제 csv의 frameNum이 아닌 순서를 세기 위한 연속적인 값을 가진다
* csv 파일의 실제 frameNum은 realFrameNum으로 표현되며, self.csvMetaData[self.currentFrame - 1][CSV_META.FRAME_NUM]로 참조한다
* 마찬가지로 한 프레임의 point 수는 self.csvMetaData[self.currentFrame - 1][CSV_META.POINT_CNT]로 참조한다

### frameTimer
* startPlay에서 최초 호출된다
* timeout시 displayFrameTimer가 호출
* 최대 프레임까지 프레임 계속 증가, 최대 프레임 도달 시 stopPlay
* isPlaying 검사를 통해 타이머 지속 여부를 결정한다

### csv 읽고 저장
* 각 포인트를 딕셔너리 형태로 하여 이를 리스트화 한 outputList에 저장
* 각 포인트의 실제 frameNum과 해당 프레임의 총 point 수는 csvMetaData에 저장
* csv 파일의 각 줄을 읽으며 frameNum의 변동 발견 시 기록하는 방식
* required_col의 존재 여부를 검사한다
    * 기존 dataCollect의 pointCloud가 아닌 다른 형식의 csv 지원하기 위해서는 해당 부분의 편집이 필수적이다

### 화면 업데이트 : updateFrame
* csvMetaData 통해 변수 값을 업데이트 하고, 좌측 레이블 값을 변경한다
* displayPointCloud 통해 scatter 출력한다
* 슬라이더 변경 통한 updateFrame의 중복 작동을 방지하기 위해서 blockSignals를 사용하여 setValue 호출한다

### displayPointCloud
* 음수값 전달 시 return한다
    * Window 생성자에서 plot시 오류 나는 문제 해결 위한 구조
    * main에서 show이후에 pointCloud 출력하되, 유효하지 않은 csv인 경우 출력을 포기하기 위함
* 읽은 파일의 global clustering 여부에 따라 coloring 방식이 다르다
* 3D plot의 scatter 사용한다