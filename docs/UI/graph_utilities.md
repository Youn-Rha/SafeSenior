### 새로 개발한 함수

#### def rotate_vertices

꼭짓점들을 회전시키는 함수로 서 있는 자세에서 팔과 다리 각도를
조정하거나 앉은 자세, 누운 자세를 만드는 데 사용함.\
\
param vertices: 꼭짓점 배열 (N x 3 형태)\
param origin: 회전의 중심 (x, y, z)\
param angle: 회전 각도 (라디안 단위)\
param axis: 회전 축 ("x" or "y" or "z")\
return: 회전된 꼭짓점 배열

### 수정한 함수

#### def getBoxLinesCoords

원래는 박스의 좌표를 간단하게 구하는 함수이나, 사람 모양을
만들기 위해서 몸, 머리, 왼팔, 오른팔, 왼다리, 오른다리 이렇게 여섯 개의 파츠를
따로 만들어서 합쳐서 리턴하는 함수로 개조함.\
\
param x, y, z: 객체의 중심 좌표\
param track_prediction: AI 모델로 부터 받은 객체의 상태를 나타내는 변수로, 1인 경우 서 있는 상태, 2인 경우 누운 상태 및 낙상 상태, 3인 경우 앉은 상태이다.\
var center: 객체의 중심 좌표의 배열\
def getBoxVertices: 중심 기준으로 정반대에 있는 꼭짓점 두개를 매개 변수로 주면 8개의 꼭짓점을 반환해주는 함수\
def getBoxLinesFromVerts: 꼭짓점 8개를 매개변수로 주면 그 박스의 선들의 집합을 반환하는 함수\
var all_lines: 함수에서 만들어진 몸, 머리, 왼팔, 오른팔, 왼다리, 오른다리 파츠를 합친 변수
