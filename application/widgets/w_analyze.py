import PyQt5.QtWidgets as QW
import PyQt5.uic as uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot

from easygui import fileopenbox, filesavebox

from constants import *
from utils.paths import Path
from utils.serialAPI import serial_api
from utils.other import load_script
from utils.widgets import MessageWindow


__all__ = (
    "AnalyzeWindow",
)


class AnalyzeWindow(QW.QMainWindow):
    __instance = None

    b_file_learn: QW.QPushButton
    b_file_test: QW.QPushButton
    b_file_algorithm: QW.QPushButton

    b_save: QW.QPushButton
    b_start_test_file: QW.QPushButton
    b_analyze_port: QW.QPushButton
    b_load_in_lib: QW.QPushButton

    b_size_down: QW.QPushButton
    b_size_up: QW.QPushButton

    label_file_learn: QW.QLabel
    label_file_test: QW.QLabel
    label_file_algorythm: QW.QLabel

    log_view: QW.QTextEdit
    rb_del_columns: QW.QRadioButton

    def __init__(self, parent: QW.QMainWindow):
        super().__init__(parent)
        uic.loadUi(Path.to_template("testing.ui"), self)
        self.setWindowTitle("Анализатор Газов: Алгоритм и Анализ")
        self.setWindowIcon(QIcon("../templates/icon.ico"))
        self.move(QW.QDesktopWidget().availableGeometry().center())

        self.b_file_test.clicked.connect(lambda: self.load_file(self.label_file_test))
        self.b_file_learn.clicked.connect(lambda: self.load_file(self.label_file_learn))
        self.b_file_algorithm.clicked.connect(self.load_script)

        self.b_load_in_lib.clicked.connect(self.loadLearnToLib)
        self.b_start_test_file.clicked.connect(self.testWithFile)
        self.b_save.clicked.connect(self.saveLog)
        self.b_analyze_port.clicked.connect(self.analyzeSwitch)

        self.b_size_down.clicked.connect(self.sizeDown)
        self.b_size_up.clicked.connect(self.sizeUp)

        self.lib = None
        self.do_analyze = False

    @staticmethod
    def load_file(widget: QW.QLabel):
        default = widget.text() if widget.text() else FILE_DEFAULTS
        file_path = fileopenbox("Выберите файл", filetypes=FILE_DEFAULTS, default=default)

        if not file_path:
            widget.setText("нет файла")
            return
        try:
            file = open(file_path, mode="r")
            file.close()
        except FileNotFoundError:
            widget.setText("нет файла")
            return

        widget.setText(file_path)

    def load_script(self):
        file_path = fileopenbox("Выберите файл алгоритма", filetypes=SCRIPT_DEFAULTS, default=SCRIPT_DEFAULTS)

        if not file_path:
            self.label_file_algorythm.setText("нет файла")
            return
        try:
            file = open(file_path, mode="r")
            file.close()
        except FileNotFoundError:
            self.label_file_algorythm.setText("нет файла")
            return

        self.lib, code = load_script(file_path)
        if code != 0:
            MessageWindow(self, f"ERROR: {code}")
            self.label_file_algorythm.setText("нет файла")
            return

        self.label_file_algorythm.setText(file_path)

    @classmethod
    def show_window(cls, parent):
        if cls.__instance is None:
            cls.__instance = cls(parent, )

        cls.__instance.show()
        return cls.__instance

    def loadLearnToLib(self):
        if not self.lib:
            MessageWindow(self, "Загрузите алгоритм")
            return

        file_path = self.label_file_learn.text()
        if file_path == "нет файла":
            MessageWindow(self, "Загрузите файл обучения")
            return

        skip_rows = [i + INFO_COLUMNS for i, state in enumerate(serial_api.getUsePortsState()) if not state]
        if not self.rb_del_columns.isChecked():
            skip_rows = []
        self.lib.load(file_path, HEADER_ROWS, skip_rows)
        MessageWindow(self, "Обучение завершено")

    def testWithFile(self):
        if not self.lib:
            return

        file_path = self.label_file_test.text()
        if not file_path or file_path == "нет файла":
            MessageWindow(self, "Загрузите файл с тестовыми данными")
            return

        self.log_view.setText(
            f"Файл Алгоритма: {self.label_file_algorythm.text()}\n"
            f"Название: {self.lib.NAME}"
        )

        with open(file_path, mode="r") as file:
            data = file.readlines()[HEADER_ROWS + 1:]
            counter, counter_good = 0, 0

            for i, line in enumerate(data):
                res = self.lib.analyze(line.strip().split(DATA_DIVIDER)[SKIP_COLUMNS:])
                true = line.split("\t")[1]
                p = "ВЕРНО" if res == true else "ПРОМАХ"
                counter += 1
                counter_good += res == true

                self.log_view.append(
                    f"{i}\tрез: {res}\tист: {true}\t{p}"
                )

            percentage = counter_good / counter * 100 // 1
            self.log_view.append(
                f"\n ТОЧНОСТЬ: {percentage}%"
            )
            MessageWindow(self, f"Тестирование завершено. Точность: {percentage}%")

    def saveLog(self):
        file_path = filesavebox("Сохранить как", filetypes=FILE_DEFAULTS, default=FILE_DEFAULTS)
        if not file_path: return
        with open(file_path, mode="w") as file:
            file.write(self.log_view.toPlainText())

    def sizeUp(self):
        font = self.log_view.font()
        font.setPointSize(min(font.pointSize() + 2, 24))
        self.log_view.setFont(font)
        self.log_view.update()

    def sizeDown(self):
        font = self.log_view.font()
        font.setPointSize(max(font.pointSize() - 2, 10))
        self.log_view.setFont(font)
        self.log_view.update()

    def analyzeSwitch(self):
        self.do_analyze = bool(self.do_analyze - 1)
        if self.do_analyze:
            self.b_analyze_port.setText("Остановить")
            self.b_analyze_port.setStyleSheet("background-color: grey")
        else:
            self.b_analyze_port.setText("Анализировать с данными порта")
            self.b_analyze_port.setStyleSheet("background-color: white")

    @pyqtSlot()
    def getSerialData(self, data):
        if not self.do_analyze:
            return

        # state = serial_api.sensorsState()
        if self.lib:
            res = self.lib.analyze(data)
            match res:
                case "Gvozd":
                    res = "Гвоздика"
                case "Air":
                    res = "Воздух"
                case "Orange":
                    res = "Апельсин"
        else:
            res = "Нет алгоритма"

        # self.log_view.clear()
        # self.log_view.append(f"Газ: {res}")
        self.log_view.setText(f"Газ: {res}")
        print(f"Газ: {res}")

        # if state == 0:
        #     self.log_view.setText( f"{res} {data}" )
        # elif state == 1:
        #     self.log_view.setText( "РОСТ" )
        # else:
        #     self.log_view.setText( "ОТДЫХ" )






















