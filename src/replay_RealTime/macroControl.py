import os
import sys

# 기능 변경 파트

# 탐지할 인원 상한
NUM_OF_DETECT_PEOPLE = 20

# Plotting Option : BoxHead는 0, CircleHead는 1
HTYPE_BOX_HEAD = 0
HTYPE_CIRCLE_HEAD = 1
HEAD_TYPE = HTYPE_BOX_HEAD

# For Debug
# Legacy AI model support
DEBUG_AI_INPUT_CONVERSION = True


# state 관련
class STATE:
    STATE_FALL = 0
    STATE_SIT = 1
    STATE_WALK = 3
    STATE_LIE_DOWN = 2

    TICKET_GREEN = 30
    TICKET_RED = 150

# AI 모델 관련
SEQ_SIZE = 5
MAX_SEQ_NOISE_LEN = SEQ_SIZE - 2   # 해당 길이보다 큰 노이즈 연속으로 들어오면 기존 큐를 삭제
MODEL_PATH = r"src\enhancedVisualizer\model\model_seq5.h5"

# path 관련
class PATH:
    if getattr(sys, 'frozen', False):   # base path for executable app
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    INI_FILE_NAME = "csv_converter.ini"
    INI_PATH = os.path.join(BASE_DIR, INI_FILE_NAME)

    DATA_DIR = os.path.join(BASE_DIR, 'data')