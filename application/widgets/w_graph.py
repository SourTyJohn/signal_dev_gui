import PyQt5.QtWidgets as QW
from PyQt5.QtCore import QRect, QEvent
from PyQt5.QtGui import QIcon, QFont

from matplotlib.figure import Figure
import numpy as np

from constants import POINTS_AT_ONCE
from utils.serialAPI import serial_api
from utils.widgets import GraphCanvas, MessageWindow
from utils.other import get_center


__all__ = (
    "GraphWindow",
)


class GraphWindow(QW.QMainWindow):
    __instance = None

    sc: GraphCanvas
    plt: Figure

    def __init__(self, parent):
        super().__init__(parent)
        self.setGeometry(QRect(700, 100, 800, 800))
        self.setWindowTitle("Анализатор Газов: График")
        self.setWindowIcon(QIcon("../templates/icon.ico"))
        self.move( *get_center() )

        self.counter = 0
        self.paused = False

        self.setup_canvas()

    @classmethod
    def show_window(cls, parent):
        if cls.__instance is None:
            cls.__instance = cls(parent, )

        cls.__instance.show()

        if serial_api.blocked:
            MessageWindow(parent, "Подключитесь к порту")

        return cls.__instance

    def setup_canvas(self):
        self.sc = GraphCanvas(width=5, height=4, dpi=100)
        self.plt = self.sc.axes

        toolbar = QW.QPushButton()
        toolbar.setText("Пауза / Запуск")
        toolbar.setFont( QFont("MS Sans Serif", 12, weight=1) )
        toolbar.clicked.connect( self.pause )

        layout = QW.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.sc)

        widget = QW.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def getSerialData(self, saved_data) -> None:
        if self.paused:
            return

        self.plt.clear()

        namings = serial_api.getNamings()
        length = min(POINTS_AT_ONCE, len(saved_data))
        display_data = np.array(list( saved_data[-length:] ), dtype=int)
        s = display_data.shape

        for x in range(s[1]):
            t = display_data[:, x]
            self.plt.plot(range(self.counter, self.counter + length), t, label=namings[x])

        self.plt.legend(loc="upper right")
        self.counter += 1
        self.sc.draw()

    def closeEvent(self, event: QEvent):
        self.hide()

    def show(self) -> None:
        super(GraphWindow, self).show()

    def pause(self):
        self.paused = bool( self.paused - 1)
