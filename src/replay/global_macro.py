import os
import sys

# path 관련
class PATH:
    if getattr(sys, 'frozen', False):   # base path for executable app
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    INI_FILE_NAME = "TI6843ISK_Replay.ini"
    INI_PATH = os.path.join(BASE_DIR, INI_FILE_NAME)

    DATA_DIR = os.path.join(BASE_DIR, 'data')

class INI:
    PATH_SECTION = "Path"
    CSV = "csv"
    CFG = "cfg"

class CSV_META:
    FRAME_NUM = 0
    POINT_CNT = 1

# 재생속도 배수
PLAY_SPEED_MULTIPLIER = 0.5