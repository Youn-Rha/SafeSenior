# General Library Imports
# PyQt Imports
# Local Imports
# Logger
# # Different methods to color the points 
COLOR_MODE_SNR = 'SNR'
COLOR_MODE_HEIGHT = 'Height'
COLOR_MODE_DOPPLER = 'Doppler'
COLOR_MODE_TRACK = 'Associated Track'

MAX_PERSISTENT_FRAMES = 30

from collections import deque
import numpy as np
import time
import string

from PySide2.QtCore import Qt, QThread
from PySide2.QtGui import QPixmap, QFont
import pyqtgraph.opengl as gl
import pyqtgraph as pg
from PySide2.QtWidgets import QGroupBox, QGridLayout, QLabel, QWidget, QVBoxLayout, QTabWidget, QComboBox, QCheckBox, QSlider, QFormLayout

from Common_Tabs.plot_3d import Plot3D
from Common_Tabs.plot_1d import Plot1D
from Demo_Classes.Helper_Classes.fall_detection import *
from demo_defines import *
from graph_utilities import get_trackColors, eulerRot
from gl_text import GLTextItem

from gui_threads import updateQTTargetThread3D
from gui_common import TAG_HISTORY_LEN

import logging

log = logging.getLogger(__name__)


class PeopleTracking(Plot3D, Plot1D):
    def __init__(self):
        Plot3D.__init__(self)
        Plot1D.__init__(self)
        self.fallDetection = FallDetection()
        self.tabs = None
        self.cumulativeCloud = None
        self.colorGradient = pg.GradientWidget(orientation='right')
        self.colorGradient.restoreState({'ticks': [ (1, (255, 0, 0, 255)), (0, (131, 238, 255, 255))], 'mode': 'hsv'})
        self.colorGradient.setVisible(False)
        self.maxTracks = int(5) # default to 5 tracks
        self.trackColorMap = get_trackColors(self.maxTracks)
        self.state = 3

        self.man_plt = []

    def setupGUI(self, gridLayout, demoTabs, device):
        # Init setup pane on left hand side
        statBox = self.initStatsPane()
        gridLayout.addWidget(statBox,2,0,1,1)

        demoGroupBox = self.initPlotControlPane()
        gridLayout.addWidget(demoGroupBox,3,0,1,1)

        fallDetectionOptionsBox = self.initFallDetectPane()
        gridLayout.addWidget(fallDetectionOptionsBox, 4,0,1,1)

        demoTabs.addTab(self.plot_3d, '3D Plot')
        demoTabs.addTab(self.rangePlot, 'Range Plot')
        self.device = device
        self.tabs = demoTabs

    def updateGraph(self, outputDict, busy=False):
        self.plotStart = int(round(time.time()*1000))
        self.updatePointCloud(outputDict)

        self.cumulativeCloud = None

        # Track indexes on 6843 are delayed a frame. So, delay showing the current points by 1 frame for 6843
        if ('frameNum' in outputDict and outputDict['frameNum'] > 1 and len(self.previousClouds[:-1]) > 0 and DEVICE_DEMO_DICT[self.device]["isxWRx843"]):
            # For all the previous point clouds (except the most recent, whose tracks are being computed mid-frame)
            for frame in range(len(self.previousClouds[:-1])):
                # if it's not empty
                if(len(self.previousClouds[frame]) > 0):
                    # if it's the first member, assign it equal
                    if(self.cumulativeCloud is None):
                        self.cumulativeCloud = self.previousClouds[frame]
                    # if it's not the first member, concatinate it
                    else:
                        self.cumulativeCloud = np.concatenate((self.cumulativeCloud, self.previousClouds[frame]),axis=0)
        elif (len(self.previousClouds) > 0):
            # For all the previous point clouds, including the current frame's
            for frame in range(len(self.previousClouds[:])):
                # if it's not empty
                if(len(self.previousClouds[frame]) > 0):
                    # if it's the first member, assign it equal
                    if(self.cumulativeCloud is None):
                        self.cumulativeCloud = self.previousClouds[frame]
                    # if it's not the first member, concatinate it
                    else:
                        self.cumulativeCloud = np.concatenate((self.cumulativeCloud, self.previousClouds[frame]),axis=0)

        if ('numDetectedPoints' in outputDict):
            self.numPointsDisplay.setText('Points: '+ str(outputDict['numDetectedPoints']))

        if ('numDetectedTracks' in outputDict):
            self.numTargetsDisplay.setText('Targets: '+ str(outputDict['numDetectedTracks']))

        # Tracks
        for cstr in self.coordStr:
            cstr.setVisible(False)

        # Plot
        if (self.tabs.currentWidget() == self.plot_3d):
            try:
                if ('trackData' in outputDict):
                    tracks = outputDict['trackData']
                    for i in range(outputDict['numDetectedTracks']):
                        rotX, rotY, rotZ = eulerRot(tracks[i,1], tracks[i,2], tracks[i,3], self.elev_tilt, self.az_tilt)
                        tracks[i,1] = rotX
                        tracks[i,2] = rotY
                        tracks[i,3] = rotZ
                        tracks[i,3] = tracks[i,3] + self.sensorHeight

                    # If there are heights to display
                    if ('heightData' in outputDict):
                        if (len(outputDict['heightData']) != len(outputDict['trackData'])):
                            log.warning("WARNING: number of heights does not match number of tracks")

                        # For each height heights for current tracks
                        for height in outputDict['heightData']:
                            # Find track with correct TID
                            for track in outputDict['trackData']:
                                # Found correct track
                                if (int(track[0]) == int(height[0])):
                                    tid = int(height[0])
                                    height_str = 'tid : ' + str(height[0]) + ', height : ' + str(round(height[1], 2)) + ' m'
                                    # If this track was computed to have fallen, display it on the screen
                                    if(self.displayFallDet.checkState() == 2):
                                        # Compute the fall detection results for each object
                                        # is main is busy, skip inference
                                        # if busy == True:
                                        #     fallDetectionDisplayResults = self.old_state
                                        # else:
                                        fallDetectionDisplayResults = self.fallDetection.step(outputDict)
                                        try:
                                            tid = fallDetectionDisplayResults[0]
                                            self.update_fall_status(fallDetectionDisplayResults, tid, tracks)
                                            self.state = fallDetectionDisplayResults[1]
                                        except TypeError:
                                            pass

                                            # update state cache
                                            # self.old_state = fallDetectionDisplayResults
                                        # try:
                                        #     if (fallDetectionDisplayResults[tid] == 0): 
                                        #         height_str = height_str + " FALL DETECTED"
                                        # except TypeError:
                                        #     pass

                                    # TODO
                                    self.coordStr[tid].setText(height_str)
                                    self.coordStr[tid].setX(track[1])
                                    self.coordStr[tid].setY(track[2])
                                    self.coordStr[tid].setZ(track[3])
                                    self.coordStr[tid].setVisible(True)
                                    break
                else:
                    # tracks = None
                    return
            except IndexError:
                pass
            if (self.plotComplete):
                self.plotStart = int(round(time.time()*1000))
                self.plot_3d_thread = updateQTTargetThread3D(self, self.cumulativeCloud, tracks, self.scatter, self.plot_3d, 0, self.ellipsoids, "", colorGradient=self.colorGradient, pointColorMode=self.pointColorMode.currentText(), trackColorMap=self.trackColorMap)
                self.plotComplete = 0
                self.plot_3d_thread.done.connect(lambda: self.graphDone(outputDict))
                self.plot_3d_thread.start(priority=QThread.HighPriority)
        elif (self.tabs.currentWidget() == self.rangePlot):
            self.update1DGraph(outputDict)
            self.graphDone(outputDict)

        if ('frameNum' in outputDict):
            self.frameNumDisplay.setText('Frame: ' + str(outputDict['frameNum']))

    def graphDone(self, outputDict):
        if ('frameNum' in outputDict):
            self.frameNumDisplay.setText('Frame: ' + str(outputDict['frameNum']))

        if ('powerData' in outputDict):
            powerData = outputDict['powerData']
            self.updatePowerNumbers(powerData)

        plotTime = int(round(time.time()*1000)) - self.plotStart
        self.plotTimeDisplay.setText('Plot Time: ' + str(plotTime) + 'ms')
        self.plotComplete = 1

    def updatePowerNumbers(self, powerData):
        if powerData['power1v2'] == 65535:
            self.avgPower.setText('Average Power: N/A')
        else:
            powerStr = str((powerData['power1v2'] \
                + powerData['power1v2RF'] + powerData['power1v8'] + powerData['power3v3']) * 0.1)
            self.avgPower.setText('Average Power: ' + powerStr[:5] + ' mW')

    def initStatsPane(self):
        statBox = QGroupBox('Statistics')
        self.frameNumDisplay = QLabel('Frame: 0')
        self.plotTimeDisplay = QLabel('Plot Time: 0 ms')
        self.numPointsDisplay = QLabel('Points: 0')
        self.numTargetsDisplay = QLabel('Targets: 0')
        self.avgPower = QLabel('Average Power: 0 mw')
        self.statsLayout = QVBoxLayout()
        self.statsLayout.addWidget(self.frameNumDisplay)
        self.statsLayout.addWidget(self.plotTimeDisplay)
        self.statsLayout.addWidget(self.numPointsDisplay)
        self.statsLayout.addWidget(self.numTargetsDisplay)
        self.statsLayout.addWidget(self.avgPower)
        statBox.setLayout(self.statsLayout)
        return statBox

    def initPlotControlPane(self):
        plotControlBox = QGroupBox('Plot Controls')
        self.pointColorMode = QComboBox()
        self.pointColorMode.addItems([COLOR_MODE_SNR, COLOR_MODE_HEIGHT, COLOR_MODE_DOPPLER, COLOR_MODE_TRACK])

        self.displayFallDet = QCheckBox('Detect Falls')
        self.snapTo2D = QCheckBox('Snap to 2D')
        self.displayFallDet.stateChanged.connect(self.fallDetDisplayChanged)
        self.persistentFramesInput = QComboBox()
        self.persistentFramesInput.addItems([str(i) for i in range(1, MAX_PERSISTENT_FRAMES + 1)])
        self.persistentFramesInput.setCurrentIndex(self.numPersistentFrames - 1)
        self.persistentFramesInput.currentIndexChanged.connect(self.persistentFramesChanged)
        plotControlLayout = QFormLayout()
        plotControlLayout.addRow("Color Points By:",self.pointColorMode)
        plotControlLayout.addRow("Enable Fall Detection", self.displayFallDet)
        plotControlLayout.addRow("# of Persistent Frames",self.persistentFramesInput)
        plotControlLayout.addRow(self.snapTo2D)
        plotControlBox.setLayout(plotControlLayout)

        return plotControlBox

    def persistentFramesChanged(self, index):
        self.numPersistentFrames = index + 1

    def fallDetDisplayChanged(self, state):
        if state:
            self.fallDetectionOptionsBox.setVisible(True)
            self.left_panel.setVisible(True)
            self.right_panel.setVisible(True)
        else:
            self.fallDetectionOptionsBox.setVisible(False)
            self.left_panel.setVisible(False)
            self.right_panel.setVisible(False)

    def updateFallDetectionSensitivity(self):
        self.fallDetection.setFallSensitivity(((self.fallDetSlider.value() / self.fallDetSlider.maximum()) * 0.4) + 0.4) # Range from 0.4 to 0.8

    def initFallDetectPane(self):
        self.fallDetectionOptionsBox = QGroupBox('Fall Detection for 5 people')
        self.fallDetLayout = QGridLayout(self.fallDetectionOptionsBox)
        self.left_panel = QtWidgets.QWidget()
        self.left_layout = QtWidgets.QVBoxLayout(self.left_panel)
        self.right_panel = QtWidgets.QWidget()
        self.right_layout = QtWidgets.QVBoxLayout(self.right_panel)

        # 패널 리스트 초기화 (5개의 패널 생성)
        self.fall_panels = []
        for i in range(5):
            l_panel = QtWidgets.QLabel(f"사람 {i + 1}")
            l_panel.setStyleSheet("background-color: transparent; border: 1px solid gray; color: black;")
            l_panel.setFixedSize(300, 60)
            l_panel.setAlignment(QtCore.Qt.AlignCenter)
            r_panel = QtWidgets.QLabel(f"")
            r_panel.setStyleSheet("background-color: transparent; border: 1px solid gray; color: black;")
            r_panel.setFixedSize(60, 60)
            r_panel.setAlignment(QtCore.Qt.AlignCenter)
            self.fall_panels.append(r_panel)
            self.left_layout.addWidget(l_panel)
            self.right_layout.addWidget(r_panel)

        self.left_panel.setLayout(self.left_layout)
        self.right_panel.setLayout(self.right_layout)
        
        horizontal_layout = QtWidgets.QHBoxLayout()
        horizontal_layout.addWidget(self.left_panel)
        horizontal_layout.addWidget(self.right_panel)
        self.fallDetLayout.addLayout(horizontal_layout, 3, 3)

        # 패널을 GUI 메인 레이아웃에 추가 (fall_detection 모드일 때만 보이게 설정)
        self.left_panel.setVisible(False)
        self.right_panel.setVisible(False)
        
        if(self.displayFallDet.checkState() == 2):
            self.fallDetectionOptionsBox.setVisible(True)
            self.left_panel.setVisible(True)
            self.right_panel.setVisible(True)
        else:
            self.fallDetectionOptionsBox.setVisible(False)

        return self.fallDetectionOptionsBox
    
    def update_fall_status(self, fall_status: list, tid, tracks):
        if tid > 5 or tid < 0:
            return
        try:
            idx = fall_status[0]
            if idx < 0 or idx > 2:
                return
        except:
            return
        
        panel = self.fall_panels[idx]
        fallChecker = [0] * 5

        try:
            # if fall_status[1] == 0 or fall_status[1] == 2:  # test code
            if fall_status[1] == 0:  # 낙상 감지됨
                panel.setStyleSheet("background-color: red; color: white; border: 1px solid black;")
                fallChecker[tid] = 1
                # 일정 시간 후 초록색으로 변경하는 타이머 설정 (10초 후)
                QtCore.QTimer.singleShot(10000, lambda p=panel: p.setStyleSheet("background-color: transparent; border: 1px solid gray; color: black;"))
                fallChecker[tid] = 0
            else:
                if fallChecker[tid] != 1:
                    panel.setStyleSheet("background-color: green; color: white; border: 1px solid black;")
                    QtCore.QTimer.singleShot(2000, lambda p=panel: p.setStyleSheet("background-color: transparent; border: 1px solid gray; color: black;"))
            # elif tracks[idx]:  # 트랙 감지됨
            #     panel.setStyleSheet("background-color: green; color: white; border: 1px solid black;")
            
            # else:  # 트랙 소멸
            #     panel.setStyleSheet("background-color: transparent; border: 1px solid gray; color: black;")
        except:
            panel.setStyleSheet("background-color: transparent; border: 1px solid gray; color: black;")

    def parseTrackingCfg(self, args):
        self.maxTracks = int(args[4])
        self.updateNumTracksBuffer() # Update the max number of tracks based off the config file
        self.trackColorMap = get_trackColors(self.maxTracks)
        # for m in range(self.maxTracks):
        for m in range(100):
            # Add track gui object
            mesh = gl.GLLinePlotItem()
            mesh.setVisible(False)
            self.plot_3d.addItem(mesh)
            self.ellipsoids.append(mesh)
            # Add track coordinate string
            text = GLTextItem()
            text.setGLViewWidget(self.plot_3d)
            text.setVisible(False)
            self.plot_3d.addItem(text)
            self.coordStr.append(text)
            # Add track classifier label string
            classifierText = GLTextItem()
            classifierText.setGLViewWidget(self.plot_3d)
            classifierText.setVisible(False)
            self.plot_3d.addItem(classifierText)
            self.classifierStr.append(classifierText)

    def updateNumTracksBuffer(self):
        # Use a deque here because the append operation adds items to the back and pops the front
        self.classifierTags = [deque([0] * TAG_HISTORY_LEN, maxlen = TAG_HISTORY_LEN) for i in range(self.maxTracks)]
        self.tracksIDsInPreviousFrame = []
        self.wasTargetHuman = [0 for i in range(self.maxTracks)]
        self.fallDetection = FallDetection(self.maxTracks)