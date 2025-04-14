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
DEBUG_AI_INPUT_CONVERSION = False


# state 관련
class STATE:
    STATE_FALL = 0
    STATE_SIT = 1
    STATE_LIE_DOWN = 2
    STATE_WALK = 3

    TICKET_GREEN = 30
    TICKET_RED = 150

# AI 모델 관련
SEQ_SIZE = 15
MAX_SEQ_NOISE_LEN = 5   # 해당 길이보다 큰 노이즈 연속으로 들어오면 기존 큐를 삭제
MODEL_PATH = r"src\enhancedVisualizer\model\model_seq5_carte.h5"
MODEL_SEQ_SIZE = 5

# path 관련
class PATH:
    if getattr(sys, 'frozen', False):   # base path for executable app
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    INI_FILE_NAME = "csv_converter.ini"
    INI_PATH = os.path.join(BASE_DIR, INI_FILE_NAME)

    DATA_DIR = os.path.join(BASE_DIR, 'data')

CLUST_MIN_SAMPLES = 30
CLUST_EPS = 1

# cluster cache 관련
class CLUSTER_CACHE:
    # clust_cache 내부 요소의 index 참조용
    XPOS = 0
    YPOS = 1
    TICKET = 2
    STATE = 3
    PID = 4
    CNT = 5
    PLTD_X = 6
    PLTD_Y = 7
    
    DISTANCE_THRESHOLD = 0.2    # cluster x, y 좌표간 squared 거리 기반 같은 클러스터 판별 임계값
    TICKET_UPDATE = 10  # 엔트리 업데이트 할 때의 티켓
    MIN_PLOT_CNT = 5    # 화면에 클러스터 결과 반영까지 필요한 최소 카운트 수
    MIN_DISTANCE_TO_MOVE = 0.1  # 모델 위치 변경에 필요한 최소한의 위치 변화
