import PyQt5.QtWidgets as QW
import PyQt5.uic as uic
from PyQt5.QtCore import QRect, QEvent, pyqtSlot, QTimer
from PyQt5.QtGui import QIcon, QPixmap

from matplotlib.figure import Figure
import numpy as np

from easygui import fileopenbox, filesavebox
from datetime import datetime

from constants import *
from utils import *


class GraphWindow(QW.QMainWindow):
    __instance = None

    sc: GraphCanvas
    plt: Figure

    def __init__(self, parent):
        super().__init__(parent)
        self.setGeometry(QRect(700, 100, 800, 800))
        self.setWindowTitle("Анализатор Газов: График")
        self.setWindowIcon(QIcon("templates/icon.ico"))
        self.move( *get_center() )

        self.counter = 0
        self.paused = False

        self.setup_canvas()

    @classmethod
    def show_window(cls, parent):
        if cls.__instance is None:
            cls.__instance = cls(parent, )

        cls.__instance.show()

        if SerialAPI.isDisabled():
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

        namings = SerialAPI.getNamings()
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

    def __init__(self):
        super().__init__()
        uic.loadUi("templates/main.ui", self)
        self.setWindowTitle("Анализатор Газов")
        self.setWindowIcon(QIcon("templates/icon.ico"))
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

        self.timer = QTimer(self)
        self.timer.setInterval(PORT_READ_DELAY)
        self.timer.timeout.connect(self.updateSerialData)
        self.timer.start()

        file = open("templates/signal_logo.png", mode="rb").read()
        pixmap = QPixmap(  )
        pixmap.loadFromData(file)
        self.image_label.setPixmap(pixmap)

    def ports_update(self):
        self.portSelect.clear()
        self.portSelect.addItems(serial_ports())

    def connect(self):
        self.timer.stop()

        if not self.portSelect.currentText():
            MessageWindow(self, "Не указан порт")
            return

        err_code = SerialAPI.usePort( self.portSelect.currentText() )

        if err_code == 0:
            self.b_connect.setStyleSheet("background-color: green")
            self.timer.start()
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

    def updateSerialData(self):
        data = SerialAPI.readLine()
        saved_data = SerialAPI.getSaved()

        if data is None:
            #MessageWindow(self, "Ошибка порта")
            self.b_connect.setStyleSheet("background-color: red")
            self.timer.stop()
            return

        if self.file_window and self.file_window.isVisible():
            self.file_window.getSerialData(data)

        if self.graph_window and self.graph_window.isVisible():
            self.graph_window.getSerialData(saved_data)

        if self.algo_window and self.algo_window.isVisible():
            self.algo_window.getSerialData(data)


