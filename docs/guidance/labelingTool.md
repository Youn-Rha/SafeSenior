# labelingTool
<img src="../../img/labeling tool.gif">

* replay tool을 기반으로 하여 클러스터 조작 기능을 추가
* DBSCAN 기반 사전 클러스터링이 된 파일을 읽는 것을 목표로 제작
    * 다른 형태의 csv 파일 읽기 위해서는 코드 수정이 필요
* 각 클러스터에 할당된 색 표시에 맞게 좌하단 버튼에도 클러스터에 대응하는 색칠된 버튼이 존재
* 해당 버튼을 누르면 클러스터 활성화되어 3D scatter 위에 구형 표시로 하이라이트
* 선택된 클러스터에 대하여 클러스터 합치기 기능과 클러스터 변경 기능이 존재
* 클러스터 변경의 경우 연속된 프레임에 대해 모두 적용하거나, 한 프레임에 대해서만 적용하는 두 가지 선택지가 존재
* 클러스터 합치기의 경우 연속된 프레임에 대해 모두 적용됨
* 클러스터의 변경 사항은 save를 통해 파일에 덮어쓰기 형식으로 저장된다
* recover 버튼의 경우 마지막에 저장된 상황을 불러오게 된다

## 파일 구분
* replay와 동일한 구성, 추가 기능은 core.py에 기술

## 기능별 flow 설명
* 기존 replay와 동일한 구성에 기능을 추가한 형태
* 레이아웃의 경우 iniClusterCtrlBox로 추가된 클러스터 제어 레이아웃을 정의

### 저장 기능의 변경
* 기존의 outputList를 대신하여 originalDictList와 revisedDictList로 저장
* recover를 위하여 originalDictList는 저장된 파일을 기준으로 저장
* revisedDictList는 유저가 편집한 내용을 즉각적으로 반영
* save 버튼을 누르게 되면 originalDictList으 내용은 revisedDictList로 덮어쓰며, csv 파일 또한 revisedDictList로 덮어쓰게 된다
* 복사는 deep copy로 두 리스트가 분리하여 관리되도록 구성함

### 클러스터 선택
* curFrameCluster에 set으로 현재 프레임의 클러스터 정보를 저장
* selectedCluster에 set으로 선택된 클러스터 정보를 저장
* 선택되어 하이라이트 된 클러스터는 highlightCluster를 통해 구형 모델을 출력하게 된다
    * 3개의 원 ellipsoid를 추가하는 형태

### mergeCluster
1. 선택된 클러스터가 2개 이상인지 검사
2. 2 개 이상의 클러스터가 선택 시, 선택된 클러스터 중 iteration 하여 처음 나오는 인덱스 선택
3. 해당 인덱스로 merge 하게 되는 다른 클러스터를 idx_to_conv에 저장
4. revisedDictList를 merge 하여 편집
5. updateFrame

### changeCluster
1. 선택된 클러스터가 1개 이상인지 검사
2. 선택된 클러스터의 인덱스를 idx_to_conv에 저장
3. IndexSetDialog 창을 띄워 할당할 인덱스(target_idx)와, 다른 프레임에 대한 저장 여부(cur_flag)를 조사
4. 만약 새 창에서 입력이 정상 수행 되지 않을 시 return
5. revisedDictList 값 편집 수행
6. updateFrame

### 클러스터 선택 버튼의 구현
 * reloadColorBtn에서 현재 프레임에 대응하는 클러스터와 그 색에 따라 버튼을 할당하고 스타일링하는 것을 수행한다
 * 버튼의 경우 color_cnt에 대응하는 양으로 생성하되, 표시된 클러스터에 매칭되는 수의 버튼만 빠른 idx부터 사용한다
 * 색의 경우 프레임 변경에 따라 각 버튼의 스타일시트 변경하는 형식으로 사용한다
 * 만약 color_cnt를 초과하는 색 나올 경우 순환식으로 색 재사용하는 점에 주의가 필요하다
    * 필요에 따라 색을 추가하거나 변경하는 것이 가능하다 : Window 생성자의 colors_rgba를 편집하면 된다
* 버튼의 컬러링 방식을 변경하기 위해서는 getBtnColorStyleSheet를 변경하면 된다