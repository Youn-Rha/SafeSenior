import time
import os
import sys
import serial
import math
import numpy as np
import struct
from contextlib import suppress

# PySide imports
from PySide2 import QtGui
from PySide2.QtCore import QTimer, Qt, QThread, Signal
from PySide2.QtGui import QKeySequence, QIntValidator, QImage, QPixmap
from PySide2.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLineEdit,
    QLabel,
    QPushButton,
    QComboBox,
    QFileDialog,
    QMainWindow,
    QWidget,
    QApplication,
    QShortcut,
    QStatusBar,
    QMessageBox,
    QScrollArea,
    QSlider,
    QHBoxLayout,
)

# ini config imports
from configparser import ConfigParser

# local imports
from tlv_defines import *
from parseTLVs import *
from plot_3d import Plot3D
from PySide2.QtWidgets import QSizePolicy
from gui_threads import PeopleTracking

# parser functions list
parserFunctions = {
    # 3D People Tracking
    MMWDEMO_OUTPUT_MSG_TRACKERPROC_3D_TARGET_LIST:          parseTrackTLV,
    MMWDEMO_OUTPUT_MSG_TRACKERPROC_TARGET_HEIGHT:           parseTrackHeightTLV,
    MMWDEMO_OUTPUT_MSG_TRACKERPROC_TARGET_INDEX:            parseTargetIndexTLV,
    MMWDEMO_OUTPUT_MSG_COMPRESSED_POINTS:                   parseCompressedSphericalPointCloudTLV,
    # Others
    # MMWDEMO_OUTPUT_MSG_DETECTED_POINTS:                     parsePointCloudTLV,
    # MMWDEMO_OUTPUT_MSG_RANGE_PROFILE:                       parseRangeProfileTLV,
    # MMWDEMO_OUTPUT_EXT_MSG_RANGE_PROFILE_MAJOR:             parseRangeProfileTLV,
    # MMWDEMO_OUTPUT_EXT_MSG_RANGE_PROFILE_MINOR:             parseRangeProfileTLV,
    # MMWDEMO_OUTPUT_MSG_DETECTED_POINTS_SIDE_INFO:           parseSideInfoTLV,
    # MMWDEMO_OUTPUT_MSG_SPHERICAL_POINTS:                    parseSphericalPointCloudTLV,
    # MMWDEMO_OUTPUT_EXT_MSG_TARGET_LIST:                     parseTrackTLV,
    # MMWDEMO_OUTPUT_EXT_MSG_TARGET_INDEX:                    parseTargetIndexTLV,
    # MMWDEMO_OUTPUT_MSG_OCCUPANCY_STATE_MACHINE:             parseOccStateMachTLV,
    # MMWDEMO_OUTPUT_MSG_VITALSIGNS:                          parseVitalSignsTLV,
    # MMWDEMO_OUTPUT_EXT_MSG_DETECTED_POINTS:                 parsePointCloudExtTLV,
    # MMWDEMO_OUTPUT_MSG_GESTURE_FEATURES_6843:               parseGestureFeaturesTLV,
    # MMWDEMO_OUTPUT_MSG_GESTURE_OUTPUT_PROB_6843:            parseGestureProbTLV6843,
    # MMWDEMO_OUTPUT_MSG_GESTURE_CLASSIFIER_6432:             parseGestureClassifierTLV6432,
    # MMWDEMO_OUTPUT_EXT_MSG_ENHANCED_PRESENCE_INDICATION:    parseEnhancedPresenceInfoTLV,
    # MMWDEMO_OUTPUT_EXT_MSG_CLASSIFIER_INFO:                 parseClassifierTLV,
    # MMWDEMO_OUTPUT_MSG_SURFACE_CLASSIFICATION:              parseSurfaceClassificationTLV,
    # MMWDEMO_OUTPUT_EXT_MSG_VELOCITY:                        parseVelocityTLV,
    # MMWDEMO_OUTPUT_EXT_MSG_RX_CHAN_COMPENSATION_INFO:       parseRXChanCompTLV,
    # MMWDEMO_OUTPUT_MSG_EXT_STATS:                           parseExtStatsTLV,
    # MMWDEMO_OUTPUT_MSG_GESTURE_FEATURES_6432:               parseGestureFeaturesTLV6432,
    # MMWDEMO_OUTPUT_MSG_GESTURE_PRESENCE_x432:               parseGesturePresenceTLV6432,
    # MMWDEMO_OUTPUT_MSG_GESTURE_PRESENCE_THRESH_x432:        parsePresenceThreshold,
    # MMWDEMO_OUTPUT_EXT_MSG_STATS_BSD:                       parseExtStatsTLVBSD,
    # MMWDEMO_OUTPUT_EXT_MSG_TARGET_LIST_2D_BSD:              parseTrackTLV2D,
    # MMWDEMO_OUTPUT_EXT_MSG_CAM_TRIGGERS:                    parseCamTLV,
    # MMWDEMO_OUTPUT_EXT_MSG_POINT_CLOUD_ANTENNA_SYMBOLS:     parseAntSymbols,
    # MMWDEMO_OUTPUT_EXT_MSG_ADC_SAMPLES:                     parseADCSamples,
    # MMWDEMO_OUTPUT_EXT_MSG_MODE_SWITCH_INFO:                parseModeSwitchTLV
}

