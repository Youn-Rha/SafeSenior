import os
import sys
import csv
import numpy as np
from functools import partial
import copy

# PySide imports
from PySide2 import QtGui
from PySide2.QtCore import QTimer, Qt
from PySide2.QtGui import QKeySequence, QColor, QIntValidator
from PySide2.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLineEdit,
    QLabel,
    QPushButton,
    QFileDialog,
    QMainWindow,
    QWidget,
    QApplication,
    QShortcut,
    QSlider,
    QSizePolicy,
    QMessageBox,
    QScrollArea,
    QDialog,
    QDialogButtonBox,
    QCheckBox
)

# ini config imports
from configparser import ConfigParser

from plot_3d import Plot3D
import pyqtgraph as pg

# MACRO constants
from global_macro import PATH, INI, CSV_META, PLAY_SPEED_MULTIPLIER

# SIZE MACRO
LEFT_WIDGET_SIZE = 500
MIN_WINDOW_WIDTH = 1280
MIN_WINDOW_HEIGHT = 720
INIT_WINDOW_WIDTH = 1980
INIT_WINDOW_HEIGHT = 1080

CSV_BOX_HEIGHT = 100
CFG_BOX_HEIGHT = 100
INFO_BOX_HEIGHT = 150
REPLAY_BOX_HEIGHT = 150

CONTROL_BOX_WIDTH = 800

PLAY_BTN_SIZE = 45
SIDE_BTN_SIZE = 40

MINI_BTN_WIDTH = 70

# TEXT MACRO
SELECT_CSV = "Select csv"
SELECT_CFG = "Select cfg"

GRP_BOX_CSV = "Select csv table"
GRP_BOX_CFG = "Config"
GRP_BOX_INFO = "Information"
# GRP_BOX_REPLAY = "Replay"

INFO_TOTAL_FRAME = "Total Frame : "
INFO_FRAME_NUM = "Current Frame : "
INFO_POINT_NUM = "Points : "
INFO_REAL_FRAME = "frameNum in CSV : "

REPLAY_START_BTN = "▶"
REPLAY_NEXT_BTN = "→"
REPLAY_PREV_BTN = "←"
REPLAY_PAUSE_BTN = "⏸"
REPLAY_TO_START_BTN = "|◀"
REPLAY_TO_END_BTN = "▶|"

FRAME_SET_MSG = "Set Frame "
FRAME_TO_MSG = " to "
FRAME_MOVE_MSG = "Move"

PLAY_SPEED_MSG = "Play Speed  x"
PLAY_SPEED_SET_MSG = "Set"

# QDialog
IDX_SET_DIALOG_TITLE = "Set Target Number"
IDX_SET_DIALOG_MSG = "Set the Target Number for the change : "
IDX_SET_DIALOG_WIDTH = 350
IDX_SET_DIALOG_HEIGHT = 100
IDX_SET_INPUT_WIDTH = 70


