# csv 파일 전처리

visualizer로 생성되는 여러 csv 파일들을 전처리 하기위한 방법

1. csv파일의 모든 데이터들의 frameNum을 각 파일마다 1부터 시작해서 1씩 증가하게 만듬
    - 데이터 수집시에 frameNum이 이상하게 섞이거나 1부터 시작하지 않는 경우가 생겼기 때문
2. frameNum 기준으로 같은 클러스터의 pointNum들을 평균
    - 여러 pointNum을 하나의 객체로 압축하는 효과
    - 한 프레임에 하나의 객체가 있다면 하나의 Azimuth, Elevation, Range, Doppler, SNR값이 나옴옴   
3. 레이블을 원핫 인코딩함
    - fall: [1,0,0,0], sit: [0,1,0,0], sleep: [0,0,1,0], walk: [0,0,0,1]