# MACRO constants
from macroControl import PATH
# if getattr(sys, 'frozen', False):   # base path for executable app
#     BASE_DIR = os.path.dirname(sys.executable)
# else:
#     BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# INI_FILE_NAME = "csv_converter.ini"
# INI_PATH = os.path.join(BASE_DIR, INI_FILE_NAME)

DATA_DIR = os.path.join(PATH.BASE_DIR, 'data')

CONNECT_N_MSG = "Not Connected"
CONNECT_Y_MSG = "Connected"
CONNECT_NA_MSG = "Unable to Connect"

CONNECT_BTN_MSG = "Connect"
CONNECT_BTN_RESET_MSG = "Reset Connection"

SEND_CFG_BTN_START_MSG = "Start with config"
SEND_CFG_BTN_RUN_MSG = "Sensor now Running"
SEND_CFG_BTN_RST_MSG = "Please Reset"

DEMO_LIST = ["People Count", "Out of Box"]

ACK_FAILED_TRESHOLD = 2
STATUS_MSG_DELAY = 2000

UART_MAGIC_WORD = bytearray(b'\x02\x01\x04\x03\x06\x05\x08\x07')

from macroControl import NUM_OF_DETECT_PEOPLE
# # 탐지할 인원 상한
# NUM_OF_DETECT_PEOPLE = 20

# SIZE MACRO
LEFT_WIDGET_SIZE = 500
MIN_WINDOW_WIDTH = 1280
MIN_WINDOW_HEIGHT = 720
INIT_WINDOW_WIDTH = 1980
INIT_WINDOW_HEIGHT = 1080

CONNECT_BOX_HEIGHT = 145
CFG_BOX_HEIGHT = 130
STAT_BOX_HEIGHT =130

FALL_PANEL_DIV = 2
FALL_PANEL_WIDTH = 200
FALL_PANEL_HEIGHT = 60
# 2분할시 너비 200, 3분할 시 너비 120, 4분할시 100

