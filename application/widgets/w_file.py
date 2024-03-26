import PyQt5.QtWidgets as QW
import PyQt5.uic as uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot

from easygui import fileopenbox, filesavebox
from datetime import datetime

from constants import *
from utils.paths import Path
from utils.serialAPI import serial_api, SerialDataReceiver
from utils.widgets import MessageWindow
from utils.other import get_center


__all__ = (
    "FileWindow",
)


class FileWindow(SerialDataReceiver, QW.QMainWindow):
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
        uic.loadUi(Path.to_template("file.ui"), self)
        self.setWindowTitle("Анализатор Газов: Файл")
        self.setWindowIcon(QIcon(Path.to_images('icon.ico')))
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

        self.main_widget = QW.QWidget(self)
        self.main_widget.setLayout(self.layout_main)
        self.layout_main.setParent(self.main_widget)
        self.setCentralWidget(self.main_widget)

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
        if serial_api.blocked and not self.write_state:
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
                serial_api.getUsePortsState(),
                data
            )
        )

    @pyqtSlot()
    def getSerialData(self, data: list, saved_data: list):
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
