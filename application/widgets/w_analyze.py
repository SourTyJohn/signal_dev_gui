import PyQt5.QtWidgets as QW
import PyQt5.uic as uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
from data.SelectionSave import selection

from easygui import fileopenbox, filesavebox

from constants import *
from utils.paths import Path
from utils.serialAPI import serial_api, SerialDataReceiver
from utils.other import load_script
from utils.widgets import MessageWindow, GraphCanvas

from matplotlib.lines import Line2D


__all__ = (
    "AnalyzeWindow",
)


# noinspection PyUnresolvedReferences
class AnalyzeWindow(SerialDataReceiver, QW.QMainWindow):
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

    b_save_selection: QW.QPushButton

    label_file_learn: QW.QLabel
    label_file_test: QW.QLabel
    label_file_algorythm: QW.QLabel
    b_check_models: QW.QPushButton

    log_view: QW.QTextEdit
    rb_del_columns: QW.QRadioButton

    rb_hide_good: QW.QRadioButton

    def __init__(self, parent: QW.QMainWindow):
        super().__init__(parent)
        uic.loadUi(Path.to_template("testing.ui"), self)
        self.setWindowTitle("Анализатор Газов: Алгоритм и Анализ")
        self.setWindowIcon(QIcon(Path.to_images('icon.ico')))
        self.move(QW.QDesktopWidget().availableGeometry().center())

        self.b_file_test.clicked.connect(lambda: self.load_file(self.label_file_test))
        self.b_file_learn.clicked.connect(lambda: self.load_file(self.label_file_learn))
        self.b_file_algorithm.clicked.connect(self.select_script)

        self.b_load_in_lib.clicked.connect(self.loadLearnToLib)
        self.b_start_test_file.clicked.connect(self.testWithFile)
        self.b_save.clicked.connect(self.saveLog)
        self.b_analyze_port.clicked.connect(self.analyzeSwitch)
        self.b_check_models.clicked.connect(self.open_view_models)

        self.b_size_down.clicked.connect(self.sizeDown)
        self.b_size_up.clicked.connect(self.sizeUp)

        self.lib = None
        self.do_analyze = False

        self.label_file_learn.setText(selection.get('analyze_window', 'file_learn', ''))
        self.label_file_test.setText(selection.get('analyze_window', 'file_test', ''))
        self.label_file_algorythm.setText(selection.get('analyze_window', 'algorythm', ''))
        if self.label_file_algorythm.text() != '':
            self.load_script()
        self.b_save_selection.clicked.connect(self.saveSelection)

        self.main_widget = QW.QWidget(self)
        self.main_widget.setLayout(self.layout_main)
        self.layout_main.setParent(self.main_widget)
        self.setCentralWidget(self.main_widget)

        self.models_view_window = None

    def open_view_models(self):
        if self.lib:
            if not hasattr(self.lib, 'getModelsData'):
                MessageWindow(self, 'Алгоритм не поддерживает просмотр моделей')
                return
            self.models_view_window = ViewModels.show_window(
                self, self.lib.getModelsData(), self.lib.NAME
            )
        else:
            MessageWindow(self, 'Сначала обучите алгоритм')

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

    def select_script(self):
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

        self.load_script()

        self.label_file_algorythm.setText(file_path)
        self.load_script()

    def load_script(self):
        self.lib, code = load_script(self.label_file_algorythm.text())
        if code != 0:
            MessageWindow(self, f"ERROR: {code}")
            self.label_file_algorythm.setText("нет файла")
            return

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
                res, *debug_return = self.lib.analyze(line.strip().split(DATA_DIVIDER)[SKIP_COLUMNS:])
                true = line.split("\t")[1]
                if (res[0][0] in true) or (true in res[0][0]) or (true.split('_')[0] == res[0][0].split('_')[0]):
                    if len(res) == len(true.split(',')):
                        counter_good += 1
                        p = "TRUE"
                    else:
                        counter_good += 0.5
                        p = 'MID'
                else:
                    p = 'FALSE'
                counter += 1
                if p == 'TRUE' and self.rb_hide_good.isChecked(): continue

                line = f"{i}\tрез: {res}\tист: {true}\t{p}\t" + (str(debug_return) if DO_DEBUG_RETURN else '')
                match p:
                    case 'TRUE':
                        line = LINE_FORMAT_GOOD.format(line)
                    case 'FALSE':
                        line = LINE_FORMAT_BAD.format(line)
                self.log_view.append(line)

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
    def getSerialData(self, data: list, saved_data: list):
        if not self.do_analyze:
            return

        # state = serial_api.sensorsState()
        if self.lib:
            res = self.lib.analyze(data)
        else:
            res = "Нет алгоритма"

        # self.log_view.clear()
        # self.log_view.append(f"Газ: {res}")
        self.log_view.setText(f"Газ: {res}")

        # if state == 0:
        #     self.log_view.setText( f"{res} {data}" )
        # elif state == 1:
        #     self.log_view.setText( "РОСТ" )
        # else:
        #     self.log_view.setText( "ОТДЫХ" )

    def saveSelection(self):
        selection.update('analyze_window', 'file_learn', self.label_file_learn.text())
        selection.update('analyze_window', 'file_test', self.label_file_test.text())
        selection.update('analyze_window', 'algorythm', self.label_file_algorythm.text())
        selection.save()


class GasSelectionWindow(QW.QMainWindow):

    def __init__(self, parent, file_path: str):
        super().__init__(parent)
        self.gases = {}
        with open(file_path, mode='r', encoding='utf-8') as file:
            pass


class ViewModels(QW.QMainWindow):
    __instance: "ViewModels" = None

    layout_main: QW.QVBoxLayout

    LINE_WIDTH = 2

    def __init__(self, parent, models: tuple, algo_name: str):
        super().__init__(parent)
        uic.loadUi(Path.to_template("models_view.ui"), self)
        self.setWindowTitle(f"{algo_name}: Просмотр Моделей")
        self.setWindowIcon(QIcon(Path.to_images('icon.ico')))

        self.main_widget = QW.QWidget(self)
        self.main_widget.setLayout(self.layout_main)
        self.layout_main.setParent(self.main_widget)
        self.setCentralWidget(self.main_widget)

        self.sc = GraphCanvas(width=5, height=4, dpi=100)
        self.plt = self.sc.axes
        self.layout_main.addWidget(self.sc)

        models_data, models_names = models
        self.drawModels(models_data, models_names)

    def drawModels(self, models_data, models_names):
        self.plt.clear()

        sen_amount = len(models_data[0])

        width = 1 / (sen_amount + 1)
        offset = 0
        for i, name in enumerate(models_names):
            self.plt.bar([j + offset for j in range(0, sen_amount)], models_data[i], width, label=name)
            offset += width

        mod_amount = len(models_names)
        offset = -width / 2
        for x in range(sen_amount):
            self.plt.add_line(
                Line2D(
                    [x + offset, x + (width * mod_amount) + offset],
                    [-ViewModels.LINE_WIDTH / 2, ] * 2,
                    linewidth=ViewModels.LINE_WIDTH
                )
            )

        self.plt.legend(loc="upper right")
        self.sc.draw()

    @classmethod
    def show_window(cls, parent, models_data, algo_name: str) -> "ViewModels":
        if cls.__instance:
            cls.__instance.close()

        cls.__instance = cls(parent, models_data, algo_name)
        cls.__instance.show()
        return cls.__instance
