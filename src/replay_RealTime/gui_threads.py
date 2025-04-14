import time
import numpy as np

from PySide2 import QtGui
from PySide2.QtCore import QThread, Signal, QTimer
from PySide2.QtGui import QImage
import pyqtgraph as pg

from graph_utilities import *
import pyqtgraph.opengl as gl

from plot_3d import Plot3D

from macroControl import HEAD_TYPE, HTYPE_CIRCLE_HEAD, HTYPE_BOX_HEAD, NUM_OF_DETECT_PEOPLE
from macroControl import STATE, PATH


POSITION_OFFSET_Z = 0.5

MAX_NUM_TRACKS = 20
MAX_PERSISTENT_FRAMES = 30

SNR_EXPECTED_MIN = 5
SNR_EXPECTED_MAX = 40
SNR_EXPECTED_RANGE = SNR_EXPECTED_MAX - SNR_EXPECTED_MIN
# DOPPLER_EXPECTED_MIN = -30
# DOPPLER_EXPECTED_MAX = 30
# DOPPLER_EXPECTED_RANGE = DOPPLER_EXPECTED_MAX - DOPPLER_EXPECTED_MIN

COLOR_MODE_SNR = 'SNR'
# COLOR_MODE_HEIGHT = 'Height'
# COLOR_MODE_DOPPLER = 'Doppler'
# COLOR_MODE_TRACK = 'Associated Track

LABEL_FRAME = "Frame : "
LABEL_PLT_TIME = "Plot Time : "
LABEL_POINTS = "Points : "
LABEL_TARGETS = "Targets : "

# panel color
PANEL_COLOR_TRANS = 0
PANEL_COLOR_GREEN = 1
PANEL_COLOR_RED = 2

