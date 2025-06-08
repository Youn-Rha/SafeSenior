## 🧭 개요

`graph_utilities.py`는 mmWave 센서 데이터를 시각화하기 위한 유틸리티 함수들을 포함하는 모듈로, **3D plot 초기화**, **프레임별 데이터 시각화 갱신**, **클러스터별 색상 표시**, **텍스트 및 라벨 처리** 등 시각적 인터페이스를 구성하는 데 사용됩니다.

---

## 🧩 주요 기능별 함수 요약

### ✅ 시각화 초기화 및 설정
- `init_3d_plot(ax)`  
  → matplotlib 기반 3D 축 설정 및 초기 카메라 위치 지정  
- `set_plot_bounds(ax, xlim, ylim, zlim)`  
  → 시각화 영역 설정

### ✅ 실시간 갱신
- `update_point_cloud(ax, point_cloud)`  
  → 포인트 클라우드를 갱신하여 새로운 프레임을 표시  
- `update_clusters(ax, clustered_data)`  
  → 클러스터 별 색상으로 시각화

### ✅ 색상 처리
- `get_cluster_color(cluster_id)`  
  → 클러스터 ID별 고정 색상 매핑  
- `generate_color_map(num_clusters)`  
  → 전체 클러스터 수에 따라 색상 리스트 생성

### ✅ 라벨링 및 텍스트
- `annotate_cluster_centroids(ax, centroids)`  
  → 클러스터 중심 좌표에 ID 라벨 표시  
- `clear_annotations(ax)`  
  → 기존 텍스트 제거

### ✅ 보조 유틸
- `normalize_coordinates(data)`  
  → plot 좌표계 기준으로 값 정규화  
- `convert_cartesian_to_spherical(x, y, z)`  
  → 좌표계 변환 지원 함수

---

## 🔄 연동 예시

```python
from graph_utilities import init_3d_plot, update_point_cloud

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
init_3d_plot(ax)

while True:
    point_cloud = get_next_frame()
    update_point_cloud(ax, point_cloud)
    plt.draw()
```

---

## 📝 참고 문서

- [`plot_3d.py`](plot_3d.md): 이 유틸리티를 사용하는 실제 시각화 모듈
- [`gui_threads.md`](gui_threads.md): 프레임 단위로 시각화 갱신 호출
- [`core.md`](core.md): 전체 시스템 흐름 중 시각화 트리거 발생 위치
