from application.widgets.w_file import *
from application.widgets.w_graph import *
from application.widgets.w_device import *
from application.widgets.w_analyze import *

import PyQt5.QtWidgets as QW
import PyQt5.uic as uic
from PyQt5.QtCore import pyqtSlot, QTimer, QObject
from PyQt5.QtGui import QIcon, QPixmap

from utils.paths import Path
from utils.serialAPI import serial_api, serial_ports, SerialDataReceiver
from utils.other import get_center
from utils.widgets import MessageWindow
from constants import UI_UPDATE_DELAY


class MainWindow(QW.QMainWindow):
    portSelect: QW.QComboBox

    b_connect: QW.QPushButton
    b_ports_update: QW.QPushButton

    canvas_placeholder: QW.QLabel

    menu_main: QW.QMenu
    menu_file: QW.QMenu
    menu_graph: QW.QMenu
    menu_algo: QW.QMenu
    menu_device: QW.QMenu

    image_label: QW.QLabel

    def __init__(self, ):
        super().__init__()
        uic.loadUi(Path.to_template("main.ui"), self)
        self.setWindowTitle("Анализатор Газов")
        self.setWindowIcon(QIcon(Path.to_images("icon.ico")))
        self.move( *get_center() )

        self.ports_update()

        self.b_connect.clicked.connect(self.connect)
        self.b_ports_update.clicked.connect(self.ports_update)

        self.menu_graph.addAction("Показать", self.open_graph)
        self.menu_file.addAction("Открыть", self.open_file)
        self.menu_algo.addAction("Показать", self.open_algo)
        self.menu_device.addAction("Показать", self.open_device)

        self.graph_window = None
        self.file_window = None
        self.algo_window = None
        self.device_window = None

        file = open(Path.to_images("signal_logo.png"), mode="rb").read()
        pixmap = QPixmap(  )
        pixmap.loadFromData(file)
        self.image_label.setPixmap(pixmap)

        self.connector = SerialConnector(self)

    def ports_update(self):
        self.portSelect.clear()
        self.portSelect.addItems(serial_ports())

    def connect(self):
        serial_api.blocked = True

        if not self.portSelect.currentText():
            MessageWindow(self, "Не указан порт")
            return

        err_code = serial_api.connect(self.portSelect.currentText())

        if err_code == 0:
            self.b_connect.setStyleSheet("background-color: green")
            self.connector.start()
            serial_api.blocked = False
        else:
            self.b_connect.setStyleSheet("background-color: red")
            self.connector.pause()
            MessageWindow(self, "Не удалось подключиться к порту")

    @pyqtSlot()
    def open_main(self):
        self.show()

    @pyqtSlot()
    def open_file(self):
        self.file_window: FileWindow = FileWindow.show_window(self, )

    @pyqtSlot()
    def open_graph(self):
        self.graph_window: GraphWindow = GraphWindow.show_window(self, )

    @pyqtSlot()
    def open_algo(self):
        self.algo_window: AnalyzeWindow = AnalyzeWindow.show_window(self, )

    @pyqtSlot()
    def open_device(self):
        self.device_window: DeviceWindow = DeviceWindow.show_window(self, )

    @pyqtSlot()
    def updateSerialData(self):
        data, saved_data = serial_api.getData()

        if data is None:
            # MessageWindow(self, "Ошибка порта")
            self.b_connect.setStyleSheet("background-color: red")
            self.connector.pause()
            serial_api.blocked = True
            return

        SerialDataReceiver.sendSerialData(data, saved_data)


class SerialConnector(QObject):
    def __init__(self, parent: MainWindow):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.setInterval(UI_UPDATE_DELAY)
        self.timer.timeout.connect(parent.updateSerialData)

    def start(self):
        self.timer.start()

    def pause(self):
        self.timer.stop()