class FileWindow(QW.QMainWindow):
    __instance = None

    b_file_open:    QW.QPushButton
    b_file_save:    QW.QPushButton
    b_pause_write:  QW.QPushButton
    b_clear:        QW.QPushButton
    b_size_down:    QW.QPushButton
    b_size_up:      QW.QPushButton

    line_gas_name:      QW.QLineEdit

    file_view_table:    QW.QTextBrowser

    # timer
    pb_timer: QW.QProgressBar
    sb_timer_time: QW.QSpinBox
    rb_use_timer: QW.QRadioButton

    def __init__(self, parent: QW.QMainWindow):
        super().__init__(parent)
        uic.loadUi("templates/file.ui", self)
        self.setWindowTitle("Анализатор Газов: Файл")
        self.setWindowIcon(QIcon("templates/icon.ico"))
        self.clear_file_view()
        self.move( *get_center() )

        self.counter = 0

        # Кнопка выбора файла
        self.b_file_open.clicked.connect(self.locate_file)
        self.file_path = ""

        # Кнопка сохранения файла
        self.b_file_save.clicked.connect(self.save_file)

        # Кнопка записи в файл
        self.b_pause_write.clicked.connect(self.b_write_state)
        self.write_state = False

        # Кнопка очищения файла
        self.b_clear.clicked.connect(self.clear_file_view)

        self.b_size_down.clicked.connect(self.sizeDown)
        self.b_size_up.clicked.connect(self.sizeUp)

        self.rb_use_timer.clicked.connect( self.radioTimerClick )
        self.timer_checked_true = self.rb_use_timer.isChecked()
        self.timer_k = 0

    @classmethod
    def show_window(cls, parent):
        if cls.__instance is None:
            cls.__instance = cls(parent, )

        cls.__instance.show()
        return cls.__instance

    def locate_file(self):
        default = self.file_path if self.file_path else FILE_DEFAULTS
        file_path = fileopenbox("Выберите файл", filetypes=FILE_DEFAULTS, default=default)
        self.file_path = file_path

        if not file_path: return

        if not file_path:
            MessageWindow(self, "Укажите путь к файлу")
            return

        try:
            file = open(file_path, mode="r")
            text = file.read()
            self.file_view_table.setText(text)

            try:
                if len(self.file_view_table.toPlainText().split("\n")) > len(FILE_FORMAT.split("\t")):
                    self.counter = int(self.file_view_table.toPlainText().split("\n")[-2].split("\t")[0]) + 1
                else:
                    self.counter = 0

            except ValueError:
                if self.file_view_table.toPlainText().split("\n")[-2].split("\t")[0] != "[DATA]":
                    MessageWindow(self, "Не удалось получить данные. Неправильный формат файла")

            except IndexError:
                MessageWindow(self, "Не удалось получить данные. Неправильный формат файла")

            file.close()
        except FileNotFoundError:
            MessageWindow(self, "Ошибка при открытии файла")

    def save_file(self):
        default = self.file_path if self.file_path else FILE_DEFAULTS
        file_path = filesavebox("Сохранить как", filetypes=FILE_DEFAULTS, default=default)
        if not file_path: return
        with open( file_path, mode="w" ) as file:
            file.write( self.file_view_table.toPlainText() )

    def b_write_state(self):
        if SerialAPI.isDisabled() and not self.write_state:
            MessageWindow(self, "Сначала подключитесь к порту")
            return

        self.write_state = bool(self.write_state - 1)
        self.timer_reset()

        if self.write_state:
            self.b_pause_write.setStyleSheet("background-color: grey")
            self.b_pause_write.setText("Приостановить")

        else:
            self.b_pause_write.setStyleSheet("background-color: white")
            self.b_pause_write.setText("Начать запись")

    def timer_reset(self):
        self.timer_k = 0
        self.pb_timer.setValue(0)
        self.pb_timer.setMaximum( self.sb_timer_time.value() )

    def timer_update(self):
        if not self.rb_use_timer.isChecked():
            return -1

        self.timer_k += 1
        self.pb_timer.setValue( self.timer_k )

        return int( self.timer_k == self.sb_timer_time.value() )

    def clear_file_view(self):
        self.counter = 0
        self.update_header(data="")

    def update_header(self, data=None):
        if data is None:
            data = self.file_view_table.toPlainText()
            data = data[ data.find("[DATA]") + 5: ]

        date = datetime.now()

        self.file_view_table.clear()
        self.file_view_table.setText(
            FILE_FORMAT.format(
                date.strftime("%d:%m:%Y"),
                date.strftime("%H/%M/%S"),
                SerialAPI.getUsePortsState(),
                data
            )
        )

    def getSerialData(self, data):
        if self.write_state is False:
            return

        if data:
            data = "\t".join(data)
            data = f"{self.counter}\t{self.line_gas_name.text()}\t{data}"
            self.counter += 1

            self.file_view_table.append( data )
            self.file_view_table.verticalScrollBar().setValue(
                self.file_view_table.verticalScrollBar().maximum()
            )

            if self.timer_update() == 1:
                self.b_write_state()

        else:
            MessageWindow(self, "Ошибка чтения порта")
            self.write_state = True
            self.parent().b_connect.setStyleSheet("background-color: red")
            self.b_write_state()

    def sizeUp(self):
        font = self.file_view_table.font()
        font.setPointSize( min( font.pointSize() + 2, 24 ) )
        self.file_view_table.setFont( font )
        self.file_view_table.update()

    def sizeDown(self):
        font = self.file_view_table.font()
        font.setPointSize( max( font.pointSize() - 2, 10 ) )
        self.file_view_table.setFont( font )
        self.file_view_table.update()

    def radioTimerClick(self, value):
        if self.write_state:
            self.rb_use_timer.setChecked( False )
            return

        self.timer_checked_true = value


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
        uic.loadUi("templates/testing.ui", self)
        self.setWindowTitle("Анализатор Газов: Алгоритм и Анализ")
        self.setWindowIcon(QIcon("templates/icon.ico"))
        self.move(QW.QDesktopWidget().availableGeometry().center())

        self.b_file_test.clicked.connect( lambda: self.load_file( self.label_file_test ) )
        self.b_file_learn.clicked.connect( lambda: self.load_file(self.label_file_learn) )
        self.b_file_algorithm.clicked.connect( self.load_script )

        self.b_load_in_lib.clicked.connect( self.loadLearnToLib )
        self.b_start_test_file.clicked.connect( self.testWithFile )
        self.b_save.clicked.connect( self.saveLog )
        self.b_analyze_port.clicked.connect( self.analyzeSwitch )

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

        widget.setText( file_path )

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

        self.lib, code = load_script( file_path )
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

        skip_rows = [i + INFO_COLUMNS for i, state in enumerate( SerialAPI.getUsePortsState() ) if not state]
        if not self.rb_del_columns.isChecked():
            skip_rows = []
        self.lib.load( file_path, HEADER_ROWS, skip_rows)
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

        with open( file_path, mode="r" ) as file:
            data = file.readlines()[HEADER_ROWS + 1:]
            counter, counter_good = 0, 0

            for i, line in enumerate( data ):
                res = self.lib.analyze( line.strip().split(DATA_DIVIDER)[SKIP_COLUMNS:] )
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
        font.setPointSize( min( font.pointSize() + 2, 24 ) )
        self.log_view.setFont( font )
        self.log_view.update()

    def sizeDown(self):
        font = self.log_view.font()
        font.setPointSize( max( font.pointSize() - 2, 10 ) )
        self.log_view.setFont( font )
        self.log_view.update()

    def analyzeSwitch(self):
        self.do_analyze = bool( self.do_analyze - 1 )
        if self.do_analyze:
            self.b_analyze_port.setText( "Остановить" )
            self.b_analyze_port.setStyleSheet("background-color: grey")
        else:
            self.b_analyze_port.setText( "Анализировать с данными порта" )
            self.b_analyze_port.setStyleSheet("background-color: white")

    def getSerialData(self, data):
        if not self.do_analyze:
            return

        state = SerialAPI.sensorsState()
        if self.lib:
            res = self.lib.analyze(data)
            match res:
                case "Air":
                    res = "Воздух"
                case "Perfume":
                    res = "Духи"
                case "Flux":
                    res = "Флюс"
        else:
            res = "Нет алгоритма"

        if state == 0:
            self.log_view.setText( f"{res} {data}" )
        elif state == 1:
            self.log_view.setText( "РОСТ" )
        else:
            self.log_view.setText( "ОТДЫХ" )


