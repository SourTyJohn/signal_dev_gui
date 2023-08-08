from PyQt5 import QtWidgets as QW

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import numpy as np

from constants import *

from typing import Union
import importlib.util
import sys
import serial


__all__ = (
    "MessageWindow",
    "GraphCanvas",

    "serial_ports",
    "SerialAPI",

    "get_center",
    "load_script"
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


class SerialAPI:
    __saved_data = []
    __port: serial.Serial = None
    __blocked: bool = True

    __use_sensors = []
    __use_sensors_names = []
    __sensors_amount = 0

    @classmethod
    def flush(cls):
        cls.__port.flush()
        cls.__port.flushInput()
        cls.__port.flushOutput()

    @classmethod
    def usePort(cls, port_name: str) -> int:
        if cls.__port:
            cls.__port.close()

        try:
            port = serial.Serial(port_name, READ_SPEED)

            # ---------------------------------------------------
            raw_data = port.readline().decode("ascii", errors="ignore")
            data = raw_data.rstrip().split(DATA_DIVIDER)[1:]
            port.flush()

            cls.__sensors_amount = len(data)
            cls.setUsePortsState( [1, ] * cls.__sensors_amount )
            # ---------------------------------------------------

            cls.__port = port
            cls.__blocked = False
            return 0

        except serial.SerialException:
            cls.__blocked = True
            return 1

    @classmethod
    def readLine(cls, ) -> Union[list, None]:
        if cls.__blocked: return

        try:
            raw_data = cls.__port.readline().decode("ascii", errors="ignore")
            data = raw_data.rstrip().split(DATA_DIVIDER)[1:]

            data = [data[i] for i in range( len(data) ) if cls.__use_sensors[i]]

            cls.flush()

            if not data:
                data = cls.__saved_data[-1]

            cls.__saved_data.append( data )
            cls.__saved_data = cls.__saved_data[ -min(SAVED_DATA_LIMIT, len(cls.__saved_data)): ]
            return data

        except serial.SerialException:
            cls.disable()
            return None

    @classmethod
    def getSaved(cls, ) -> list:
        return cls.__saved_data

    @classmethod
    def sensorsState(cls, ) -> int:  # -1 - rest. 0 - stable. 1 - rising
        raw_data = cls.getSaved()
        length = len(raw_data)

        # long means
        data = raw_data[ -min(length, DEVIATION_POINTS): -min(length, RECENT_DEVIATION_POINTS)]
        arr = np.array(data, dtype=np.float64)
        means_long = np.mean(arr, axis=0, )

        # recent means
        data = raw_data[ -min(length, RECENT_DEVIATION_POINTS): ]
        arr = np.array( data, dtype=np.float64 )
        means_short = np.mean(arr, axis=0, )

        delta = means_long - means_short
        delta_ratio = delta / means_short

        rise, rest = 0, 0
        for d in delta_ratio:
            if d < 0 and abs(d) > MAX_DEVIATION_RISING:
                rise += 1
            elif d > 0 and abs(d) > MAX_DEVIATION_REST:
                rest += 1

        if rise == 0 and rest == 0:
            return 0
        elif rise >= rest:
            return 1
        else:
            return -1

    @classmethod
    def disable(cls) -> None:
        __blocked = True

    @classmethod
    def isDisabled(cls):
        return cls.__blocked

    @classmethod
    def setUsePortsState(cls, states):
        assert len(states) == cls.__sensors_amount
        if cls.__use_sensors != states:
            cls.__use_sensors = states
            cls.__use_sensors_names = [ str(x) for x in range( len(states) ) if cls.__use_sensors[x] ]
            cls.__saved_data.clear()

    @classmethod
    def getUsePortsState(cls):
        return cls.__use_sensors

    @classmethod
    def getNamings(cls):
        return cls.__use_sensors_names


def serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(32)]
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException) as e:
            if e.args[0].find("PermissionError") > 0:
                print(e)

    return result


def get_center():
    point = QW.QDesktopWidget().availableGeometry().center()
    return int( point.x() * 0.6 ), int( point.y() * 0.6 )


def load_script(file_name, module_name="ActiveLib"):
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_name)
        lib = importlib.util.module_from_spec( spec )
        sys.modules[module_name] = lib
        spec.loader.exec_module( lib )

        try:
            lib.load()
            lib.analyze()

        except AttributeError:
            return None, "Script must have load(text: str) and analyze(data: list) functions"

        except TypeError:
            pass

    except Exception as e:
        return None, e

    return lib, 0
