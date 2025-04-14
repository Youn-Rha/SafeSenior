import pyqtgraph as pg
from PySide2 import QtGui
from PySide2.QtCore import Qt
from PySide2.QtGui import QImage
from PySide2.QtWidgets import QApplication
import pyqtgraph.opengl as gl
import numpy as np
from PIL import Image

app = QApplication([])
view = gl.GLViewWidget()
view.show()

path = r"C:\Users\aa093\Documents\github\fall_detect\src\enhancedVisualizer\img\people_image_4.png"
image_data = Image.open(path)
image_data = image_data.convert("RGBA")
image_data = image_data.resize((200, 400), Image.ANTIALIAS)
image_array = np.array(image_data)
image_item = gl.GLImageItem(image_array)
image_item.translate(0, 0, 0)

view.addItem(image_item)
app.instance().exec_()