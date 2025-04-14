# # 구 테스트
import sys
import numpy as np
from PySide2.QtCore import Qt, QTimer
from PySide2.QtGui import QVector3D
from PySide2.QtWidgets import QApplication, QMainWindow
import pyqtgraph.opengl as gl
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QTimer

# # 3D 구 생성 함수 (중심 좌표를 전달받음)
# def create_sphere(radius, num_points=300, center=(0, 0, 0)):
#     theta = np.linspace(0, np.pi, num_points)  # 위도 (0에서 π까지)
#     phi = np.linspace(0, 2 * np.pi, num_points)  # 경도 (0에서 2π까지)

#     # 구의 좌표 계산
#     x = radius * np.outer(np.sin(theta), np.cos(phi))
#     y = radius * np.outer(np.sin(theta), np.sin(phi))
#     z = radius * np.outer(np.cos(theta), np.ones_like(phi))

#     # 중심 좌표를 더해 구의 위치를 이동
#     x += center[0]
#     y += center[1]
#     z += center[2]

#     return x, y, z

# # 3D 좌표를 받아서 GLLinePlotItem으로 구를 그리는 함수
# def plot_sphere(x, y, z):
#     # 좌표들을 3D 배열로 결합
#     points = np.vstack([x.flatten(), y.flatten(), z.flatten()]).T
    
#     # GLViewWidget 및 GLLinePlotItem 설정
#     view = GLViewWidget()
#     view.show()
    
#     # GLLinePlotItem을 사용해 3D 구 그리기
#     line_item = GLLinePlotItem(pos=points, color=(1, 1, 1, 1), width=1)
#     view.addItem(line_item)

#     return view

# # 애플리케이션 실행
# app = QApplication(sys.argv)

# # 구의 중심과 좌표 생성 (임의의 중심)
# center = (2.0, 3.0, 4.0)  # 구의 중심 (x, y, z)
# x, y, z = create_sphere(1.0, center=center)  # 반지름 1의 구를 생성

# # 전달받은 x, y, z 좌표로 구 그리기
# plot_sphere(x, y, z)

# # 메인 이벤트 루프 실행
# sys.exit(app.exec_())

# # 원 테스트

# # 3D 원 생성 함수
# def create_circle(radius, num_points=100, center=(0, 0, 0), plane='xy'):
#     theta = np.linspace(0, 2 * np.pi, num_points)  # 0에서 2π까지
    
#     if plane == 'xy':
#         # xy 평면에서 원
#         x = radius * np.cos(theta) + center[0]
#         y = radius * np.sin(theta) + center[1]
#         z = np.zeros_like(theta) + center[2]
#     elif plane == 'yz':
#         # yz 평면에서 원
#         x = np.zeros_like(theta) + center[0]
#         y = radius * np.cos(theta) + center[1]
#         z = radius * np.sin(theta) + center[2]
#     elif plane == 'xz':
#         # xz 평면에서 원
#         x = radius * np.cos(theta) + center[0]
#         y = np.zeros_like(theta) + center[1]
#         z = radius * np.sin(theta) + center[2]
    
#     return x, y, z

# # 3D 좌표를 받아서 GLLinePlotItem으로 원 그리기
# def plot_circle(x, y, z):
#     # 좌표들을 3D 배열로 결합
#     points = np.vstack([x.flatten(), y.flatten(), z.flatten()]).T
    
#     # GLViewWidget 및 GLLinePlotItem 설정
#     view = GLViewWidget()
#     view.show()
    
#     # GLLinePlotItem을 사용해 3D 원 그리기
#     line_item = GLLinePlotItem(pos=points, color=(1, 1, 1, 1), width=2)
#     view.addItem(line_item)

#     return view


class Circle3D:
    def __init__(self, radius=1.0, segments=100):
        self.radius = radius
        self.segments = segments
        self.circle_mesh = self._create_circle()

    def _create_circle(self):
        # Create points for a 2D circle in the X-Y plane
        theta = np.linspace(0, 2 * np.pi, self.segments)
        x = self.radius * np.cos(theta)
        y = self.radius * np.sin(theta)
        z = np.zeros_like(x)  # Flat on the X-Y plane
        points = np.column_stack((x, y, z))
        return points

    def get_circle_mesh(self):
        return self.circle_mesh

class CircleBillboard3D:
    def __init__(self, radius=1.0):
        self.circle = Circle3D(radius)
        self.view = None

    def add_to_view(self, view):
        self.view = view
        # Create a Line plot to represent the circle
        self.plot_item = gl.GLLinePlotItem(pos=self.circle.get_circle_mesh(), color=(1, 0, 0, 1), width=2, mode='line_strip')
        self.view.addItem(self.plot_item)

    def update_orientation(self):
        if self.view is None:
            return

        # Access camera position and target
        camera_position = self.to_numpy_vector(self.view.cameraPosition())
        camera_target = self.to_numpy_vector(self.view.opts['center'])  # Point the camera is looking at

        # Compute the view direction
        view_direction = camera_target - camera_position
        view_direction /= np.linalg.norm(view_direction)  # Normalize the direction

        # Define a default "up" vector
        up_vector = np.array([0, 0, 1])  # Assuming Z-axis as "up"

        # Compute the right vector (perpendicular to view direction and up vector)
        right_vector = np.cross(up_vector, view_direction)
        right_vector /= np.linalg.norm(right_vector)  # Normalize the vector

        # Recompute the corrected "up" vector
        corrected_up = np.cross(view_direction, right_vector)

        # Create a rotation matrix (view alignment)
        rotation_matrix = np.column_stack((right_vector, corrected_up, view_direction))

        # Apply the rotation to the circle's mesh points
        circle_points = self.circle.get_circle_mesh()  # Original circle points
        transformed_circle = circle_points @ rotation_matrix.T  # Transform the points
        self.plot_item.setData(pos=transformed_circle)


    # Convert PySide2 QVector3D objects to NumPy arrays
    def to_numpy_vector(self, vec):
        return np.array([vec.x(), vec.y(), vec.z()])

        


# PySide2 Application setup
app = QApplication([])

# PyQtGraph OpenGL view
view = gl.GLViewWidget()
view.show()

# Add grid for reference
grid = gl.GLGridItem()
grid.setSize(x=10, y=10, z=0)
grid.setSpacing(x=1, y=1, z=1)
view.addItem(grid)

# Add a billboard circle to the 3D view
circle = CircleBillboard3D(radius=2)
circle.add_to_view(view)

# Timer to update the circle's orientation based on camera movement
timer = QTimer()
timer.timeout.connect(circle.update_orientation)
timer.start(30)

app.exec_()
