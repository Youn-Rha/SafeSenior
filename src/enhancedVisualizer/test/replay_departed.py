import sys
import pandas as pd
from PySide2.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSlider, QWidget, QLineEdit, QPushButton, QHBoxLayout, QInputDialog, QFileDialog
from PySide2.QtCore import Qt, QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)

# x,y,z,global_cluster,frameNum 포함된 데이터
data = pd.read_csv("./data/data_with_xyz (1).csv")
class SliderVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('XYZ Frame Visualizer')
        self.setGeometry(100, 100, 800, 600)

        self.current_frame = 1
        self.total_frames = len(data["frameNum"].unique())
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.is_playing = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.play_frames)

        layout = QVBoxLayout(self.main_widget)

        # Matplotlib Canvas
        self.canvas = FigureCanvas(plt.figure())
        layout.addWidget(NavigationToolbar(self.canvas, self))
        layout.addWidget(self.canvas)

        # 슬라이더
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(self.total_frames - 1)
        self.slider.setValue(1)
        self.slider.valueChanged.connect(self.update_frame)
        layout.addWidget(self.slider)

        # Save Data Button
        self.save_data_button = QPushButton('Save Data to CSV')
        self.save_data_button.clicked.connect(self.save_data_to_csv)
        layout.addWidget(self.save_data_button)

        self.plot_frame(self.current_frame)
        # 프레임 검색 부분
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Enter frame number')
        self.search_button = QPushButton('Go')
        self.search_button.clicked.connect(self.search_frame)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # 클러스터 변경 부분
        self.update_cluster_button = QPushButton('Update Cluster Label')
        self.update_cluster_button.clicked.connect(self.update_cluster_label)
        layout.addWidget(self.update_cluster_button)

        # Play and Stop Buttons
        playback_layout = QHBoxLayout()
        self.play_button = QPushButton('Play')
        self.play_button.clicked.connect(self.start_playback)
        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_playback)
        playback_layout.addWidget(self.play_button)
        playback_layout.addWidget(self.stop_button)
        layout.addLayout(playback_layout)

        self.plot_frame(self.current_frame)

    #한 프레임 plot하는 함수
    def plot_frame(self, frame_index):
        self.canvas.figure.clear()
        fig = plt.figure(figsize=(8, 8))
        ax = self.canvas.figure.add_subplot(111, projection='3d')
        data_for_frame = data[data['frameNum'] == frame_index]
        df_scale = data_for_frame[["x", "y", "z", "global_cluster"]]
        scatter = ax.scatter(
            df_scale['x'],
            df_scale['y'],
            df_scale['z'],
            c=df_scale['global_cluster'],
            cmap='viridis',
            marker='o',
            s=50)

        legend = ax.legend(*scatter.legend_elements(), title="Clusters")
        ax.add_artist(legend)
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')
        ax.set_title(f'Frame {frame_index}')
        self.canvas.draw()


    #슬라이더로 value가 변할 때 프레임을 업데이트하는 함수
    def update_frame(self, value):
        self.current_frame = value
        self.plot_frame(self.current_frame)

    #프레임 직접 검색 기능
    def search_frame(self):
        try:
            frame_number = int(self.search_input.text())
            if 0 <= frame_number < self.total_frames:
                self.slider.setValue(frame_number)
                self.update_frame(frame_number)
            else:
                print('Frame number out of range')
        except ValueError:
            print('Invalid frame number')

    #old_label 번호의 클러스터를 new_label 번호의 클러스터로 변경, 모든 프레임에 대해서 일어남
    def update_cluster_label(self):
        old_label, ok = QInputDialog.getInt(self, 'Update Cluster', 'Enter current cluster label:')
        if ok:
            new_label, ok = QInputDialog.getInt(self, 'Update Cluster', 'Enter new cluster label:')
            if ok:
                data.loc[data["global_cluster"] == old_label, "global_cluster"] = new_label
                self.plot_frame(self.current_frame)

    def start_playback(self):
        if not self.is_playing:
            self.is_playing = True
            self.timer.start(100)  # 500 ms per frame

    def stop_playback(self):
        self.is_playing = False
        self.timer.stop()
    def play_frames(self):
        if self.current_frame < self.total_frames - 1:
            self.current_frame += 1
        else:
            self.current_frame = 0
        self.slider.setValue(self.current_frame)
        self.update_frame(self.current_frame)

    def save_data_to_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save Data', '', 'CSV Files (*.csv)')
        if file_path:
            data.to_csv(file_path)
            print(f'Data saved to {file_path}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = SliderVisualizer()
    main_window.show()
    sys.exit(app.exec_())
