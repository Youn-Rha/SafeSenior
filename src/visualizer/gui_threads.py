# General Library Imports
import numpy as np

# PyQt imports
from PySide2.QtCore import QThread, Signal
import pyqtgraph as pg

# Local Imports
from gui_parser import UARTParser
from gui_common import *
from graph_utilities import *

import pyqtgraph.opengl as gl

from Common_Tabs.plot_3d import Plot3D

import copy

# Logger
import logging
log = logging.getLogger(__name__)

# Classifier Configurables
MAX_NUM_TRACKS = 20 # This could vary depending on the configuration file. Use 20 here as a safe likely maximum to ensure there's enough memory for the classifier

# Expected minimums and maximums to bound the range of colors used for coloring points
SNR_EXPECTED_MIN = 5
SNR_EXPECTED_MAX = 40
SNR_EXPECTED_RANGE = SNR_EXPECTED_MAX - SNR_EXPECTED_MIN
DOPPLER_EXPECTED_MIN = -30
DOPPLER_EXPECTED_MAX = 30
DOPPLER_EXPECTED_RANGE = DOPPLER_EXPECTED_MAX - DOPPLER_EXPECTED_MIN

# Different methods to color the points 
COLOR_MODE_SNR = 'SNR'
COLOR_MODE_HEIGHT = 'Height'
COLOR_MODE_DOPPLER = 'Doppler'
COLOR_MODE_TRACK = 'Associated Track'

# Magic Numbers for Target Index TLV
TRACK_INDEX_WEAK_SNR = 253 # Point not associated, SNR too weak
TRACK_INDEX_BOUNDS = 254 # Point not associated, located outside boundary of interest
TRACK_INDEX_NOISE = 255 # Point not associated, considered as noise


class parseUartThread(QThread):
    fin = Signal(dict)

    def __init__(self, uParser):
            QThread.__init__(self)
            self.parser = uParser

    def run(self):
        if(self.parser.parserType == "SingleCOMPort"):
            outputDict = self.parser.readAndParseUartSingleCOMPort()
        else:
            outputDict = self.parser.readAndParseUartDoubleCOMPort()
        self.fin.emit(outputDict)

    def stop(self):
        self.terminate()
class sendCommandThread(QThread):
    done = Signal()
    def __init__(self, uParser, command):
            QThread.__init__(self)
            self.parser = uParser
            self.command = command

    def run(self):
        self.parser.sendLine(self.command)
        self.done.emit()

class updateQTTargetThread3D(QThread):
    done = Signal()

    def __init__(self, par, pointCloud, targets, scatter, pcplot: gl.GLViewWidget, numTargets, ellipsoids, coords, colorGradient=None, classifierOut=[], zRange=[-3, 3], pointColorMode="", drawTracks=True, trackColorMap=None, pointBounds={'enabled': False}):
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
        # This ignores divide by 0 errors when calculating the log2
        np.seterr(divide = 'ignore')

        self.man_plt = par.man_plt
        self.state = par.state

        # for i in range(5):
        #     self.man_plt.append(gl.GLLinePlotItem())

    def drawTrack(self, track, trackColor):
        # Get necessary track data
        tid = int(track[0])
        x = track[1]
        y = track[2]
        z = track[3]

        # print(f"ploting on {x} {y} {z}")
        # track = self.ellipsoids[tid]
        # track = self.man_plt[tid]
        self.track = gl.GLLinePlotItem()
        mesh = getBoxLinesCoords(x,y,z, track_prediction=self.state)
        self.track.setData(pos=mesh,color=trackColor,width=2,antialias=True,mode='lines')
        # self.pcplot.addItem(track)
        # mesh = getBoxLinesCoords(x,y,z, track[12])
        self.track.setVisible(True)
        self.man_plt.append(self.track)
        # self.man_plt[-1].setVisible(False)
        

    # Return transparent color if pointBounds is enabled and point is outside pointBounds
    # Otherwise, color the point depending on which color mode we are in    
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

        # Color the points by their SNR
        if (self.pointColorMode == COLOR_MODE_SNR):
            snr = self.pointCloud[i,4]
            # SNR value is out of expected bounds, make it white
            if (snr < SNR_EXPECTED_MIN) or (snr > SNR_EXPECTED_MAX):
                return pg.glColor('w')
            else:
                return pg.glColor(self.colorGradient.getColor((snr-SNR_EXPECTED_MIN)/SNR_EXPECTED_RANGE))

        # Color the points by their Height
        elif (self.pointColorMode == COLOR_MODE_HEIGHT):
            zs = self.pointCloud[i, 2]

            # Points outside expected z range, make it white
            if (zs < self.zRange[0]) or (zs > self.zRange[1]):
                return pg.glColor('w')
            else:
                colorRange = self.zRange[1]+abs(self.zRange[0]) 
                zs = self.zRange[1] - zs 
                return pg.glColor(self.colorGradient.getColor(abs(zs/colorRange)))

        # Color Points by their doppler
        elif(self.pointColorMode == COLOR_MODE_DOPPLER):
            doppler = self.pointCloud[i,3]
            # Doppler value is out of expected bounds, make it white
            if (doppler < DOPPLER_EXPECTED_MIN) or (doppler > DOPPLER_EXPECTED_MAX):
                return pg.glColor('w')
            else:
                return pg.glColor(self.colorGradient.getColor((doppler-DOPPLER_EXPECTED_MIN)/DOPPLER_EXPECTED_RANGE))
                
        # Color the points by their associate track
        elif (self.pointColorMode == COLOR_MODE_TRACK):
            trackIndex = int(self.pointCloud[i, 6])
            # trackIndex of 253, 254, or 255 indicates a point isn't associated to a track, so check for those magic numbers here
            if (trackIndex == TRACK_INDEX_WEAK_SNR or trackIndex == TRACK_INDEX_BOUNDS or trackIndex == TRACK_INDEX_NOISE):
                return pg.glColor('w')
            else:
                # Catch any errors that may occur if track or point index go out of bounds
                try:
                    return self.trackColorMap[trackIndex]
                except Exception as e:
                    log.error(e)
                    return pg.glColor('w')

        # Unknown Color Option, make all points green
        else:
            return pg.glColor('g')

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

            
        while self.man_plt:
            fig : gl.GLLinePlotItem = self.man_plt.pop()
            fig.setVisible(False)
            self.pcplot.removeItem(fig)

        # Graph the targets
        try:
            if (self.drawTracks):
                if (self.targets is not None):
                    for track in self.targets:
                        trackID = int(track[0])
                        trackColor = self.trackColorMap[trackID]
                        self.drawTrack(track,trackColor)
                for fig in self.man_plt:
                    self.pcplot.addItem(fig)
        except Exception as e:
            log.error(e, "Unable to draw all tracks, ignoring and continuing execution...")
            pass

        self.done.emit()

    def stop(self):
        self.terminate()