class Window(QMainWindow):
    def __init__(self, parent=None, title="app"):
        super().__init__(parent)

        # pre-declare
        self.fall_panels = []

        # GLView declare before core set
        self.gl_view = Plot3D()
        self.gl_view.plot_3d.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.core = Core(self)

        # ini parser setting
        self.iniParser = ConfigParser()
        if not os.path.exists(PATH.INI_PATH):
            self.core.ini_create(self.iniParser)
        
        self.iniParser.read(PATH.INI_PATH)
        if self.iniParser.sections() == []: # file with no contents
            self.core.ini_create(self.iniParser)

        self.demo_idx = self.core.ini_get_demo(self.iniParser)
        self.cli_com = self.core.ini_get_cli_com(self.iniParser)
        self.data_com = self.core.ini_get_data_com(self.iniParser)
        self.cfg_path = self.core.ini_get_cfg_path(self.iniParser)

        self.frame_count = 0
        self.image_list = []
        self.frame_index = 0
        self.frame_num = "0"
        self.label = None

        # part widget declare
        self.initConnectBox()
        self.initCfgBox()
        self.initStatBox()
        self.initFallDetectBox()
        self.initReplayBox()

        # icon
        if getattr(sys, 'frozen', False):
            self.setWindowIcon(QtGui.QIcon(os.path.join(sys._MEIPASS, 'bm_icon.ico')))
            print(sys._MEIPASS)
        else:
            self.setWindowIcon(QtGui.QIcon(PATH.BASE_DIR + "/img/bm_icon.ico"))

        # Layout setting
        self.gridLayout = QGridLayout()
        self.central = QWidget()
        self.central.setLayout(self.gridLayout)

        # left pannel
        self.leftWidget = QWidget()
        self.leftGridLayout = QGridLayout()
        self.leftGridLayout.addWidget(self.connectBox, 0, 0)
        self.leftGridLayout.addWidget(self.cfgBox, 1, 0)
        self.leftGridLayout.addWidget(self.statBox, 2, 0)
        self.leftGridLayout.addWidget(self.fallDetectionDisplayBox, 3, 0)
        self.leftWidget.setLayout(self.leftGridLayout)
        self.leftWidget.setFixedWidth(LEFT_WIDGET_SIZE)
        self.gridLayout.addWidget(self.leftWidget, 0, 0)

        # middleBottom panel 실험용
        self.middleBottomWidget = QWidget()
        self.middleBottomGridLayout = QGridLayout()
        self.middleBottomGridLayout.addWidget(self.replayBox, 0, 0)
        self.middleBottomWidget.setLayout(self.middleBottomGridLayout)
        self.gridLayout.addWidget(self.middleBottomWidget, 3, 1)

        # add GLViewWidget
        self.gridLayout.addWidget(self.gl_view.plot_3d , 0, 1)

        # adjust gl_view size with column stretch
        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 5)

        # status bar setting
        self.setStatusBar(QStatusBar(self)) # bottom bar that explains tooltips
        self.statusBar().showMessage("Status Description")

        # window size setting
        self.setMinimumWidth(MIN_WINDOW_WIDTH)
        self.setMinimumHeight(MIN_WINDOW_HEIGHT)
        self.resize(INIT_WINDOW_WIDTH, INIT_WINDOW_HEIGHT)

        self.connectBox.setFixedHeight(CONNECT_BOX_HEIGHT)
        self.cfgBox.setFixedHeight(CFG_BOX_HEIGHT)
        self.statBox.setFixedHeight(STAT_BOX_HEIGHT)

        # Shortcut
        self.shortcut = QShortcut(QKeySequence("Ctrl+Q"), self) # ctrl+Q to close program
        self.shortcut.activated.connect(self.close)

        self.setCentralWidget(self.central)
        self.setWindowTitle(title)

        # set boundaryBox using cfg_path
        self.initBoundaryBox()

    def initConnectBox(self):
        # outter box
        self.connectBox = QGroupBox("Connection")
        self.connectLayout = QGridLayout()
        self.connectBox.setLayout(self.connectLayout)
        self.connectCfgLayout = QGridLayout()
        self.connectBtnLayout = QGridLayout()
        self.connectLayout.addLayout(self.connectCfgLayout, 0, 0)
        self.connectLayout.addLayout(self.connectBtnLayout, 1, 0)

        # inner component
        self.connectCfgLayout.addWidget(QLabel("Demo"), 0, 0)
        self.demoList = QComboBox()
        self.demoList.addItems(DEMO_LIST)
        self.connectCfgLayout.addWidget(self.demoList, 0, 1)
        self.demoList.setCurrentIndex(self.demo_idx)

        self.connectCfgLayout.addWidget(QLabel("CLI COM"), 1, 0)
        self.cli_num_line = QLineEdit(self.cli_com)
        self.cli_num_line.setToolTip("Enhanced Port")
        self.connectCfgLayout.addWidget(self.cli_num_line, 1, 1)
        
        self.connectCfgLayout.addWidget(QLabel("Data COM"), 2, 0)
        self.data_num_line = QLineEdit(self.data_com)
        self.data_num_line.setToolTip("Standard Port")
        self.connectCfgLayout.addWidget(self.data_num_line, 2, 1)

        self.connectStatus = QLabel(CONNECT_N_MSG)
        self.connectStatus.setAlignment(Qt.AlignCenter)
        self.connectBtnLayout.addWidget(self.connectStatus, 0, 0)
        self.connectBtn = QPushButton(CONNECT_BTN_MSG)
        self.connectBtn.setToolTip("You MUST set COM port before connection")
        self.connectBtn.setMaximumWidth(120)
        self.connectBtnLayout.addWidget(self.connectBtn, 0, 1)

        # COM Port range restriction
        self.COM_valid = QIntValidator(1, 256)
        self.cli_num_line.setValidator(self.COM_valid)
        self.data_num_line.setValidator(self.COM_valid)

        # signal connection
        self.demoList.currentIndexChanged.connect(self.demoChanged)
        self.connectBtn.clicked.connect(self.startConnect)

    def initCfgBox(self):
        # outter box
        self.cfgBox = QGroupBox("Config")
        self.cfgLayout = QGridLayout()
        self.cfgBox.setLayout(self.cfgLayout)

        # inner box
        self.filenameCfg = QLineEdit(self.cfg_path)
        self.filenameCfg.setReadOnly(True)
        self.cfgLayout.addWidget(self.filenameCfg, 0, 0)

        self.selectCfgBtn = QPushButton("Select config")
        self.selectCfgBtn.setFixedWidth(100)
        self.cfgLayout.addWidget(self.selectCfgBtn, 0, 1)

        self.sendCfgBtn = QPushButton(SEND_CFG_BTN_START_MSG)
        self.sendCfgBtn.setEnabled(False)
        self.cfgLayout.addWidget(self.sendCfgBtn, 1, 0, 1, 2)

        # signal connection
        self.selectCfgBtn.clicked.connect(lambda: self.selectCfg(self.filenameCfg))
        self.sendCfgBtn.clicked.connect(self.startSensor)

    def initStatBox(self):
        self.statBox = QGroupBox("Statistics")
        self.statLayout = QGridLayout()
        self.statBox.setLayout(self.statLayout)
        self.frameNumLabel = QLabel("Frame : 0")
        self.plotTimeLabel = QLabel("Plot Time : 0 ms")
        self.numPointsLabel = QLabel("Points : 0")
        self.numTargetsLabel = QLabel("Targets : 0")

        self.statLayout.addWidget(self.frameNumLabel, 0, 0)
        self.statLayout.addWidget(self.plotTimeLabel, 1, 0)
        self.statLayout.addWidget(self.numPointsLabel, 2, 0)
        self.statLayout.addWidget(self.numTargetsLabel, 3, 0)
    
    def initFallDetectBox(self):
        self.fallDetectionDisplayBox = QGroupBox('Fall Notification')
        self.faldt_layout = QGridLayout()
        self.fallDetectionDisplayBox.setLayout(self.faldt_layout)
        self.faldt_contetns = QWidget()
        self.faldt_scroll = QScrollArea()
        self.faldt_scroll.setWidgetResizable(True)
        self.faldt_layout.addWidget(self.faldt_scroll)
        self.faldt_scroll.setWidget(self.faldt_contetns)
        self.faldt_inner_layout = QGridLayout()
        self.faldt_contetns.setLayout(self.faldt_inner_layout)

        # 스크롤 높이 설정
        max_scroll_len = (FALL_PANEL_HEIGHT + 10) * ((NUM_OF_DETECT_PEOPLE + 2) / FALL_PANEL_DIV) + 10
        self.faldt_scroll.setMaximumHeight(max_scroll_len)

        # 패널 리스트 초기화 (NUM_OF_DETECT_PEOPLE 개의 패널 생성)
        # self.fall_panels = []
        for i in range(NUM_OF_DETECT_PEOPLE):
            f_panel = QLabel(f"사람 {i + 1}")
            f_panel.setStyleSheet("background-color: transparent; border: 1px solid gray; color: black;")
            f_panel.setFixedSize(FALL_PANEL_WIDTH, FALL_PANEL_HEIGHT)
            f_panel.setAlignment(Qt.AlignCenter)

            self.fall_panels.append(f_panel)
            # 분할 구현 : FALL_PANEL_DIV 수 만큼 분할
            self.faldt_inner_layout.addWidget(f_panel, i / FALL_PANEL_DIV, i % FALL_PANEL_DIV)

    def initReplayBox(self):
        self.replayBox = QGroupBox("Replay")
        self.replayBox.setFixedSize(900, 120)
        self.replayLayout = QGridLayout()
        self.replayBox.setLayout(self.replayLayout)

        self.timelineSlider = QSlider(Qt.Horizontal)
        self.timelineSlider.setMinimum(0)
        self.timelineSlider.setMaximum(100)
        self.timelineSlider.setValue(0)
        self.timelineSlider.setFixedSize(800, 30)
        self.timelineSlider.setTickPosition(QSlider.TicksBelow)
        self.timelineSlider.setTickInterval(10)
        self.timelineSlider.setToolTip("Timeline")

        self.frameLabelLayout = QHBoxLayout()
        self.frameLabel = QLabel("FrameNums : 0")
        self.frameInputBox = QLineEdit(self.frame_num)
        self.frameInputBox.setFixedSize(40, 20)
        self.submitBtn = QPushButton("Move")
        self.submitBtn.setFixedSize(50, 20)
        # self.submitBtn.clicked.connect(self.restore_widget_btn(self.frame_num))
        self.submitBtn.clicked.connect(lambda: self.restore_widget_btn(self.frameInputBox.text()))
        self.frameLabelLayout.addWidget(self.frameLabel)
        self.frameLabelLayout.addWidget(self.frameInputBox)
        self.frameLabelLayout.addWidget(self.submitBtn)

        self.frameLabelWidget = QWidget()
        self.frameLabelWidget.setLayout(self.frameLabelLayout)

        self.replayBtn = QPushButton("▶")
        self.replayBtn.setFixedSize(40, 40)
        self.replayBtn.clicked.connect(self.toggleReplay)

        self.frameBtnLayout = QHBoxLayout()
        self.frameLBtn = QPushButton("←")
        self.frameLBtn.setFixedSize(30, 30)
        self.frameRBtn = QPushButton("→")
        self.frameRBtn.setFixedSize(30, 30)
        self.frameLBtn.clicked.connect(self.restore_leftframe)
        self.frameRBtn.clicked.connect(self.restore_rightframe)
        self.frameBtnLayout.addWidget(self.frameLBtn)
        self.frameBtnLayout.addWidget(self.frameRBtn)

        self.frameBtnWidget = QWidget()
        self.frameBtnWidget.setLayout(self.frameBtnLayout)

        self.replayLayout.addWidget(self.timelineSlider, 0, 0, 1, 1)
        self.replayLayout.addWidget(self.frameLabelWidget, 1, 0, Qt.AlignLeft)
        self.replayLayout.addWidget(self.replayBtn, 1, 0, Qt.AlignCenter)
        self.replayLayout.addWidget(self.frameBtnWidget, 1, 0, Qt.AlignRight)

    def frameControl(self):
        self.frametimer = QTimer()
        self.frametimer.timeout.connect(self.capture_frame_image)
        self.replayBtn.setText("⏸")
        self.frametimer.start(33)

    def toggleReplay(self):
        current_text = self.replayBtn.text()
        if current_text == "▶":
            # self.remove_all_items()
            # self.gl_view.__init__()
            self.label.hide()
            self.startSensor()
        else:
            self.startConnect()

    # def remove_all_items(self):
    #     for item in self.gl_view.plot_3d.items:
    #         self.gl_view.plot_3d.removeItem(item)

    def capture_frame_image(self):
        # image = QImage(self.gl_view.plot_3d.width(), self.gl_view.plot_3d.height(), QImage.Format_RGBA8888)
        # self.gl_view.plot_3d.render(image)
        image = self.gl_view.plot_3d.grabFrameBuffer()
        pixmap = QPixmap.fromImage(image)
        self.image_list.append(pixmap)
        self.frameLabel.setText("FrameNums : " + str(self.frame_count))
        self.frame_count += 1

    # def capture_frame_widget(self):
    #     self.image_list.append(self.gl_view.plot_3d)
    #     self.frameLabel.setText("FrameNums : " + str(self.frame_count))
    #     self.frame_count += 1

    def restore_leftframe(self):
        if 0 < self.frame_index:
            self.frame_index -= 1
            self.restore_image(self.frame_index)

    def restore_rightframe(self):
        if self.frame_index < len(self.image_list) - 1: 
            self.frame_index += 1
            self.restore_image(self.frame_index)

    # def restore_widget(self, index):
    #     if 0 <= index < len(self.image_list):
    #         self.gl_view.plot_3d = self.image_list[index]
    #         self.frameLabel.setText("FrameNums : " + str(self.frame_index))

    def restore_image(self, index):
        if 0 <= index < len(self.image_list):
            if self.label is not None:
                self.label.hide()
            pixmap = self.image_list[index]
            self.label = QLabel(self.gl_view.plot_3d)
            self.label.setPixmap(pixmap)
            self.label.show()
            self.frameLabel.setText("FrameNums : " + str(self.frame_index))

    def restore_widget_btn(self, index):
        intIndex = int(index)
        if intIndex > len(self.image_list):
            intIndex = self.frame_count - 1
        self.frame_index = intIndex
        self.restore_image(self.frame_index)

    # def get_frame(self, index):
    #     if 0 <= index < len(self.image_list):
    #         return self.image_list[index]
    #     else:
    #         return None

    # REF : onConnect(self)
    def startConnect(self):
        if(self.connectStatus.text() == CONNECT_N_MSG or self.connectStatus.text() == CONNECT_NA_MSG):
            if self.core.connectCom(self.connectStatus) == 0:
                self.connectBtn.setText(CONNECT_BTN_RESET_MSG)
                self.sendCfgBtn.setEnabled(True)
                self.statusBar().showMessage("Connected", STATUS_MSG_DELAY)
            else:
                self.sendCfgBtn.setEnabled(False)
                self.statusBar().showMessage("Connect Failed", STATUS_MSG_DELAY)
        else:
            self.core.gracefulReset()
            self.connectStatus.setText(CONNECT_N_MSG)
            self.connectBtn.setText(CONNECT_BTN_MSG)
            self.replayBtn.setText("▶")
            self.frame_index = self.frame_count
            self.frametimer.stop()
            self.sendCfgBtn.setEnabled(False)   # double check
            self.sendCfgBtn.setText(CONNECT_BTN_MSG)

    # REF : onChangeDemo -> core.changeDemo
    def demoChanged(self):
        self.demo_idx = self.demoList.currentIndex()
        self.statusBar().showMessage("Demo : " + self.demoList.currentText(), STATUS_MSG_DELAY)

    # REF : core.selectCfg
    def selectCfg(self, cfgLine):
        self.statusBar().showMessage("Select configuartion file", STATUS_MSG_DELAY)

        fname = self.core.selectFile(cfgLine)
        if fname == "":
            return  # selection canceled
        try:
            self.core.parseCfg(fname)
            # if parse succed, set text
            cfgLine.setText(fname)
            self.statusBar().showMessage("cfg set : " + os.path.basename(fname), STATUS_MSG_DELAY)
        except Exception as e:
            self.cfg_selec_warn(e)

    def cfg_selec_warn(self, e: Exception):
        self.cfg_select_warn_box = QMessageBox.warning(
            self, "Cfg selection error", repr(e)
        )

    def reset_warn(self):
        self.reset_warn_box = QMessageBox.warning(
            self, "ACK receive failed", "Need to Reset Sensor with physical button"
        )
        self.sendCfgBtn.setDisabled(True)
        self.sendCfgBtn.setText(SEND_CFG_BTN_RST_MSG)

    def startSensor(self):
        self.statusBar().showMessage("Send config and start")
        self.frameControl()
        if(self.core.sendCfg()):
            # disable button before reset
            self.sendCfgBtn.setDisabled(True)
            self.sendCfgBtn.setText(SEND_CFG_BTN_RUN_MSG)

    def initBoundaryBox(self):
        if self.cfg_path != "":
            try:
                self.core.parseCfg(self.cfg_path)
            except Exception as e:
                self.cfg_path = ""
                print("failed to read init cfg file : ", e)
                self.statusBar().showMessage("failed to read init cfg file", STATUS_MSG_DELAY)

    def closeEvent(self, event):
        event.accept()
        self.core.ini_save(self.iniParser)
        QApplication.quit()


