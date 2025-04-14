# core.py에서 실험하며 작성한 코드들

class Test:
    def __init__(self):

        self.frame_count = 0
        self.image_list = []
        self.frame_index = 0
        self.frame_num = "0"

        self.initReplayBox()

        # middleBottom panel 실험용
        self.middleBottomWidget = QWidget()
        self.middleBottomGridLayout = QGridLayout()
        self.middleBottomGridLayout.addWidget(self.replayBox, 0, 0)
        self.middleBottomWidget.setLayout(self.middleBottomGridLayout)
        self.gridLayout.addWidget(self.middleBottomWidget, 3, 1)

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
            self.startSensor()
        else:
            self.startConnect()

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
            pixmap = self.image_list[index]
            label = QLabel(self.gl_view.plot_3d)
            label.setPixmap(pixmap)
            label.show()
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

    # 아래는 위 함수들과 프로그램을 연결하기 위해 수정한 함수들
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

    def startSensor(self):
        self.statusBar().showMessage("Send config and start")
        self.frameControl()
        if(self.core.sendCfg()):
            # disable button before reset
            self.sendCfgBtn.setDisabled(True)
            self.sendCfgBtn.setText(SEND_CFG_BTN_RUN_MSG)