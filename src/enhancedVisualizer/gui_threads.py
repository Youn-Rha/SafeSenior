import time
import numpy as np

from PySide2 import QtGui
from PySide2.QtCore import QThread, Signal, QTimer
from PySide2.QtGui import QImage
import pyqtgraph as pg

from graph_utilities import *
import pyqtgraph.opengl as gl
# from PIL import Image

from plot_3d import Plot3D

from fall_detection import FallDetection

from macroControl import HEAD_TYPE, HTYPE_CIRCLE_HEAD, HTYPE_BOX_HEAD, NUM_OF_DETECT_PEOPLE
from macroControl import STATE, PATH, CLUSTER_CACHE


POSITION_OFFSET_Z = 0.5
DRAW_CLUST_Z_OFFSET = 1

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

    def __init__(self, panels, state, pointCloud, targets, scatter, pcplot: gl.GLViewWidget, numTargets, ellipsoids, coords, panel_color, panel_ticket, clust_cache, colorGradient=None, classifierOut=[], zRange=[-3, 3], pointColorMode="", drawTracks=True, trackColorMap=None, pointBounds={'enabled': False}):
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
        self.clust_cache = clust_cache

        self.panel_color = panel_color
        self.panel_ticket = panel_ticket

        # self.image = Image.open((PATH.BASE_DIR + "/img/people_image_4.png"))
        # self.imgae = self.image.convert("RGBA")
        # self.image = self.image.resize((100, 200), Image.ANTIALIAS)
        # self.image_array = np.array(self.image)
    
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


    def update_fall_status(self, state, tid):
        if tid >= NUM_OF_DETECT_PEOPLE or tid < 0:
            return
        
        idx = tid
        
        panel = self.fall_panels[idx]

        try:
            if state == STATE.STATE_FALL:  # 낙상 감지됨
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
        except:
            panel.setStyleSheet("background-color: transparent; border: 1px solid gray; color: black;")  

    def drawClust(self, entry, trackColor):
        if entry[CLUSTER_CACHE.CNT] < CLUSTER_CACHE.MIN_PLOT_CNT:
            return

        tid = entry[CLUSTER_CACHE.PID]
        x = entry[CLUSTER_CACHE.XPOS]
        y = entry[CLUSTER_CACHE.YPOS]
        z = DRAW_CLUST_Z_OFFSET
        state = entry[CLUSTER_CACHE.STATE]

        # print(f"ploting on {x} {y} {z} id {tid} state {state}")
        self.update_fall_status(state, tid)

        # TODO compare with cache, if changed distance lower than threshold, keep it same
        pltd_x = entry[CLUSTER_CACHE.PLTD_X]
        pltd_y = entry[CLUSTER_CACHE.PLTD_Y]
        sq_dist = (pltd_x - x)**2 + (pltd_y - y)**2
        if sq_dist < CLUSTER_CACHE.MIN_DISTANCE_TO_MOVE:
            x = pltd_x
            y = pltd_y
        else:
            # update plotted position on cache
            entry[CLUSTER_CACHE.PLTD_X] = x
            entry[CLUSTER_CACHE.PLTD_Y] = y

        self.track = self.ellipsoids[tid]
        if HEAD_TYPE == HTYPE_CIRCLE_HEAD:
            self.track2 = self.ellipsoids[NUM_OF_DETECT_PEOPLE*2-1-tid]
            z = z + POSITION_OFFSET_Z
            head = CircleBillboard3D(0, 0, 0, radius=0.15, view= self.pcplot)
            self.head_list.append(head)
            mesh1 = getBoxLinesCoordsCircleHead(x, y, z, track_prediction=state)

            # set posture
            if state == STATE.STATE_FALL or state == STATE.STATE_LIE_DOWN:
                mesh2 = head.update_orientation() + np.array([x, y - 0.8, z])
            else:
                mesh2 = head.update_orientation() + np.array([x, y, z + 0.8])
            self.track2.setData(pos=mesh2,color=trackColor,width=2,antialias=True,mode='lines')
            self.track2.setVisible(True)
        else:
            mesh1 = getBoxLinesCoordsBoxHead(x, y, z, track_prediction=state)

        self.track.setData(pos=mesh1,color=trackColor,width=2,antialias=True,mode='lines')
        self.track.setVisible(True)

    def drawTrack(self, track, trackColor):
        # Get necessary track data
        tid = int(track[0])
        x = track[1]
        y = track[2]
        z = track[3]
        # print(f"ploting on {x} {y} {z}")

        self.update_fall_status(self.state, tid)
        self.track = self.ellipsoids[tid]
        self.track2 = self.ellipsoids[NUM_OF_DETECT_PEOPLE*2-1-tid]

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
            self.track2.setVisible(True)   
        else:
            mesh1 = getBoxLinesCoordsBoxHead(x, y, z, track_prediction=self.state[tid])
            
        self.track.setData(pos=mesh1,color=trackColor,width=2,antialias=True,mode='lines')
        self.track.setVisible(True)

    def drawTrackImage(self, track):
        # Get necessary track data
        tid = int(track[0])
        x = track[1]
        y = track[2]
        z = track[3]

        image_item = gl.GLImageItem(self.image_array)
        image_item.translate(x, y, z)
        # self.update_fall_status(self.state, tid)
        
        self.pcplot.addItem(image_item)

    def run(self):

        # Clear all previous targets
        for e in self.ellipsoids:
            if (e.visible()):
                e.hide()

        # to supress openGL scatter error, foce to match pos and color size
        if(self.pointCloud is not None):
            toPlot = self.pointCloud[:, 0:3]
            pointNum = toPlot.shape[0]

            snr_val = np.maximum(self.pointCloud[:,4], 1e-10)
            size = np.log2(snr_val)

            # ensure size matching
            size = size[:pointNum]

            pointColors = np.zeros((pointNum, 4))
            for i in range(pointNum):
                pointColors[i] = self.getPointColors(i)
            try:
                self.scatter.setData(pos=toPlot, color=pointColors, size=size)
                self.scatter.setVisible(True)
            except Exception as e:
                print(e)
        else:
            self.scatter.setVisible(False)
        
        # try:
        #     # Create a list of just X, Y, Z values to be plotted
        #     if(self.pointCloud is not None):
        #         toPlot = self.pointCloud[:, 0:3]

        #         # Determine the size of each point based on its SNR
        #         with np.errstate(divide='ignore'):
        #             size = np.log2(self.pointCloud[:, 4])
                
        #         # Each color is an array of 4 values, so we need an numPoints*4 size 2d array to hold these values
        #         pointColors = np.zeros((self.pointCloud.shape[0], 4))

        #         # Set the color of each point
        #         for i in range(self.pointCloud.shape[0]):
        #             pointColors[i] = self.getPointColors(i)

        #         # Plot the points
        #         self.scatter.setData(pos=toPlot, color=pointColors, size=size)
        #         # Make the points visible 
        #         self.scatter.setVisible(True)
        #     else:
        #         # Make the points invisible if none are detected.
        #         self.scatter.setVisible(False)
        # except:
        #     # log.error("Unable to draw point cloud, ignoring and continuing execution...")
        #     pass

        # Graph the targets
        try:
            if (self.drawTracks):
                for idx, elem in enumerate(self.clust_cache):
                    trackColor = self.trackColorMap[idx]
                    self.drawClust(elem, trackColor)
                    # self.drawTrackImage(elem, trackColor)

            # if (self.drawTracks):
            #     if (self.targets is not None):
            #         for track in self.targets:
            #             trackID = int(track[0])
            #             trackColor = self.trackColorMap[trackID]
            #             self.drawTrackImage(track)

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

        # Fall Detection class
        self.fallDetection = FallDetection(self)

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

        # cluster cache
        self.used_people_id = set()
        self.clust_cache = []

    def updateGraph(self, outputDict, busy=False):
        self.plotStart = int(round(time.time() * 1000))
        self.window.gl_view.updatePointCloud(outputDict)

        self.cumulativeCloud = None

        if ('frameNum' in outputDict and outputDict['frameNum'] > -1 and len(self.previousClouds[:-1]) > 0):
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
                    
                    self.updateClusterTicket()
                    ret = self.fallDetection.step(outputDict)
                    if ret[0]:  # 클러스터링 결과가 존재
                        for xPos, yPos in ret[1]:
                            self.updateClusterCache(xPos, yPos)
                        # print(self.used_people_id, end='\n\n')

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
            self.plot_3d_thread = updateQTTargetThread3D(self.fall_panels, self.state, self.cumulativeCloud, tracks, self.scatter, self.plot_3d, 0, self.ellipsoids, "", self.panel_color, self.panel_ticket, self.clust_cache, colorGradient=self.colorGradient, pointColorMode='SNR', trackColorMap=self.trackColorMap)
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

    def stateTransition(self, param):
        for elem in param:
            xPos = elem[0][0]
            yPos = elem[0][1]
            state = elem[1]

            if state < 0:
                continue    # wrong state value

            idx_to_update = 0
            # find nearest cluster
            for idx, elem in enumerate(self.clust_cache):
                if elem[CLUSTER_CACHE.CNT] < CLUSTER_CACHE.MIN_PLOT_CNT:
                    pass    # ignore not plotted entry
                if idx == 0:
                    min_dist = (elem[CLUSTER_CACHE.XPOS] - xPos)**2 + (elem[CLUSTER_CACHE.YPOS] - yPos)**2
                sq_dist = (elem[CLUSTER_CACHE.XPOS] - xPos)**2 + (elem[CLUSTER_CACHE.YPOS] - yPos)**2
                if min_dist > sq_dist:
                    idx_to_update = idx
                    min_dist = sq_dist

            # update state from cache table
            self.clust_cache[idx_to_update][CLUSTER_CACHE.STATE] = state


    def updateClusterTicket(self):
        del_elem = []
        for idx, elem in enumerate(self.clust_cache):
            # ticket calc
            elem[CLUSTER_CACHE.TICKET] -= 1
            if elem[CLUSTER_CACHE.TICKET] < 1:
                # expired
                del_elem.append(elem)
                self.used_people_id.remove(elem[CLUSTER_CACHE.PID])

        # delete expired entry
        for elem in del_elem:
            self.clust_cache.remove(elem)


    def updateClusterCache(self, xPos, yPos):
        near_clust_flag = False

        for idx, elem in enumerate(self.clust_cache):
            sq_dist = (elem[CLUSTER_CACHE.XPOS] - xPos)**2 + (elem[CLUSTER_CACHE.YPOS] - yPos)**2
            
            if sq_dist < CLUSTER_CACHE.DISTANCE_THRESHOLD:  # near cluster found
                # print(sq_dist, " : " ,elem[CLUSTER_CACHE.XPOS], elem[CLUSTER_CACHE.YPOS])
                if near_clust_flag == False:
                    near_clust_flag = True
                    near_clust = (sq_dist, elem[CLUSTER_CACHE.XPOS], elem[CLUSTER_CACHE.YPOS], idx)
                else:
                    if near_clust[0] > sq_dist:
                        near_clust = (sq_dist, elem[CLUSTER_CACHE.XPOS], elem[CLUSTER_CACHE.YPOS], idx)

        if near_clust_flag:
            # update cache to near cluster data
            self.clust_cache[near_clust[3]] = [xPos, yPos, CLUSTER_CACHE.TICKET_UPDATE, self.clust_cache[near_clust[3]][3], self.clust_cache[near_clust[3]][4], self.clust_cache[near_clust[3]][5] + 1, self.clust_cache[near_clust[3]][6], self.clust_cache[near_clust[3]][7]]
            # counter ++
        else:
            new_id = 1
            while new_id in self.used_people_id:
                new_id += 1

            if new_id > NUM_OF_DETECT_PEOPLE:   # pid overflowed
                # find min ticket
                min = CLUSTER_CACHE.TICKET_UPDATE
                min_idx = 1
                for idx, elem in enumerate(self.clust_cache):
                    if min > elem[CLUSTER_CACHE.TICKET]:
                        min_idx = idx + 1
                        min = elem[CLUSTER_CACHE.TICKET]
                self.clust_cache[min_idx] = [xPos, yPos, CLUSTER_CACHE.TICKET_UPDATE, STATE.STATE_WALK, self.clust_cache[min_idx][4], 0, 0, 0]
            else:
                # add new cluster info
                self.used_people_id.add(new_id)
                self.clust_cache.append([xPos, yPos, CLUSTER_CACHE.TICKET_UPDATE, STATE.STATE_WALK, new_id, 0, 0, 0])