class Core:
    def __init__(self, window: Window):
        self.parser = UARTParser()
        self.demo = DEMO_LIST[0]
        self.window = window
        self.frameTime = 55     # init for just in case

        # demo class Dictionary : init class per demo
        self.demoClassDict = {
            DEMO_LIST[0]: PeopleTracking(self.window),
            DEMO_LIST[1]: PeopleTracking(self.window),
        }

    def selectFile(self, fLine: QLineEdit):
        try:
            cfg_dir = PATH.BASE_DIR
            # recover dir from ini
            path = fLine.text()
            if path != "":
                cfg_dir = os.path.dirname(path)
                if not os.path.exists(cfg_dir):
                    cfg_dir = ""
        except:
            cfg_dir = ""

        fname = QFileDialog.getOpenFileName(caption="Open .cfg File", dir=cfg_dir, filter="cfg(*.cfg)")
        return fname[0]

    def parseCfg(self, fname):
        with open(fname, "r") as cfg_file:
            self.cfg_lines = cfg_file.readlines()
            self.parser.cfg = self.cfg_lines
            self.parser.demo = self.demo
        
        for line in self.cfg_lines:
            args = line.split()
            if len(args) > 0:
                if args[0] == "trackingCfg":
                    if len(args) < 5:
                        print("CFG_ERROR : trackingCfg had fewer arguments than expected")
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.window.demoList.currentText()].parseTrackingCfg(args)
                elif args[0] == "SceneryParam" or args[0] == "boundaryBox":
                    if len(args) < 7:
                        print("CFG_ERROR : SceneryParam/boundaryBox had fewer arguments than expected")
                    else:
                        # with suppress(AttributeError):
                            # self.demoClassDict[self.window.demoList.currentText()].parseBoundaryBox(args)
                        self.window.gl_view.parseBoundaryBox(args)
                elif args[0] == "frameCfg":
                    if len(args) < 4:
                        print("CFG_ERROR : frameCfg had fewer arguments than expected")
                    else:
                        self.frameTime = float(args[5]) / 2
                elif args[0] == "sensorPosition":
                        if len(args) < 4:
                            print("CFG_ERROR : sensorPosition had fewer arguments than expected")
                        else:
                            with suppress(AttributeError):
                                # self.demoClassDict[self.window.demoList.currentText()].parseSensorPosition(args)
                                self.window.gl_view.parseSensorPosition(args)

    # Start with config button call this method
    # REF : core.sendCfg
    def sendCfg(self):
        try:
            self.cfg_lines
        except AttributeError:
            try:
                self.parseCfg(self.window.filenameCfg.text())
            except Exception as e:
                self.window.cfg_selec_warn(e)
                return False

        if not self.parser.uartSendCfg(self.cfg_lines):
            self.window.reset_warn()
            sys.stdout.flush()
            return
        sys.stdout.flush()
        # it will start self.parseData thread
        self.parseTimer.start(self.frameTime)

        return True

    # Connection Handling
    # REF : connectCom()
    def connectCom(self, statusLine: QLabel):
        self.cli_com = int(self.window.cli_num_line.text())
        self.data_com = int(self.window.data_num_line.text())

        # init thread
        self.uart_thread = parseUartThread(self.parser)

        self.uart_thread.fin.connect(self.updateGraph)
        # Notice : timer starts from sendCfg() - binds with sendCfgBtn
        self.parseTimer = QTimer()
        self.parseTimer.setSingleShot(False)
        self.parseTimer.timeout.connect(self.parseData)

        try:
            if os.name == "nt":
                uart = "COM" + str(self.cli_com)
                data = "COM" + str(self.data_com)
            else:
                uart = self.cli_com
                data = self.data_com
            self.parser.connectComPort(uart, data)
            self.window.connectStatus.setText(CONNECT_Y_MSG)
        except:
            self.window.connectStatus.setText(CONNECT_NA_MSG)
            return -1

        return 0
    
    def updateGraph(self, outputDict: dict):
        # find matching (csv convert) function
        self.demoClassDict[self.window.demoList.currentText()].updateGraph(outputDict)

    # REF : gracefulReset()
    def gracefulReset(self):
        self.parseTimer.stop()
        self.uart_thread.stop()

        if self.parser.cliCom is not None:
            self.parser.cliCom.close()
        if self.parser.dataCom is not None:
            self.parser.dataCom.close()

    def parseData(self):
        self.uart_thread.start(priority=QThread.HighestPriority)

    
    # INI Parse
    def ini_get_demo(self, parser: ConfigParser):
        self.demo_idx = self.window.iniParser.getint(
            "Selection", "demo_idx", fallback=0
        )
        if self.demo_idx >= len(DEMO_LIST):
            self.demo_idx = 0
        return self.demo_idx
    
    def ini_get_cli_com(self, parser: ConfigParser):
        self.cli_com = self.window.iniParser.get(
            "Selection", "cli_com", fallback=""
        )
        try:
            if (self.cli_com != "") and ((int(self.cli_com) < 1) or (int(self.cli_com) > 256)):
                self.cli_com = ""
        except ValueError:
                self.cli_com = ""
        return self.cli_com
    
    def ini_get_data_com(self, parser: ConfigParser):
        self.data_com = self.window.iniParser.get(
            "Selection", "data_com", fallback=""
        )
        try:
            if (self.data_com != "") and ((int(self.data_com) < 1) or (int(self.data_com) > 256)):
                self.data_com = ""
        except ValueError:
                self.data_com = ""
        return self.data_com

    def ini_get_cfg_path(self, parser: ConfigParser):
        self.cfg_path = self.window.iniParser.get(
            "Selection", "cfg_path", fallback=""
        )
        if not os.path.exists(self.cfg_path):
            self.cfg_path = ""
        return self.cfg_path

    def ini_create(self, parser: ConfigParser):
        if "Selection" not in parser:
            parser["Selection"] = {
                "Demo_idx" : "0",
                "CLI_COM" : "",
                "Data_COM" : "",
                "cfg_path" : ""
            }

        self.ini_write(parser)

    def ini_write(self, parser: ConfigParser):
        with open(PATH.INI_PATH, "w", encoding="UTF-8") as ini_file:
            parser.write(ini_file)
    
    def ini_save(self, parser: ConfigParser):
        parser["Selection"]["Demo_idx"] = str(self.window.demo_idx)
        parser["Selection"]["cli_com"] = self.window.cli_num_line.text()
        parser["Selection"]["data_com"] = self.window.data_num_line.text()
        parser["Selection"]["cfg_path"] = self.window.filenameCfg.text()
        
        self.ini_write(parser)