class updateQTTargetThread3D(QThread):
    done = Signal()

    def __init__(self, panels, state, pointCloud, targets, scatter, pcplot: gl.GLViewWidget, numTargets, ellipsoids, coords, panel_color, panel_ticket, colorGradient=None, classifierOut=[], zRange=[-3, 3], pointColorMode="", drawTracks=True, trackColorMap=None, pointBounds={'enabled': False}):
        QThread.__init__(self)
        self.pointCloud = pointCloud
        self.targets = targets
        self.scatter = scatter
        self.pcplot = pcplot
        self.colorArray = ('r','g','b','w')
        self.numTargets = numTargets
        self.ellipsoids = ellipsoids
        self.coordStr = coords
        self.classifierOut = classifierOut
        self.zRange = zRange
        self.colorGradient = colorGradient
        self.pointColorMode = pointColorMode
        self.drawTracks = drawTracks
        self.trackColorMap = trackColorMap
        self.pointBounds = pointBounds
        self.state = state
        self.fall_panels = panels

        self.panel_color = panel_color
        self.panel_ticket = panel_ticket

        self.image = QImage(PATH.BASE_DIR + "/img/people_image_4.png")
        self.image_array = np.array(self.image.convertToFormat(QImage.Format_RGBA8888).bits()).copy().reshape(self.image.height(), self.image.width(), 4)
    
        np.seterr(divide = 'ignore')

        self.head_list = []
        # self.man_plt = par.man_plt
        # self.state = par.state

    def getPointColors(self, i):
        if (self.pointBounds['enabled']) :
            xyz_coords = self.pointCloud[i,0:3]
            if (   xyz_coords[0] < self.pointBounds['minX']
                or xyz_coords[0] > self.pointBounds['maxX']
                or xyz_coords[1] < self.pointBounds['minY']
                or xyz_coords[1] > self.pointBounds['maxY']
                or xyz_coords[2] < self.pointBounds['minZ']
                or xyz_coords[2] > self.pointBounds['maxZ']
                ) :
                return pg.glColor((0,0,0,0))

        # return pg.glColor(color_def(i))
        # Color the points by their SNR
        if (self.pointColorMode == COLOR_MODE_SNR):
            snr = self.pointCloud[i,4]
            # SNR value is out of expected bounds, make it white
            if (snr < SNR_EXPECTED_MIN) or (snr > SNR_EXPECTED_MAX):
                return pg.glColor('w')
            else:
                return pg.glColor(self.colorGradient.getColor((snr-SNR_EXPECTED_MIN)/SNR_EXPECTED_RANGE))


    def update_fall_status(self, state: list, tid):
        if tid >= NUM_OF_DETECT_PEOPLE or tid < 0:
            return
        
        idx = tid
        
        panel = self.fall_panels[idx]

        try:
            if state[idx] == STATE.STATE_FALL or state[idx] == STATE.STATE_LIE_DOWN:  # 낙상 감지됨
                if self.panel_color != PANEL_COLOR_RED:
                    # 낙상 감지 시, 시간 연장 없는 방식으로 구현
                    self.panel_ticket[idx] = STATE.TICKET_RED
                    panel.setStyleSheet("background-color: red; color: white; border: 1px solid black;")
                    self.panel_color[idx] = PANEL_COLOR_RED
            else:
                    if self.panel_color[idx] == PANEL_COLOR_TRANS:
                        self.panel_ticket[idx] = STATE.TICKET_GREEN
                        panel.setStyleSheet("background-color: green; color: white; border: 1px solid black;")
                        self.panel_color[idx] = PANEL_COLOR_GREEN
                    elif self.panel_color[idx] == PANEL_COLOR_GREEN:
                        self.panel_ticket[idx] = STATE.TICKET_GREEN
            # elif tracks[idx]:  # 트랙 감지됨
            #     panel.setStyleSheet("background-color: green; color: white; border: 1px solid black;")
        except:
            panel.setStyleSheet("background-color: transparent; border: 1px solid gray; color: black;")  

    def drawTrack(self, track, trackColor):
        # Get necessary track data
        tid = int(track[0])
        x = track[1]
        y = track[2]
        z = track[3]
        # print(f"ploting on {x} {y} {z}")

        self.track = self.ellipsoids[tid]
        self.track2 = self.ellipsoids[NUM_OF_DETECT_PEOPLE*2-1-tid]

        # self.update_fall_status(self.state, tid)
        if HEAD_TYPE == HTYPE_CIRCLE_HEAD:
            z = z + POSITION_OFFSET_Z
            head = CircleBillboard3D(0, 0, 0, radius=0.15, view= self.pcplot)
            self.head_list.append(head)
            mesh1 = getBoxLinesCoordsCircleHead(x, y, z, track_prediction=self.state[tid])
            if self.state[tid] == 0 or self.state[tid] == 2:
                mesh2 = head.update_orientation() + np.array([x, y - 0.8, z])
            else:
                mesh2 = head.update_orientation() + np.array([x, y, z + 0.8])
            self.track2.setData(pos=mesh2,color=trackColor,width=2,antialias=True,mode='lines')
            # self.pcplot.addItem(self.track2) # useless code
            self.track2.setVisible(True)   
        else:
            mesh1 = getBoxLinesCoordsBoxHead(x, y, z, track_prediction=self.state[tid])
            
        self.track.setData(pos=mesh1,color=trackColor,width=2,antialias=True,mode='lines')
        self.track.setVisible(True)
        # mesh2 = head.return_circle_mesh()
        # head_x, head_y, head_z = create_circle(0.15, center=(x, y, z + 0.8))
        # mesh2 = np.vstack([head_x.flatten(), head_y.flatten(), head_z.flatten()]).T
        # self.pcplot.addItem(track)
        # mesh = getBoxLinesCoords(x,y,z, track[12])
        # self.man_plt.append(self.track)
        # self.man_plt[-1].setVisible(False)

    def drawTrackImage(self, track):
        # Get necessary track data
        tid = int(track[0])
        x = track[1]
        y = track[2]
        z = track[3]
        # print(f"ploting on {x} {y} {z}")

        image_item = gl.GLImageItem(self.image_array)
        image_item.translate(x, y, z)
        self.update_fall_status(self.state, tid)
        
        self.pcplot.addItem(image_item)

    def run(self):

        # Clear all previous targets
        for e in self.ellipsoids:
            if (e.visible()):
                e.hide()
        
        try:
            # Create a list of just X, Y, Z values to be plotted
            if(self.pointCloud is not None):
                toPlot = self.pointCloud[:, 0:3]

                # Determine the size of each point based on its SNR
                with np.errstate(divide='ignore'):
                    size = np.log2(self.pointCloud[:, 4])
                
                # Each color is an array of 4 values, so we need an numPoints*4 size 2d array to hold these values
                pointColors = np.zeros((self.pointCloud.shape[0], 4))

                # Set the color of each point
                for i in range(self.pointCloud.shape[0]):
                    pointColors[i] = self.getPointColors(i)

                # Plot the points
                self.scatter.setData(pos=toPlot, color=pointColors, size=size)
                # Make the points visible 
                self.scatter.setVisible(True)
            else:
                # Make the points invisible if none are detected.
                self.scatter.setVisible(False)
        except:
            # log.error("Unable to draw point cloud, ignoring and continuing execution...")
            pass

        # while self.man_plt:
        #     fig : gl.GLLinePlotItem = self.man_plt.pop()
        #     fig.setVisible(False)
        #     self.pcplot.removeItem(fig)

        # Graph the targets
        try:
            if (self.drawTracks):
                if (self.targets is not None):
                    for track in self.targets:
                        trackID = int(track[0])
                        trackColor = self.trackColorMap[trackID]
                        self.drawTrack(track, trackColor)
                    # for fig in self.man_plt:
                    #     self.pcplot.addItem(fig)
        except Exception as e:
            print("can't draw Tracks", e)
            pass

        self.done.emit()

    def stop(self):
        self.terminate()

