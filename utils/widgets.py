from PyQt5 import QtWidgets as QW
from PyQt5.QtGui import QFont

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure


__all__ = (
    "MessageWindow",
    "GraphCanvas",
)


class MessageWindow(QW.QMainWindow):

    def __init__(self, parent: QW.QMainWindow, message):
        super(MessageWindow, self).__init__(parent)
        self.label = QW.QLabel(parent=self, text=message)
        self.label.setFont( QFont("MS Sans Serif", pointSize=12) )
        self.setCentralWidget(self.label)
        self.setWindowTitle("Сообщение")
        self.setGeometry(parent.geometry().x() + 40, parent.geometry().y() + 40, 300, 50)
        self.show()
        self.setFocus()


class GraphCanvas(FigureCanvasQTAgg):

    def __init__(self, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(GraphCanvas, self).__init__(fig)


class AskWindow(QW.QMainWindow):
    pass
