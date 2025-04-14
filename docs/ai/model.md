# 모델 구조
- GRU 사용

- 은닉층: 32 * 64, 각 층 뒤에 드랍아웃 0,2, 0,3 적용용

- input_shape: (5,5)
-- Range, Azimuth, Elevation, Doppler, SNR 값을 가진 데이터를 5개 붙인 시계열 데이터, stride = 2, window size = 5

- output_shape: (4) -- fall, sit, sleep, walk 각각일 확률, softmax, 원핫 인코딩 

- train, test 75:25 분할

- 손실 함수: categorical_crossentropy
- optimizer: 학습률 0.001의 Adam
- 평가 지표: accuracy 