class UARTParser():
    def __init__(self):
        self.binData = bytearray(0)
        self.uartCounter = 0

    def readAndParseUartCOMPort(self):
        fail = 0
        index = 0

        magicByte = self.dataCom.read(1)
        frameData = bytearray(b'')

        while (1):
            if (len(magicByte) < 1):
                if(fail > 10):
                    return {}
                fail += 1
                # data receive failed, retry
                magicByte = self.dataCom.read(1)
            elif (magicByte[0] == UART_MAGIC_WORD[index]):
                index += 1
                frameData.append(magicByte[0])
                if (index == 8):    # full magic word found
                    break
                magicByte = self.dataCom.read(1)
            else:
                # failed to find next magicByte : do reset
                if (index == 0):
                    magicByte = self.dataCom.read(1)
                index = 0
                frameData = bytearray(b'')

        versionBytes = self.dataCom.read(4)
        frameData += bytearray(versionBytes)

        lengthBytes = self.dataCom.read(4)
        frameData += bytearray(lengthBytes)
        frameLength = int.from_bytes(lengthBytes, byteorder='little')
        # subtract already readed bytes : magic word, version ...
        frameLength -= 16

        frameData += bytearray(self.dataCom.read(frameLength))

        outputDict = self.parseStandardFrame(frameData)

        return outputDict
    
    def parseStandardFrame(self, frameData):
        headerStruct = 'Q8I'    # UART binary format what ti sensor often uses
        frameHeaderLen = struct.calcsize(headerStruct)
        tlvHeaderLength = 8

        outputDict = {}
        outputDict['error'] = 0

        totalLenCheck = 0

        # Read the frame Header
        try:
            magic, version, totalPacketLen, platform, frameNum, timeCPUCycles, numDetectedObj, numTLVs, subFrameNum = struct.unpack(headerStruct, frameData[:frameHeaderLen])
        except:
            # header read failed
            outputDict['error'] = 1

        # Move frameData ptr to start of 1st TLV   
        frameData = frameData[frameHeaderLen:]
        totalLenCheck += frameHeaderLen

        outputDict['frameNum'] = frameNum

        # pointInfo : X, Y, Z, Doppler, SNR, Noise, Track index
        outputDict['pointCloud'] = np.zeros((numDetectedObj, 7), np.float64)
        # init Track index as no track(255)
        outputDict['pointCloud'][:, 6] = 255

        # find and parse all TLVs
        for i in range(numTLVs):
            try:
                tlvType, tlvLength = struct.unpack('2I', frameData[:tlvHeaderLength])
                frameData = frameData[tlvHeaderLength:]
                totalLenCheck += tlvHeaderLength
            except:
                # parsing error, ignore frame
                outputDict['error'] = 2
                return {}

            if (tlvType in parserFunctions):
                parserFunctions[tlvType](frameData[:tlvLength], tlvLength, outputDict)

            # move to next TLV
            frameData = frameData[tlvLength:]
            totalLenCheck += tlvLength
        
        totalLenCheck = 32 * math.ceil(totalLenCheck / 32)
        if (totalLenCheck != totalPacketLen):
            # subsequent frames may dropped due to transmission error
            outputDict['error'] = 3
        
        return outputDict

    def connectComPort(self, cliCom, dataCom):
        self.cliCom = serial.Serial(cliCom, 115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.6)
        self.dataCom = serial.Serial(dataCom, 921600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.6)
        self.dataCom.reset_output_buffer()

    # REF : UARTParser.sendCfg
    def uartSendCfg(self, cfg: list[str]):
        failed_cnt = 0

        # remove empty lines from the cfg
        cfg = [line for line in cfg if line != '\n']
        # attach \n at the end of each line
        cfg = [line + '\n' if not line.endswith('\n') else line for line in cfg]
        # remove commented lines
        cfg = [line for line in cfg if line[0] != '%']

        for line in cfg:
            if(failed_cnt >= ACK_FAILED_TRESHOLD):
                # need to reset sensor
                return False
            time.sleep(0.03)    # line dealy

            if(self.cliCom.baudrate == 1250000):
                for char in [*line]:    # [*var] unpacks list into elements
                    time.sleep(0.001)   # char delay
                    self.cliCom.write(char.encode())
            else:
                self.cliCom.write(line.encode())

            # print ack messages
            ack = self.cliCom.readline()
            print(ack, flush=True)
            if(ack == b''):
                failed_cnt += 1
            else:
                failed_cnt = 0
            ack = self.cliCom.readline()
            print(ack, flush=True)

            splitLine = line.split()
            if(splitLine[0] == "baudRate"):
                try:
                    self.cliCom.baudrate = int(splitLine[1])
                except:
                    sys.exit(1)
        
        time.sleep(0.03)
        self.cliCom.reset_input_buffer()

        return True

    def sendLine(self, line: str):
        if(self.cliCom.baudrate == 1250000):
            for char in [*line]:
                time.sleep(0.001)
                self.cliCom.write(char.encode())
        else:
            self.cliCom.write(line.encode())
        ack = self.cliCom.readline()
        print(ack)
        ack = self.cliCom.readline()
        print(ack)

