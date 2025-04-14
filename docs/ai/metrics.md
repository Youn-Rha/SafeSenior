# 모델 평가 내용

* 평가 지표(클러스터링 제외한 경우, 한 프레임에 한 사람만 잡힌다고 가정)

- GRU

| | |
| --- | --- |
| accuracy | 0.8957 |
| f1_score | 0.8731274371734583 |
| precision_score | 0.8857854560064283 |
| recall_score | 0.8663603754233029 |

- Light Gradient Boosting Machine

| | |
| --- | --- |
| accuracy | 0.9406	 |
| f1_score | 0.9402 |
| precision_score | 0.9432 |
| recall_score | 0.9406 |

- Extra Tress Classifier

| | |
| --- | --- |
| accuracy | 0.9464	 |
| f1_score | 0.9453 |
| precision_score | 0.9488 |
| recall_score | 0.9464 |

- 타 모델의 더 좋은 성능에도 GRU를 사용, 시계열 데이터의 특성을 해치지 않기 위함

- 클러스터링 후 성능 매우 저하됨, 개선 필요요