class Window(QMainWindow):
    def __init__(self, parent=None, title="app"):
        super().__init__(parent)

        self.gl_view = Plot3D()
        self.gl_view.plot_3d.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # init value setting
        self.cfg_path = ""
        self.csv_path = ""
        self.currentFrame = 0
        self.totalFrame = 0
        self.pointCnt = 0
        self.realFrameNum = 0
        self.frameTime = 50     # default value [ms]
        self.originalFrameTime = self.frameTime
        self.originalDictList = []
        self.revisedDictList = []
        self.csvMetaData = []
        self.isPlaying = False
        self.firstFrameNum = -1
        self.playSpeedMultiplier = PLAY_SPEED_MULTIPLIER
        self.selectedCluster = set([])
        self.curFrameCluster = set([])
        self.curFilePath = ""

        # Frame Timer
        self.frameTimer = QTimer()
        self.frameTimer.timeout.connect(lambda: self.displayFrameTimer())

        # ini parser setting
        self.iniParser = ConfigParser()
        if not os.path.exists(PATH.INI_PATH):
            self.ini_create(self.iniParser)
        
        self.iniParser.read(PATH.INI_PATH)
        if self.iniParser.sections() == []: # file with no contents
            self.ini_create(self.iniParser)

        self.cfg_path = self.ini_get_cfg_path(self.iniParser)
        self.csv_path = self.ini_get_csv_path(self.iniParser)

        self.colors_rgba = [
            (255, 87, 51, 1),  # #FF5733 - Orange Red
            (51, 255, 87, 1),  # #33FF57 - Lime Green
            (51, 87, 255, 1),  # #3357FF - Bright Blue
            (241, 196, 15, 1), # #F1C40F - Golden Yellow
            (255, 255, 255, 1), # White
            (155, 89, 182, 1), # #9B59B6 - Amethyst Purple
            (26, 188, 156, 1), # #1ABC9C - Turquoise
            (231, 76, 60, 1),  # #E74C3C - Crimson Red
            (52, 152, 219, 1), # #3498DB - Sky Blue
            (230, 126, 34, 1),# #E67E22 - Pumpkin Orange
            # (52, 73, 94, 1),  # #34495E - Blue Gray
            (139, 69, 19, 1), # Brown
            # (127, 140, 141, 1), # #7F8C8D - Slate Gray
            (22, 160, 133, 1), # #16A085 - Teal
            (142, 68, 173, 1), # #8E44AD - Dark Purple
            # (44, 62, 80, 1),  # #2C3E50 - Midnight Blue
            (255, 191, 204, 1), # Pastel Pink
            (189, 195, 199, 1), # #BDC3C7 - Silver Gray
            (39, 174, 96, 1), # #27AE60 - Forest Green
            (41, 128, 185, 1),# #2980B9 - Blue
            (232, 67, 147, 1),# #E84393 - Hot Pink
            (108, 92, 231, 1),# #6C5CE7 - Royal Blue
            (129, 236, 236, 1),# #81ECEC - Aqua
            (0, 206, 201, 1),# #00CEC9 - Strong Teal
            (85, 239, 196, 1),# #55EFC4 - Mint Green
            (250, 107, 180, 1),# #FAB1A0 - Peach Pink
            (255, 234, 167, 1),# #FFEAA7 - Light Cream Yellow
            (214, 48, 49, 1)  # #D63031 - Scarlet Red
        ]
        self.colors_qcolor = [QColor(r, g, b, int(a * 255)) for r, g, b, a in self.colors_rgba]
        self.color_cnt = len(self.colors_qcolor)
        self.default_qcolor = QColor(149, 165, 166, 255)
        self.image_list = []
        self.label = None
        self.image_count = 0
        
        # part widget declare
        self.initCsvBox()
        self.initCfgBox()
        self.initInfoBox()
        self.initReplayBox()
        self.initClustCtrlBox()

        # icon
        if getattr(sys, 'frozen', False):
            self.setWindowIcon(QtGui.QIcon(os.path.join(sys._MEIPASS, 'replay.ico')))
        else:
            self.setWindowIcon(QtGui.QIcon(PATH.BASE_DIR + "/img/replay.ico"))
        
        # Layout setting
        self.mainLayout = QGridLayout()
        self.central = QWidget()
        self.central.setLayout(self.mainLayout)

        # left pannel
        self.leftWidget = QWidget()
        self.leftGridLayout = QGridLayout()
        self.leftGridLayout.addWidget(self.csvBox, 0, 0)
        self.leftGridLayout.addWidget(self.cfgBox, 1, 0)
        self.leftGridLayout.addWidget(self.infoBox, 2, 0)
        self.leftGridLayout.addWidget(self.clustCtrlBox, 3, 0)  # widget for size adjust

        self.leftWidget.setLayout(self.leftGridLayout)
        self.leftWidget.setFixedWidth(LEFT_WIDGET_SIZE)
        self.mainLayout.addWidget(self.leftWidget, 0, 0)

        # add replay
        self.mainLayout.addWidget(self.replayBox, 1, 0, 1, 2)

        # add GLViewWidget
        self.mainLayout.addWidget(self.gl_view.plot_3d , 0, 1)

        # adjust gl_view size with column stretch
        self.mainLayout.setColumnStretch(0, 1)
        self.mainLayout.setColumnStretch(1, 5)

        # window size setting
        self.setMinimumWidth(MIN_WINDOW_WIDTH)
        self.setMinimumHeight(MIN_WINDOW_HEIGHT)
        self.resize(INIT_WINDOW_WIDTH, INIT_WINDOW_HEIGHT)

        self.cfgBox.setFixedHeight(CFG_BOX_HEIGHT)
        self.csvBox.setFixedHeight(CSV_BOX_HEIGHT)
        self.infoBox.setFixedHeight(INFO_BOX_HEIGHT)
        self.replayBox.setFixedHeight(REPLAY_BOX_HEIGHT)

        # Shortcut
        self.quitShortCut = QShortcut(QKeySequence("Ctrl+Q"), self) # ctrl+Q to close program
        self.quitShortCut.activated.connect(self.close)
        self.nextShortCut = QShortcut(QKeySequence("Right"), self)
        self.nextShortCut.activated.connect(self.restoreNextFrame)
        self.prevShortCut = QShortcut(QKeySequence("Left"), self)
        self.prevShortCut.activated.connect(self.restorePreviousFrame)
        self.jumpStartShortCut = QShortcut(QKeySequence("Home"), self)
        self.jumpStartShortCut.activated.connect(self.jumpToStartFrame)
        self.jumpEndShortCut = QShortcut(QKeySequence("End"), self)
        self.jumpEndShortCut.activated.connect(self.jumpToEndFrame)
        self.startShortCut = QShortcut(QKeySequence("Space"), self)
        self.startShortCut.activated.connect(self.toggleReplay)

        # INI 읽기 성공 시 data load 수행
        self.parseCfg(self.filenameCfg.text())
        self.csvToDict(self.filenameCsv.text())
        self.sliderRangeSet()

        self.setCentralWidget(self.central)
        self.setWindowTitle(title)

        self.makeEllipsoids()

    def initCsvBox(self):
        # outter box
        self.csvBox = QGroupBox(GRP_BOX_CSV)
        self.csvLayout = QGridLayout()
        self.csvBox.setLayout(self.csvLayout)

        # inner box
        self.filenameCsv = QLineEdit(self.csv_path)
        self.filenameCsv.setReadOnly(True)
        self.csvLayout.addWidget(self.filenameCsv, 0, 0)

        self.selectCsvBtn = QPushButton(SELECT_CSV)
        self.selectCsvBtn.setFixedWidth(100)
        self.csvLayout.addWidget(self.selectCsvBtn, 0, 1)

        # signal connection
        self.selectCsvBtn.clicked.connect(self.selectCsv)

    def initCfgBox(self):
        # outter box
        self.cfgBox = QGroupBox(GRP_BOX_CFG)
        self.cfgLayout = QGridLayout()
        self.cfgBox.setLayout(self.cfgLayout)

        # inner box
        self.filenameCfg = QLineEdit(self.cfg_path)
        self.filenameCfg.setReadOnly(True)
        self.cfgLayout.addWidget(self.filenameCfg, 0, 0)

        self.selectCfgBtn = QPushButton(SELECT_CFG)
        self.selectCfgBtn.setFixedWidth(100)
        self.cfgLayout.addWidget(self.selectCfgBtn, 0, 1)

        # signal connection
        self.selectCfgBtn.clicked.connect(self.selectCfg)

    def initInfoBox(self):
        # outer box
        self.infoBox = QGroupBox(GRP_BOX_INFO)
        self.infoLayout = QGridLayout()
        self.infoBox.setLayout(self.infoLayout)

        # inner box
        self.totalFrameLabel = QLabel(INFO_TOTAL_FRAME + str(self.totalFrame))
        self.frameNumLabel = QLabel(INFO_FRAME_NUM + str(self.currentFrame))
        self.pointCntLabel = QLabel(INFO_POINT_NUM + str(self.pointCnt))
        self.realFrameLabel = QLabel(INFO_REAL_FRAME + str(self.realFrameNum))

        self.infoLayout.addWidget(self.totalFrameLabel, 0, 0)
        self.infoLayout.addWidget(self.frameNumLabel, 1, 0)
        self.infoLayout.addWidget(self.pointCntLabel, 2, 0)
        self.infoLayout.addWidget(self.realFrameLabel, 3, 0)

    def initReplayBox(self):
        # outer box
        self.replayBox = QWidget()
        self.replayLayout = QGridLayout()
        self.replayBox.setLayout(self.replayLayout)

        # inner box
        self.timelineSlider = QSlider(Qt.Horizontal)
        self.timelineSlider.setMinimum(0)
        self.timelineSlider.setRange(0, self.totalFrame)
        self.timelineSlider.setValue(0)

        self.timelineSlider.setFixedHeight(40)
        self.timelineSlider.setTickPosition(QSlider.TicksBelow)
        self.timelineSlider.setToolTip("Timeline indicator")

        self.timelineSlider.valueChanged.connect(self.sliderChanged)

        self.controlBox = QWidget()
        self.controlLayout = QGridLayout()
        self.controlBox.setLayout(self.controlLayout)
        self.controlBox.setFixedWidth(CONTROL_BOX_WIDTH)

        # control box
        self.ctrlWidget = QWidget()
        self.ctrlLayout = QGridLayout()
        self.ctrlWidget.setLayout(self.ctrlLayout)

        self.frameBtnWidget = QWidget()
        self.frameBtnLayout = QGridLayout()
        self.frameBtnWidget.setLayout(self.frameBtnLayout)

        self.speedCtrlWidget = QWidget()
        self.speedCtrlLayout = QGridLayout()
        self.speedCtrlWidget.setLayout(self.speedCtrlLayout)

        self.playBtn = QPushButton(REPLAY_START_BTN)
        self.playBtn.setFixedSize(PLAY_BTN_SIZE, PLAY_BTN_SIZE)
        self.playBtn.clicked.connect(self.toggleReplay)

        self.nextBtn = QPushButton(REPLAY_NEXT_BTN)
        self.nextBtn.setFixedSize(SIDE_BTN_SIZE, SIDE_BTN_SIZE)
        self.nextBtn.clicked.connect(self.restoreNextFrame)

        self.prevBtn = QPushButton(REPLAY_PREV_BTN)
        self.prevBtn.setFixedSize(SIDE_BTN_SIZE, SIDE_BTN_SIZE)
        self.prevBtn.clicked.connect(self.restorePreviousFrame)

        self.toStartBtn = QPushButton(REPLAY_TO_START_BTN)
        self.toStartBtn.setFixedSize(SIDE_BTN_SIZE, SIDE_BTN_SIZE)
        self.toStartBtn.clicked.connect(self.jumpToStartFrame)

        self.toEndBtn = QPushButton(REPLAY_TO_END_BTN)
        self.toEndBtn.setFixedSize(SIDE_BTN_SIZE, SIDE_BTN_SIZE)
        self.toEndBtn.clicked.connect(self.jumpToEndFrame)

        self.frameSetWidget = QWidget()
        self.frameSetLayout = QGridLayout()
        self.frameSetWidget.setLayout(self.frameSetLayout)

        self.frameSetLabel = QLabel(FRAME_SET_MSG + str(self.currentFrame) + FRAME_TO_MSG)
        self.frameInput = QLineEdit("0")
        self.frameSubmitBtn = QPushButton(FRAME_MOVE_MSG)
        self.frameSubmitBtn.setFixedWidth(MINI_BTN_WIDTH)
        self.frameSubmitBtn.clicked.connect(self.jumpToInputFrame)

        self.speedCtrlLabel = QLabel(PLAY_SPEED_MSG)
        self.speedCtrlInput = QLineEdit(str(self.playSpeedMultiplier))
        self.speedCtrlSetBtn = QPushButton(PLAY_SPEED_SET_MSG)
        self.speedCtrlSetBtn.setFixedWidth(MINI_BTN_WIDTH)
        self.speedCtrlSetBtn.clicked.connect(self.setPlaySpeed)

        # widget add
        self.ctrlLayout.addWidget(self.speedCtrlWidget, 0, 0, Qt.AlignLeft)
        self.ctrlLayout.addWidget(self.frameBtnWidget, 0, 1, Qt.AlignCenter)
        self.ctrlLayout.addWidget(self.frameSetWidget, 0, 2, Qt.AlignRight)

        self.frameBtnLayout.addWidget(self.toStartBtn, 0, 0)
        self.frameBtnLayout.addWidget(self.prevBtn, 0, 1)
        self.frameBtnLayout.addWidget(self.playBtn, 0, 2)
        self.frameBtnLayout.addWidget(self.nextBtn, 0, 3)
        self.frameBtnLayout.addWidget(self.toEndBtn, 0, 4)

        self.replayLayout.addWidget(self.timelineSlider, 0, 0)
        self.replayLayout.addWidget(self.ctrlWidget, 1, 0)

        self.frameSetLayout.addWidget(self.frameSetLabel, 0, 0)
        self.frameSetLayout.addWidget(self.frameInput, 0, 1)
        self.frameSetLayout.addWidget(self.frameSubmitBtn, 0, 2)

        self.speedCtrlLayout.addWidget(self.speedCtrlLabel, 0, 0)
        self.speedCtrlLayout.addWidget(self.speedCtrlInput, 0, 1)
        self.speedCtrlLayout.addWidget(self.speedCtrlSetBtn, 0, 2)

    def initClustCtrlBox(self):
        CLST_CTRL_BOX_MSG = "Cluster Control"
        CLST_CTRL_L1_MSG = "Merge"
        CLST_CTRL_R1_MSG = "Save"
        CLST_CTRL_L2_MSG = "Change Cluster"
        CLST_CTRL_R2_MSG = "Recover"
        COLOR_BTN_HEIGHT = 80
        COLOR_BTN_COL_CNT = 3
        self.clustCtrlBox = QGroupBox(CLST_CTRL_BOX_MSG)
        self.clustCtrlLayout = QGridLayout()
        self.clustCtrlBox.setLayout(self.clustCtrlLayout)
        
        self.clustCtrlBtnL1 = QPushButton(CLST_CTRL_L1_MSG)
        self.clustCtrlBtnR1 = QPushButton(CLST_CTRL_R1_MSG)
        self.clustCtrlBtnL2 = QPushButton(CLST_CTRL_L2_MSG)
        self.clustCtrlBtnR2 = QPushButton(CLST_CTRL_R2_MSG)

        self.clustCtrlBtnL1.clicked.connect(self.mergeCluster)
        self.clustCtrlBtnR1.clicked.connect(self.saveClusterChanged)
        self.clustCtrlBtnL2.clicked.connect(self.changeCluster)
        self.clustCtrlBtnR2.clicked.connect(self.recoverClusterChanged)

        self.clustCtrlScroll = QScrollArea()
        self.clustCtrlScroll.setWidgetResizable(True)
        self.colorBtnContainer = QWidget()
        self.clustCtrlScroll.setWidget(self.colorBtnContainer)
        self.colorBtnLayout = QGridLayout()
        self.colorBtnContainer.setLayout(self.colorBtnLayout)

        self.colorBtnList = []
        for idx in range(self.color_cnt):
            self.colorBtnList.append(QPushButton(str(idx)))
        for idx, btn in enumerate(self.colorBtnList):
            btn.setFixedHeight(COLOR_BTN_HEIGHT)
            btn.setCheckable(True)
            self.colorBtnLayout.addWidget(btn, idx / COLOR_BTN_COL_CNT, idx % COLOR_BTN_COL_CNT)
            btn.clicked.connect(partial(self.colorBtnClicked,btn, idx))

        self.clustCtrlLayout.addWidget(self.clustCtrlBtnL1, 0, 0)
        self.clustCtrlLayout.addWidget(self.clustCtrlBtnR1, 0, 1)
        self.clustCtrlLayout.addWidget(self.clustCtrlBtnL2, 1, 0)
        self.clustCtrlLayout.addWidget(self.clustCtrlBtnR2, 1, 1)
        self.clustCtrlLayout.addWidget(self.clustCtrlScroll, 2, 0, 1, 2)

    # read & control file
    def selectCfg(self):
        fname = self.selectCfgFile()
        if fname == "":
            return
        try:
            self.parseCfg(fname)
            self.filenameCfg.setText(fname)
        except Exception as e:
            self.fileSelectionWarn(e)
    
    def selectCsv(self):
        fname = self.selectCsvFile()
        if fname == "":
            return
        try:
            if not self.csvToDict(fname):
                self.fileSelectionWarn("csv format not supported")
                return
            self.filenameCsv.setText(fname)
            self.sliderRangeSet()
            self.updateFrame()
        except Exception as e:
            self.fileSelectionWarn(e)
    
    def fileSelectionWarn(self, e: Exception):
        self.warn = QMessageBox.warning(self, "File Selection Error", repr(e))
    
    def selectCfgFile(self):
        try:
            cfg_dir = PATH.BASE_DIR
            path = self.filenameCfg.text()
            if path != "":
                cfg_dir = os.path.dirname(path)
                if not os.path.exists(cfg_dir):
                    cfg_dir = ""
        except:
            cfg_dir = ""

        fname = QFileDialog.getOpenFileName(caption="Open .cfg File", dir=cfg_dir, filter="cfg(*.cfg)")
        return fname[0]
    
    def selectCsvFile(self):
        try:
            csv_dir = PATH.BASE_DIR
            path = self.filenameCsv.text()
            if path != "":
                csv_dir = os.path.dirname(path)
                if not os.path.exists(csv_dir):
                    csv_dir = ""
        except:
            csv_dir = ""

        fname = QFileDialog.getOpenFileName(caption="Open .csv File", dir=csv_dir, filter="csv(*.csv)")
        return fname[0]
    
    def parseCfg(self, fname):
        if fname == "":
            return
        
        with open(fname, "r") as cfg_file:
            cfg_lines = cfg_file.readlines()

        # read height and frame interval info
        for line in cfg_lines:
            args = line.split()
            if len(args) > 0:
                if args[0] == "boundaryBox":
                    if len(args) < 7:
                        print("CFG_ERROR : SceneryParam/boundaryBox had fewer arguments than expected")
                    else:
                        self.gl_view.parseBoundaryBox(args)
                elif args[0] == "frameCfg":
                    if len(args) < 4:
                        print("CFG_ERROR : frameCfg had fewer arguments than expected")
                    else:
                        self.originalFrameTime = float(args[5])
                        self.frameTime = self.originalFrameTime / self.playSpeedMultiplier
                elif args[0] == "sensorPosition":
                        if len(args) < 4:
                            print("CFG_ERROR : sensorPosition had fewer arguments than expected")
                        else:
                            self.gl_view.parseSensorPosition(args)

    def csvToDict(self, fname):
        if fname == "":
            return True
        
        self.originalDictList = []
        self.csvMetaData = []
        frameCnt = 0
        prevFrame = -1
        pointCnt = 0
        startFlag = False
        required_col = ['frameNum', 'pointNum', 'Doppler', 'SNR', 'xPos', 'yPos', 'zPos', 'cluster', 'global_cluster']

        with open(fname, "r", encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            # column check
            csv_col = csv_reader.fieldnames
            for col in required_col:
                if col not in csv_col:
                    self.filenameCsv.setText("")
                    self.firstFrameNum = -1
                    return False

            for row in csv_reader:
                rowDict = dict(row)
                curFrame = int(rowDict['frameNum'])
                if startFlag == False:
                    startFlag = True
                    prevFrame = curFrame
                    pointCnt = 1
                elif curFrame != prevFrame:
                    # save info
                    self.csvMetaData.append([prevFrame, pointCnt])

                    # update info
                    prevFrame = curFrame
                    frameCnt += 1
                    pointCnt = 1
                else:
                    pointCnt += 1

                self.originalDictList.append(rowDict)
            if pointCnt > 0:
                frameCnt += 1
                # save info
                self.csvMetaData.append([curFrame, pointCnt])

            self.revisedDictList = copy.deepcopy(self.originalDictList)
            self.firstFrameNum = self.originalDictList[0]['frameNum']
            # info update
            self.totalFrame = frameCnt
            self.totalFrameLabel.setText(INFO_TOTAL_FRAME + str(self.totalFrame))
        
        self.curFilePath = fname
        return True
    
    def checkCurFrame(self, frameNum):
        self.curFrameCluster.clear()

        toPlotnum = 0
        toPlot = []
        pointColors = []
        xPosList = [[] for _ in range(self.color_cnt)]
        yPosList = [[] for _ in range(self.color_cnt)]
        zPosList = [[] for _ in range(self.color_cnt)]

        for dict in self.revisedDictList:
            if int(dict['frameNum']) == frameNum:
                toPlotnum += 1
                toPlot.append([float(dict['xPos']), float(dict['yPos']), float(dict['zPos'])])
                clust_idx = int(float(dict['global_cluster']))
                if 0 <= clust_idx:
                    color_idx = clust_idx % self.color_cnt
                    pointColors.append(self.colors_qcolor[color_idx])
                    self.curFrameCluster.add(clust_idx)
                    xPosList[color_idx].append(float(dict['xPos']))
                    yPosList[color_idx].append(float(dict['yPos']))
                    zPosList[color_idx].append(float(dict['zPos']))
                else:
                    pointColors.append(self.default_qcolor)
        return toPlotnum, toPlot, pointColors, xPosList, yPosList, zPosList

    # graphics & display
    def displayGraphics(self, frameNum):
        # if theres nothing to print, frameNum set to -1
        if float(frameNum) < 0:
            return
        
        # reset highlighted cluster
        for e in self.gl_view.ellipsoids:
            if (e.visible()):
                e.hide()
        self.gl_view.scatter.setVisible(False)
        toPlotnum, toPlot, pointColors, self.xPosList, self.yPosList, self.zPosList = self.checkCurFrame(frameNum)

        size = [5] * toPlotnum
        nptoPlot = np.array(toPlot)
        nppointColors = np.array([pg.glColor(c) for c in pointColors], dtype=np.float32)
        npsize = np.array(size)
        self.gl_view.scatter.setData(pos=nptoPlot, color=nppointColors, size=npsize)
        self.gl_view.scatter.setVisible(True)

    def makeEllipsoids(self):
        for _ in range(self.color_cnt * 3):    # x, y, z
            mesh = pg.opengl.GLLinePlotItem()
            mesh.setVisible(False)
            self.gl_view.plot_3d.addItem(mesh)
            self.gl_view.ellipsoids.append(mesh)
    
    def highlightCluster(self, radius=0.2, segments=50):
        theta = np.linspace(0, 2 * np.pi, segments)
        for e in self.gl_view.ellipsoids:
            if (e.visible()):
                e.hide()
        
        for idx in self.selectedCluster:
            num = int(self.colorBtnList[idx].text()) % self.color_cnt
            xMean = np.mean(self.xPosList[num])
            yMean = np.mean(self.yPosList[num])
            zMean = np.mean(self.zPosList[num])
            xFirst = xMean + radius * np.cos(theta)
            yFirst = yMean + radius * np.sin(theta)
            zFirst = zMean + np.zeros_like(xFirst)
            firstPoints = np.column_stack((xFirst, yFirst, zFirst))
            xSec = xMean + radius * np.cos(theta)
            ySec = yMean + np.zeros_like(xSec)
            zSec = zMean + radius * np.sin(theta)
            secPoints = np.column_stack((xSec, ySec, zSec))
            yTh = yMean + radius * np.cos(theta)
            xTh = xMean + np.zeros_like(yTh)
            zTh = zMean + radius * np.sin(theta)
            thPoints = np.column_stack((xTh, yTh, zTh))
            colors = [(self.colors_rgba[num][0] / 255, self.colors_rgba[num][1] / 255, self.colors_rgba[num][2] / 255, self.colors_rgba[num][3])] * firstPoints.shape[0]
            npColors = np.array(colors)
            self.gl_view.ellipsoids[num * 3].setData(pos=firstPoints, color=npColors, width=2, antialias=True, mode='line_strip')
            self.gl_view.ellipsoids[num * 3].setVisible(True)
            self.gl_view.ellipsoids[num * 3 + 1].setData(pos=secPoints, color=npColors, width=2, antialias=True, mode='line_strip')
            self.gl_view.ellipsoids[num * 3 + 1].setVisible(True)
            self.gl_view.ellipsoids[num * 3 + 2].setData(pos=thPoints, color=npColors, width=2, antialias=True, mode='line_strip')
            self.gl_view.ellipsoids[num * 3 + 2].setVisible(True)

    def updateFrameInfo(self):
        self.realFrameNum = self.csvMetaData[self.currentFrame - 1][CSV_META.FRAME_NUM]
        self.pointCnt = self.csvMetaData[self.currentFrame - 1][CSV_META.POINT_CNT]

        self.frameNumLabel.setText(INFO_FRAME_NUM + str(self.currentFrame))
        self.pointCntLabel.setText(INFO_POINT_NUM + str(self.pointCnt))
        self.realFrameLabel.setText(INFO_REAL_FRAME + str(self.realFrameNum))

    # button connected function
    def toggleReplay(self):
        current_text = self.playBtn.text()
        if current_text == REPLAY_START_BTN:
            self.startPlay()
        else:
            self.stopPlay()
        return
    
    def startPlay(self):
        if len(self.revisedDictList) == 0:
            self.isPlaying = False
            return
        
        # start when it reached end frame, start from begin
        if self.currentFrame >= self.totalFrame:
            self.currentFrame = 1

        self.playBtn.setText(REPLAY_PAUSE_BTN)
        self.isPlaying = True
        self.displayFrameTimer()

    def stopPlay(self):
        self.playBtn.setText(REPLAY_START_BTN)
        self.isPlaying = False

    def updateFrame(self):
        self.updateFrameInfo()
        self.displayGraphics(self.realFrameNum)
        self.timelineSlider.blockSignals(True)
        self.timelineSlider.setValue(self.currentFrame)
        self.timelineSlider.blockSignals(False)
        self.frameSetLabel.setText(FRAME_SET_MSG + str(self.currentFrame) + FRAME_TO_MSG)
        self.reloadColorBtn()

    def displayFrameTimer(self):
        if self.isPlaying == False:
            self.stopPlay()
            return
        if self.currentFrame >= self.totalFrame:
            self.stopPlay()
            return
        self.frameTimer.start(self.frameTime)
        self.currentFrame += 1
        self.updateFrame()
    
    def restorePreviousFrame(self):
        if self.isPlaying:
            self.stopPlay()
        if self.currentFrame <= 1:
            return
        
        self.currentFrame -= 1
        self.updateFrame()
    
    def restoreNextFrame(self):
        if self.isPlaying:
            self.stopPlay()
        if self.currentFrame >= self.totalFrame:
            return
        
        self.currentFrame += 1
        self.updateFrame()

    def jumpToStartFrame(self):
        if self.isPlaying:
            self.stopPlay()
        self.currentFrame = 1
        self.updateFrame()

    def jumpToEndFrame(self):
        if self.isPlaying:
            self.stopPlay()
        self.currentFrame = self.totalFrame
        self.updateFrame()

    def jumpToInputFrame(self):
        if self.isPlaying:
            self.stopPlay()
        self.currentFrame = self.getFrameToJump(self.frameInput.text())
        self.currentFrame = int(self.frameInput.text())
        self.updateFrame()
    
    def getFrameToJump(self, frameNum):
        if frameNum < 1:
            frameNum = 1
        elif frameNum > self.totalFrame:
            frameNum = self.totalFrame
        return frameNum
    
    def setPlaySpeed(self):
        try:
            self.playSpeedMultiplier = float(self.speedCtrlInput.text())
            self.frameTime = self.originalFrameTime / self.playSpeedMultiplier
        except:
            self.speedCtrlInput.setText("1.0")
            self.frameTime = self.originalFrameTime
    
    # slider functions
    def sliderRangeSet(self):
        self.timelineSlider.setRange(1, self.totalFrame)
        self.timelineSlider.setValue(1)

    def sliderChanged(self):
        self.currentFrame = self.timelineSlider.value()
        self.updateFrame()

    # cluster control functions
    def mergeCluster(self):
        if len(self.selectedCluster) < 2:
            return
        
        clust_list = list(self.curFrameCluster)
        first_idx = next(iter(self.selectedCluster))
        merged_idx = clust_list[first_idx]

        idx_to_conv = []
        for idx in self.selectedCluster:
            if idx != first_idx:
                idx_to_conv.append(clust_list[idx])

        for dict in self.revisedDictList:
            clust_num = int(float(dict['global_cluster']))
            if clust_num in idx_to_conv:
                dict['global_cluster'] = str(merged_idx)

        self.updateFrame()
        return

    def changeCluster(self):
        if len(self.selectedCluster) < 1:
            return
        
        clust_list = list(self.curFrameCluster)
        idx_to_conv = []
        for idx in self.selectedCluster:
            idx_to_conv.append(clust_list[idx])

        idx_dialog = IndexSetDialog(self)
        if idx_dialog.exec_():
            target_idx = idx_dialog.get_input_idx()
            cur_flag = idx_dialog.get_checkbox_flag()
        else:
            return
        
        if target_idx < -1:
            print("target index out of range")

        if cur_flag:
            for dict in self.revisedDictList:
                frameNum = int(float(dict['frameNum']))
                if frameNum == self.realFrameNum:
                    clust_num = int(float(dict['global_cluster']))
                    if clust_num in idx_to_conv:
                        dict['global_cluster'] = str(target_idx)
        else:
            for dict in self.revisedDictList:
                clust_num = int(float(dict['global_cluster']))
                if clust_num in idx_to_conv:
                    dict['global_cluster'] = str(target_idx)

        self.updateFrame()
        return
    
    def saveClusterChanged(self):
        # save to file
        self.saveCsv()
        self.originalDictList = copy.deepcopy(self.revisedDictList)
    
    def recoverClusterChanged(self):
        self.revisedDictList = copy.deepcopy(self.originalDictList)
        self.updateFrame()
    
    def saveCsv(self):
        if self.revisedDictList:
            fieldnames = self.revisedDictList[0].keys()
            with open(self.curFilePath, mode="w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.revisedDictList)

    # color button
    def colorBtnClicked(self, btn: QPushButton, idx: int):
        pushed = btn.isChecked()
        if pushed:
            self.selectedCluster.add(idx)
        else:
            self.selectedCluster.remove(idx)
        self.highlightCluster()
    
    def reloadColorBtn(self):
        # reset btn
        for idx in self.selectedCluster:
            self.colorBtnList[idx].setChecked(False)

        clust_cnt = len(self.curFrameCluster)
        clust_list = list(self.curFrameCluster)
        for idx in range(clust_cnt):
            self.colorBtnList[idx].show()
            self.colorBtnList[idx].setText(str(clust_list[idx]))
            styleSheet = self.getBtnColorStyleSheet(self.colors_qcolor[clust_list[idx] % self.color_cnt])
            self.colorBtnList[idx].setStyleSheet(styleSheet)
        for idx in range(clust_cnt, self.color_cnt):
            self.colorBtnList[idx].hide()

        self.selectedCluster.clear()

    # ini function
    def ini_get_cfg_path(self, parser: ConfigParser):
        cfg_path = parser.get(INI.PATH_SECTION, INI.CFG, fallback="")
        if not os.path.exists(cfg_path):
            cfg_path = ""
        return cfg_path
    
    def ini_get_csv_path(self, parser: ConfigParser):
        csv_path = parser.get(INI.PATH_SECTION, INI.CSV, fallback="")
        if not os.path.exists(csv_path):
            csv_path = ""
        return csv_path

    def ini_write(self, parser: ConfigParser):
        with open(PATH.INI_PATH, "w", encoding="UTF-8") as ini_file:
            parser.write(ini_file)

    def ini_create(self, parser: ConfigParser):
        if INI.PATH_SECTION not in parser:
            parser[INI.PATH_SECTION] = {
                INI.CSV : "",
                INI.CFG : "",
            }

        self.ini_write(parser)

    def ini_save(self, parser: ConfigParser):
        parser[INI.PATH_SECTION][INI.CSV] = self.filenameCsv.text()
        parser[INI.PATH_SECTION][INI.CFG] = self.filenameCfg.text()

        self.ini_write(parser)

    # color
    def getBtnColorStyleSheet(self, color: QColor):
        r = color.red()
        g = color.green()
        b = color.blue()
        a = color.alpha()
        ha = a / 2
        stylesheet = f"""
            QPushButton {{
                background-color: rgba({r}, {g}, {b}, {ha});
                color: black;
                border: 1px solid rgba(0, 0, 0, 10);
                border-radius: 5px;
                padding: 2px;
            }}
            QPushButton:hover {{
                background-color: rgba({r}, {g}, {b}, {ha});
            }}
            QPushButton:pressed {{
                background-color: rgba({r}, {g}, {b}, {ha});
            }}
            QPushButton:checked {{
                background-color: rgba({r}, {g}, {b}, {a});
            }}
        """
        return stylesheet

    def closeEvent(self, event):
        event.accept()
        self.ini_save(self.iniParser)
        QApplication.quit()

class IndexSetDialog(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle(IDX_SET_DIALOG_TITLE)
        self.setFixedSize(IDX_SET_DIALOG_WIDTH, IDX_SET_DIALOG_HEIGHT)

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.label = QLabel(IDX_SET_DIALOG_MSG)
        self.layout.addWidget(self.label, 0, 0, Qt.AlignCenter)

        self.idxInput = QLineEdit()
        self.idxInput.setFixedWidth(IDX_SET_INPUT_WIDTH)
        self.idxInput.setValidator(QIntValidator())
        self.layout.addWidget(self.idxInput, 0, 1, Qt.AlignCenter)

        self.btnBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.btnBox.accepted.connect(self.accept)
        self.btnBox.rejected.connect(self.reject)
        self.layout.addWidget(self.btnBox, 1, 0, 1, 2, Qt.AlignRight)

        IDX_SET_CHECKBOX_MSG = "Current Frame Only"
        self.checkBox = QCheckBox(IDX_SET_CHECKBOX_MSG)
        self.layout.addWidget(self.checkBox, 2, 0, 1, 1, Qt.AlignLeft)

    def get_input_idx(self):
        return int(self.idxInput.text())
    
    def get_checkbox_flag(self):
        return self.checkBox.isChecked()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window(title="Cloud Point Labeling Tool")
    main.show()
    main.displayGraphics(0 + int(main.firstFrameNum))
    sys.exit(app.exec_())
