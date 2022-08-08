from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import time
import random
import numpy as np
import math
import matplotlib as mpl
import matplotlib.pyplot as pypl
pypl.ion()
mpl.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar

DEFAULT_START = (0, 0)
DEFAULT_LENGTH = 1
SPEEDS = ("0.01", "0.05", "0.1", "0.15", "0.2", "0.33", "0.5", "1")

def getEndPoint(angle, start=DEFAULT_START, length=DEFAULT_LENGTH):
    startX, startY = start
    rad = math.radians(angle)
    endX = startX + length * math.sin(rad)
    endY = startY + length * math.cos(rad)

    return (endX, endY)

def calculateCrossing(L1, L2):
    # takes 2 tuples containing dots (also tuples) which build the lines
    # unpack the dot coordinates
    p1, p2 = L1
    p3, p4 = L2
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    # stack overflow solution
    # I had mine but I deleted it bc I'm dumb
    s = np.vstack([p1, p2, p3, p4])         # s for stacked
    h = np.hstack((s, np.ones((4, 1))))     # h for homogeneous
    l1 = np.cross(h[0], h[1])               # get first line
    l2 = np.cross(h[2], h[3])               # get second line
    x, y, z = np.cross(l1, l2)              # point of intersection
    if z == 0:                              # lines are parallel
        return False
    x = x / z
    y = y / z

    res = []
    res.append(x1 <= x <= x2 if x1 < x2 else x2 <= x <= x1)
    res.append(x3 <= x <= x4 if x3 < x4 else x4 <= x <= x3)
    res.append(y1 <= y <= y2 if y1 < y2 else y2 <= y <= y1)
    res.append(y3 <= y <= y4 if y3 < y4 else y4 <= y <= y3)

    if all(res):
        return True

    return False


class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = pypl.figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.currentSleepTime = 0.01
        self.flag = False
        self.maxAttempts = 0
        self.drawGraphs = 1

        self.setup()
        self.initUi()
        self.setupConnections()
        self.show()

    def setup(self):
        self.setWindowTitle("Simulation")
        self.resize(1000, 800)
        self.move(200, 100)

    def initUi(self):
        self.grid = QGridLayout()

        # label that tells us the results of the simulation
        self.tahoma = QFont("Tahoma", 16, 1)
        self.resultsLbl = QLabel("Начните симуляцию!")
        self.resultsDisplay = QLabel("0/0")
        self.resultsLbl.setFont(self.tahoma)
        self.resultsDisplay.setFont(self.tahoma)
        self.grid.addWidget(self.resultsLbl, 1, 1, 1, 1)
        self.grid.addWidget(self.resultsDisplay, 2, 1, 1, 1)

        # start simulation button
        self.start = QPushButton("Начать симуляцию!")
        self.grid.addWidget(self.start, 1, 3, 1, 1)

        # stop simulation button
        self.stop = QPushButton("Остановить симуляцию")
        self.grid.addWidget(self.stop, 2, 3, 1, 1)

        # enter number of attempts to run
        self.attemptsLbl = QLabel("Количество попыток (0 или оставить пустым для бесконечной симуляции):")
        self.grid.addWidget(self.attemptsLbl, 3, 2, 1, 1, alignment=Qt.AlignRight)
        self.attemptsInput = QTextEdit("")
        self.attemptsInput.setFixedHeight(40)
        self.grid.addWidget(self.attemptsInput, 3, 3, 1, 1)

        # enter sleeping interval between drawing each simulation
        self.sleepingLbl = QLabel("С какой скоростью (в долях сек) обновлять симуляцию:")
        self.grid.addWidget(self.sleepingLbl, 4, 2, 1, 1, alignment=Qt.AlignRight)
        self.sleepingInput = QComboBox()
        self.sleepingInput.addItems(SPEEDS)
        self.grid.addWidget(self.sleepingInput, 4, 3, 1, 1)

        # do we need to draw graphs?
        self.gl = QHBoxLayout()
        self.drawGraphs1 = QLabel("Обновлять графики каждые ")
        self.drawGraphs2 = QTextEdit("")
        self.drawGraphs2.setFixedSize(45, 30)
        self.drawGraphs3 = QLabel(" попыток")
        self.gl.addWidget(self.drawGraphs1)
        self.gl.addWidget(self.drawGraphs2)
        self.gl.addWidget(self.drawGraphs3)
        self.grid.addLayout(self.gl, 5, 3, 1, 1)

        # canvas where the simulations are drawn
        self.figureWidget = QWidget()
        self.sc = MplCanvas(self)
        self.sc.axes.grid()
        self.toolbar = NavigationToolbar(self.sc, self.figureWidget)
        plotLayout = QVBoxLayout()
        plotLayout.addWidget(self.toolbar)
        plotLayout.addWidget(self.sc)
        self.figureWidget.setLayout(plotLayout)
        self.grid.addWidget(self.figureWidget, 6, 1, 3, 2)

        # log that prints out the results
        self.log = QTextEdit("Результаты:")
        self.grid.addWidget(self.log, 6, 3, 3, 1)

        self.setLayout(self.grid)

    def setupConnections(self):
        self.start.clicked.connect(self.simulate)
        self.stop.clicked.connect(self.stopSimulation)
        self.sleepingInput.currentTextChanged.connect(self.setSpeed)
        self.attemptsInput.textChanged.connect(self.setAttempts)
        self.drawGraphs2.textChanged.connect(self.setDrawGraphs)

    def setDrawGraphs(self):
        draw = self.drawGraphs2.toPlainText()

        if draw.isdigit():
            draw = int(draw)
            if draw > 0:
                self.drawGraphs = draw

    def setAttempts(self):
        att = self.attemptsInput.toPlainText()

        if att.isdigit():
            self.maxAttempts = int(att)

    def setSpeed(self):
        self.currentSleepTime = float(self.sleepingInput.currentText())

    def stopSimulation(self):
        self.flag = False
        if self.attempts > 0:
            self.appendToLog(f'{self.successes} / {self.attempts} = {self.successes / self.attempts * 100:.4}%')
            self.appendToLog("Симуляция завершена")

    def appendToLog(self, text):
        txt = self.log.toPlainText()

        txt += "\n" + text
        self.log.setText(txt)

    def simulate(self):
        # start the simulation
        self.resultsLbl.setText("Текущий результат (успехи/попытки):")
        self.log.setText("Результаты:")
        self.attempts = 0
        self.successes = 0
        self.flag = True

        while self.flag:
            # building and showing the graph
            dots = [DEFAULT_START]
            for i in range(3):
                r = random.randint(0, 360)
                dots.append(getEndPoint(r, dots[i]))
            dots_unzipped = list(zip(*dots))

            # only draw graphs if on a certain attempts
            if self.attempts % self.drawGraphs == 0:
                self.sc.axes.cla()
                self.sc.axes.plot(*dots_unzipped, color="red", linewidth=2, marker="o")
                renderer = self.sc.renderer
                self.sc.axes.draw(renderer)

            # did the lines cross?
            self.attempts += 1
            crossing = calculateCrossing((dots[0], dots[1]), (dots[2], dots[3]))
            if crossing:
                self.successes += 1

            # editing labels
            self.resultsDisplay.setText(str(self.successes) + "/" + str(self.attempts))
            if self.attempts % 100 == 0:
                self.appendToLog(f'{self.successes} / {self.attempts} = {self.successes / self.attempts * 100:.4}%')

            # sleep
            app.processEvents()
            time.sleep(self.currentSleepTime)
            if self.attempts == self.maxAttempts:
                break

app = QApplication([])
mainWindow = MainWindow()
app.exec_()