# Thread Define
class parseUartThread(QThread):
    fin = Signal(dict)

    def __init__(self, uParser: UARTParser):
            QThread.__init__(self)
            self.parser = uParser

    def run(self):
        outputDict = self.parser.readAndParseUartCOMPort()
        self.fin.emit(outputDict)

    def stop(self):
        self.terminate()


class calc():
    def next_power_of_2(x):  
        return 1 if x == 0 else 2**(x - 1).bit_length()

    # Convert 3D Spherical Points to Cartesian
    # Assumes sphericalPointCloud is an numpy array with at LEAST 3 dimensions
    # Order should be Range, Elevation, Azimuth
    def sphericalToCartesianPointCloud(sphericalPointCloud):
        shape = sphericalPointCloud.shape
        cartesianPointCloud = sphericalPointCloud.copy()
        if (shape[1] < 3):
            print('Error: Failed to convert spherical point cloud to cartesian due to numpy array with too few dimensions')
            return sphericalPointCloud

        # Compute X
        # Range * sin (azimuth) * cos (elevation)
        cartesianPointCloud[:,0] = sphericalPointCloud[:,0] * np.sin(sphericalPointCloud[:,1]) * np.cos(sphericalPointCloud[:,2]) 
        # Compute Y
        # Range * cos (azimuth) * cos (elevation)
        cartesianPointCloud[:,1] = sphericalPointCloud[:,0] * np.cos(sphericalPointCloud[:,1]) * np.cos(sphericalPointCloud[:,2]) 
        # Compute Z
        # Range * sin (elevation)
        cartesianPointCloud[:,2] = sphericalPointCloud[:,0] * np.sin(sphericalPointCloud[:,2])
        return cartesianPointCloud


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window(title="Batch Maker : Fall Detect")
    main.show()
    sys.exit(app.exec_())
