import PyQt5.QtWidgets as QW
import PyQt5.uic as uic
from PyQt5.QtGui import QIcon

from utils.paths import Path
from constants import FONT_SMALL_DEF
from utils.serialAPI import serial_api

__all__ = (
    "DeviceWindow",
)


class DeviceWindow(QW.QMainWindow):
    __instance = None

    b_refresh: QW.QVBoxLayout
    grid: QW.QGridLayout

    def __init__(self, parent):
        super().__init__(parent)
        uic.loadUi(Path.to_template("device.ui"), self)
        self.setWindowTitle("Анализатор Газов: Устройство")
        self.setWindowIcon(QIcon(Path.to_images('icon.ico')))

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

        for i, active in enumerate( serial_api.getUsePortsState() ):
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
        serial_api.setUsePortsState( states )
