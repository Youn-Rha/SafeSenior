# AI 파이프라인 구조
1. CSV 데이터 전처리
2. 모델 학습 및 성능 평가
3. 적용

# [전처리](./preprocessing.md) 및 [클러스터링](./clustering.md)
* 여러 파일에 나눠져 있는 csv 데이터를 하나의 DataFrame 변수에 저장
* 한 Frame에 있는 여러 Point들을 클러스터링
* 각 클러스터의 특징들을 평균해서 하나의 데이터로 만듬

# [모델 학습](./model.md)
* 전처리한 데이터를 시계열 데이터로 변환 후 모델(GRU) 학습

# [성능 평가](./metrics.md)
- 데이터를 약 7:3 분할하여 accuracy, f1_score 등의 평가 지표로 평가

# 코드
1. ai_code_prototype
    - colab에서 작성된 ai코드 프로토타입
2. sensor_connected_model
    - 센서와 UI 파트와 연결시키는 ai 코드
3. final_model
    - 완성된 모델 파라미터

# 논문 리뷰 및 제안사항
### [PeopleTracking 논문 리뷰](./Application%20of%20mmWave%20Rador%20Sensor%20for%20People%20Identification%20and%20Classifition%20논문%20리뷰.pdf)
### [DBSCAN 논문 리뷰](./DBSCAN%20논문%20리뷰.pdf)
### [AI 관련 개선점 제안사항](./개선점%20생각.pdf)