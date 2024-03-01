from application.widgets.w_file import *
from application.widgets.w_graph import *
from application.widgets.w_device import *
from application.widgets.w_analyze import *

import PyQt5.QtWidgets as QW
import PyQt5.uic as uic
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon, QPixmap

from utils.paths import Path
from utils.serialAPI import serial_api, serial_ports
from utils.other import get_center
from utils.widgets import MessageWindow


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

        file = open(Path.to_template("signal_logo.png"), mode="rb").read()
        pixmap = QPixmap(  )
        pixmap.loadFromData(file)
        self.image_label.setPixmap(pixmap)

    def ports_update(self):
        self.portSelect.clear()
        self.portSelect.addItems(serial_ports())

    def connect(self):
        serial_api.blocked = True

        if not self.portSelect.currentText():
            MessageWindow(self, "Не указан порт")
            return

        err_code = serial_api.connect(
            self.portSelect.currentText(), self.updateSerialData
        )

        if err_code == 0:
            self.b_connect.setStyleSheet("background-color: green")
            serial_api.blocked = False
        else:
            self.b_connect.setStyleSheet("background-color: red")
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
    def updateSerialData(self, data, saved_data):
        if data is None:
            # MessageWindow(self, "Ошибка порта")
            self.b_connect.setStyleSheet("background-color: red")
            serial_api.blocked = True
            return

        if self.file_window and self.file_window.isVisible():
            self.file_window.getSerialData(data)

        if self.graph_window and self.graph_window.isVisible():
            self.graph_window.getSerialData(saved_data)

        if self.algo_window and self.algo_window.isVisible():
            self.algo_window.getSerialData(data)
