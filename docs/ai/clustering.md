# 클러스터링
1. DBSCAN을 통해 한 프레임 내의 pointNum들이 몇 번 클러스터에 속하는지 표시
    - calculate_dynamic_eps: 클러스터의 eps를 동적으로 변경
    - 클러스터링에는 Range, Azimuth, Elevation 특징만 사용, Doppler, SNR은 클러스터링에 필요가 없다고 판단했기 때문문
    - 군집 수를 정해주지 않기 위해서 K-means가 아닌 DBSCAN 사용

2. 헝가리안 알고리즘으로  데이터의 모든 프레임의 pointnum들에 글로벌 클러스터 값 할당.

    - 글로버 클러스터링 과정에서 너무 많은 데이터를 이상치로 판별하여 모델 정확도가 매우 떨어지는 모습이 보여짐