class PeopleTracking():
    def __init__(self, window):
        self.tabs = None
        self.cumulativeCloud = None
        self.colorGradient = pg.GradientWidget(orientation='right')
        self.colorGradient.restoreState({'ticks': [ (1, (255, 0, 0, 255)), (0, (131, 238, 255, 255))], 'mode': 'hsv'})
        self.colorGradient.setVisible(False)
        self.maxTracks = int(5) # default to 5 tracks
        self.trackColorMap = get_trackColors(self.maxTracks)
        self.state = [3] * NUM_OF_DETECT_PEOPLE
        self.window = window
        self.fall_panels = self.window.fall_panels

        # self.fallDetection = FallDetection()

        # gl_view connection
        self.elev_tilt = self.window.gl_view.elev_tilt
        self.az_tilt = self.window.gl_view.az_tilt
        self.sensorHeight = self.window.gl_view.sensorHeight
        self.plot_3d = self.window.gl_view.plot_3d
        self.scatter = self.window.gl_view.scatter
        self.previousClouds = self.window.gl_view.previousClouds
        self.plotComplete = self.window.gl_view.plotComplete
        self.ellipsoids = self.window.gl_view.ellipsoids

        # panel ticket
        self.panel_ticket = []
        self.panel_color = []
        for _ in range(NUM_OF_DETECT_PEOPLE):
            self.panel_color.append(PANEL_COLOR_TRANS)
            self.panel_ticket.append(0)

    def updateGraph(self, outputDict, busy=False):
        self.plotStart = int(round(time.time() * 1000))
        self.window.gl_view.updatePointCloud(outputDict)

        self.cumulativeCloud = None

        if ('frameNum' in outputDict and outputDict['frameNum'] > 1 and len(self.previousClouds[:-1]) > 0):
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
            self.window.numPointsLabel.setText(LABEL_POINTS + str(outputDict['numDetectedPoints']))

        if ('numDetectedTracks' in outputDict):
            self.window.numTargetsLabel.setText(LABEL_TARGETS + str(outputDict['numDetectedTracks']))

        try:
            if ('trackData' in outputDict):
                tracks = outputDict['trackData']
                for i in range(outputDict['numDetectedTracks']):
                    rotX, rotY, rotZ = eulerRot(tracks[i,1], tracks[i,2], tracks[i,3], self.elev_tilt, self.az_tilt)
                    tracks[i,1] = rotX
                    tracks[i,2] = rotY
                    tracks[i,3] = rotZ
                    tracks[i,3] = tracks[i,3] + self.sensorHeight

                if ('heightData' in outputDict):
                    if (len(outputDict['heightData']) != len(outputDict['trackData'])):
                        pass
                    
                    # AI Fall Detection
                    # for height in outputDict['heightData']:
                    #     for track in outputDict['trackData']:
                    #         if (int(track[0]) == int(height[0])):
                    #             tid = int(height[0])
                    #             fallDetectionDisplayResults = self.fallDetection.step(outputDict)
                    #             try:
                    #                 tid = fallDetectionDisplayResults[0]
                    #                 self.state[tid] = fallDetectionDisplayResults[1]
                    #             except TypeError:
                    #                 pass
                                # will display state as model and pannel on updateQTT.update_fall_status                   
            else:
                return
        except IndexError:
            pass

        # decrease pannel ticket
        for idx in range(NUM_OF_DETECT_PEOPLE):
            if(self.panel_ticket[idx] > 0):
                self.panel_ticket[idx] = self.panel_ticket[idx] - 1
            else:
                self.window.fall_panels[idx].setStyleSheet("background-color: transparent; border: 1px solid gray; color: black;")
                self.panel_color[idx] = PANEL_COLOR_TRANS

        if (self.plotComplete):
            self.plotStart = int(round(time.time() * 1000))
            self.plot_3d_thread = updateQTTargetThread3D(self.fall_panels, self.state, self.cumulativeCloud, tracks, self.scatter, self.plot_3d, 0, self.ellipsoids, "", self.panel_color, self.panel_ticket, colorGradient=self.colorGradient, pointColorMode='SNR', trackColorMap=self.trackColorMap)
            self.plotComplete = 0
            self.plot_3d_thread.done.connect(lambda: self.graphDone(outputDict))
            self.plot_3d_thread.start(priority=QThread.HighPriority)
    
        if ('frameNum' in outputDict):
            self.window.frameNumLabel.setText(LABEL_FRAME + str(outputDict['frameNum']))

    def graphDone(self, outputDict):
        if ('frameNum' in outputDict):
            self.window.frameNumLabel.setText(LABEL_FRAME + str(outputDict['frameNum']))

        plotTime = int(round(time.time() * 1000)) - self.plotStart
        self.window.plotTimeLabel.setText(LABEL_PLT_TIME + str(plotTime) + 'ms')
        self.plotComplete = 1

    # def update_fall_status(self, fall_status: list, tid, tracks):
    #     pass
    # # TODO 해당 부분 구현 필요
    #     if tid > 5 or tid < 0:
    #         return
    #     try:
    #         idx = fall_status[0]
    #         if idx < 0 or idx > 5:
    #             return
    #     except:
    #         return
        
    #     panel = self.window.fall_panels[idx]

    #     try:
    #         def reset_fall_checker(panel, tid):
    #             panel.setStyleSheet("background-color: transparent; border: 1px solid gray; color: black;")
    #             fallChecker[tid] = 0
    #         # if fall_status[1] == 0 or fall_status[1] == 2:  # test code
    #         if fall_status[1] == 0:  # 낙상 감지됨
    #             panel.setStyleSheet("background-color: red; color: white; border: 1px solid black;")
    #             fallChecker[tid] = 1
    #             # 일정 시간 후 초록색으로 변경하는 타이머 설정 (10초 후)
    #             QTimer.singleShot(10000, lambda: reset_fall_checker(panel, tid))
    #         else:
    #             if fallChecker[tid] != 1:
    #                 panel.setStyleSheet("background-color: green; color: white; border: 1px solid black;")
    #                 QTimer.singleShot(2000, lambda p=panel: p.setStyleSheet("background-color: transparent; border: 1px solid gray; color: black;"))
    #         # elif tracks[idx]:  # 트랙 감지됨
    #         #     panel.setStyleSheet("background-color: green; color: white; border: 1px solid black;")
            
    #         # else:  # 트랙 소멸
    #         #     panel.setStyleSheet("background-color: transparent; border: 1px solid gray; color: black;")
    #     except:
    #         panel.setStyleSheet("background-color: transparent; border: 1px solid gray; color: black;")        

    def parseTrackingCfg(self, args):
        self.maxTracks = int(args[4])
        self.trackColorMap = get_trackColors(self.maxTracks)
        # for m in range(self.maxTracks):
        for _ in range(NUM_OF_DETECT_PEOPLE * 2):
            # Add track gui object
            mesh = gl.GLLinePlotItem()
            mesh.setVisible(False)
            self.plot_3d.addItem(mesh)
            self.ellipsoids.append(mesh)