# How to install Driver
1. 5-pin USB로 IWR6843ISK 장치를 PC와 연결
    * USB-A type, 케이블에 따라 정상적인 통신 되지 않는 경우 존재하기에 주의 필요
    * 초기 연결 시 terminal output에 b'' 무한정 표시되는 경우 다른 케이블로 시도할것
    * 위 경우, 연결 이후 센서에 깜빡임 없는 증상도 동반됨 (cfg 전송이 불가능한 상황)

2. 장치 관리자 열고 '기타 장치' 탭에서 Enhanced와 Standard 적힌 장치 확인
    * 기타 장치에 해당 이름 표시되지 않는 경우 또한 케이블 교체 필요

3. 장치 중 하나를 우클릭 후, '드라이버 업데이트' 클릭

4. '내 컴퓨터에서 드라이버 찾아보기' 후, 제공된 CP210x_Universal_Windows_Driver 폴더 선택

5. 하위 폴더 포함 체크박스 체크 후, 다음 버튼

6. 나머지 장치에 대해서도 3~5 과정 진행

7. 설치 완료 시, '포트(COM & LPT)'에서 2개의 포트 확인 가능

## Port Info
* Enhanced 포트 : 설정 전송용
* Standard 포트 : Data 전송용