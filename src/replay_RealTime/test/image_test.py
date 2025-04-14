import pyqtgraph as pg
from PySide2 import QtGui
from PySide2.QtCore import Qt
from PySide2.QtGui import QImage
from PySide2.QtWidgets import QApplication
import pyqtgraph.opengl as gl
import numpy as np

app = QApplication([])
view = gl.GLViewWidget()
view.show()

path = r"C:\Users\aa093\Documents\github\fall_detect\src\enhancedVisualizer\img\people_image_4.png"
image_data = QImage(path)
image_array = np.array(image_data.convertToFormat(QImage.Format_RGBA8888).bits()).copy().reshape(image_data.height(), image_data.width(), 4)
image_item = gl.GLImageItem(image_array)
image_item.translate(0, 0, 0)

view.addItem(image_item)
app.instance().exec_()