class DeviceWindow(QW.QMainWindow):
    __instance = None

    b_refresh: QW.QVBoxLayout
    grid: QW.QGridLayout

    def __init__(self, parent):
        super().__init__(parent)
        uic.loadUi("templates/device.ui", self)
        self.setWindowTitle("Анализатор Газов: Устройство")
        self.setWindowIcon(QIcon("templates/icon.ico"))

        self.b_refresh.clicked.connect( self.refresh )
        self.states_checkers = []
        self.refresh()

    @classmethod
    def show_window(cls, parent):
        if cls.__instance is None:
            cls.__instance = cls(parent, )

        cls.__instance.show()
        return cls.__instance

    def refresh(self):
        if self.grid.count():
            for i in range(self.grid.count() - 1, -1, -1):
                h_layout = self.grid.itemAt(i).layout()

                for x in range( h_layout.count() - 1, -1, -1 ):
                    h_layout.removeWidget( h_layout.itemAt(x).widget() )

            self.states_checkers.clear()

        for i, active in enumerate( SerialAPI.getUsePortsState() ):
            row = QW.QHBoxLayout(self)

            c = QW.QLabel( str(i) )
            c.setFont( FONT_SMALL_DEF )
            row.addWidget( c )

            c = QW.QCheckBox("использовать")
            c.setChecked(active)
            c.setFont(FONT_SMALL_DEF)
            c.clicked.connect( self.state_update )
            self.states_checkers.append( c )
            row.addWidget(c)

            c = QW.QPushButton()
            c.setFont(FONT_SMALL_DEF)
            row.addWidget(c)

            self.grid.addLayout(row, i, )

    def state_update(self):
        states = [ x.isChecked() for x in self.states_checkers ]
        SerialAPI.setUsePortsState( states )
