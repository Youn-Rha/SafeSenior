# import matplotlib.pyplot as plt

# colors = [
#     "#FF5733", "#33FF57", "#3357FF", "#F1C40F", "#9B59B6",
#     "#1ABC9C", "#3498DB", "#2ECC71", "#E67E22", "#34495E",
#     "#BDC3C7", "#7F8C8D", "#16A085", "#8E44AD", "#2C3E50",
#     "#27AE60", "#2980B9", "#E84393", "#6C5CE7", "#81ECEC",
#     "#00CEC9", "#55EFC4", "#FAB1A0", "#FFEAA7", "#D63031"
# ]

# default_color = "#95A5A6" # gray

# plt.bar(range(len(colors)), [1] * len(colors), color=colors)
# plt.show()

import matplotlib.pyplot as plt
import numpy as np
from PySide2.QtGui import QColor

# List of RGBA colors
colors_rgba = [
    (255, 87, 51, 1),  # #FF5733 - Orange Red
    (51, 255, 87, 1),  # #33FF57 - Lime Green
    (51, 87, 255, 1),  # #3357FF - Bright Blue
    (241, 196, 15, 1), # #F1C40F - Golden Yellow
    (155, 89, 182, 1), # #9B59B6 - Amethyst Purple
    (26, 188, 156, 1), # #1ABC9C - Turquoise
    (231, 76, 60, 1),  # #E74C3C - Crimson Red
    (52, 152, 219, 1), # #3498DB - Sky Blue
    (230, 126, 34, 1),# #E67E22 - Pumpkin Orange
    (52, 73, 94, 1),  # #34495E - Blue Gray
    (189, 195, 199, 1), # #BDC3C7 - Silver Gray
    (127, 140, 141, 1), # #7F8C8D - Slate Gray
    (22, 160, 133, 1), # #16A085 - Teal
    (142, 68, 173, 1), # #8E44AD - Dark Purple
    (44, 62, 80, 1),  # #2C3E50 - Midnight Blue
    (39, 174, 96, 1), # #27AE60 - Forest Green
    (41, 128, 185, 1),# #2980B9 - Blue
    (232, 67, 147, 1),# #E84393 - Hot Pink
    (108, 92, 231, 1),# #6C5CE7 - Royal Blue
    (129, 236, 236, 1),# #81ECEC - Aqua
    (0, 206, 201, 1),# #00CEC9 - Strong Teal
    (85, 239, 196, 1),# #55EFC4 - Mint Green
    (250, 177, 160, 1),# #FAB1A0 - Peach Pink
    (255, 234, 167, 1),# #FFEAA7 - Light Cream Yellow
    (214, 48, 49, 1)  # #D63031 - Scarlet Red
]

default_rgba = (149, 165, 166, 1) # #95A5A6 - Light Gray

# Convert RGBA to 0-1 range for matplotlib
colors_normalized = [(r/255, g/255, b/255, a) for r, g, b, a in colors_rgba]

# # Create a plot
# fig, ax = plt.subplots(figsize=(2, 10))

# # Display the colors as vertical bars
# ax.imshow([colors_normalized], aspect='auto', extent=[0, 1, 0, len(colors_rgba)])

# # Hide the axes
# ax.axis('off')

# # Show the plot
# plt.show()

colors_qcolor = [QColor(r, g, b, int(a * 255)) for r, g, b, a in colors_rgba]
default_qcolor = QColor(149, 165, 166, 255)

for qcolor in colors_qcolor:
    print(qcolor.name(), qcolor.alpha())
print(default_qcolor.name(), default_qcolor.alpha())
