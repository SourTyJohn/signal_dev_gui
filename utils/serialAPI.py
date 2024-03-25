from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSlot

import sys
import serial

from constants import DATA_DIVIDER, SAVED_DATA_LIMIT, PORT_READ_DELAY


__all__ = (
    "serial_ports",
    "serial_api",
    "SerialDataReceiver"
)


class SerialPort:
    def __init__(self, port_name):
        try:
            self.__port = serial.Serial(port_name, timeout=0.2)

            # ---------------------------------------------------
            while not self.__port.readline().decode("ascii", errors="ignore"):
                self.__port.flush()
            # ---------------------------------------------------

            self.__blocked = False

        except serial.SerialException:
            self.port = None
            self.__blocked = True

    def checkError(self):
        return self.__port is None

    @property
    def blocked(self):
        return self.__blocked

    @blocked.setter
    def blocked(self, value: bool):
        self.__blocked = value

    def flush(self):
        self.__port.flush()
        self.__port.flushInput()
        self.__port.flushOutput()

    def readLine(self, use_sensors=None, **kwargs):
        if self.__blocked:
            return

        # ------- READ ---------------------------------------------------------
        raw_data = None
        try:
            raw_data = self.__port.readline().decode("ascii", errors="ignore")
            data = raw_data.rstrip().split(DATA_DIVIDER)[1:]
            self.flush()
        except serial.SerialException as ex:
            print(f'ERROR WHILE READING. Err: {ex}')
            print(f'DATA: {raw_data}')
            self.blocked = True
            return None
        # ----------------------------------------------------------------------

        # ------- USE_SENSORS --------------------------------------------------
        if use_sensors:
            data = [data_i for i, data_i in enumerate(data) if use_sensors[i]]
        # ----------------------------------------------------------------------

        # self.flush()
        return data

    def disconnect(self):
        self.__port.close()


class PortData:
    def __init__(self):
        self.__saved_data = []

    def saveData(self, data):
        self.__saved_data.append(data)
        self.__saved_data = self.__saved_data[-min(SAVED_DATA_LIMIT, len(self.__saved_data)):]

    def getSaved(self, ) -> list:
        return self.__saved_data

    def getLast(self):
        if self.__saved_data:
            return self.__saved_data[-1]
        return None

    def clear(self):
        self.__saved_data.clear()


class SerialAPIThread(QThread):
    def __init__(self, function, parent=None):
        super().__init__(parent)
        self.__function = function
        self.finished.connect(self.__function_wrapper)

    @pyqtSlot()
    def __function_wrapper(self):
        self.__function()
        self.msleep(PORT_READ_DELAY)
        self.start()

    def run(self) -> None:
        self.__function_wrapper()


class __SerialAPI:
    def __init__(self):
        self.port = None
        self.data = None
        self.__use_sensors = []
        self.__use_sensors_names = []

    # -------- THREAD ---------------------------------
    def __update_data(self):
        if self.blocked: return
        self.readLine()

    def __run_thread(self):
        self.thread = SerialAPIThread(self.__update_data)
        self.thread.start()
    # -------------------------------------------------

    def connect(self, port_name, ):
        if self.port:
            self.port.disconnect()
        self.port = SerialPort(port_name)
        self.data = PortData()

        # --------- USE_PORTS ------------------------
        self.port.readLine()
        self.setUsePortsState([1, ] * len(self.port.readLine()))
        # ------------------- ------------------------

        self.__run_thread()

        return self.port.blocked

    def readLine(self):
        _data = self.port.readLine(self.__use_sensors)
        prev_data = self.data.getLast()
        if prev_data is not None and len(_data) != len(prev_data):
            _data = prev_data
        self.data.saveData(_data)
        return _data

    @property
    def blocked(self):
        if self.port is None:
            return None
        return self.port.blocked

    @blocked.setter
    def blocked(self, value: bool):
        if self.port is not None:
            self.port.blocked = value

    def setUsePortsState(self, states):
        if self.__use_sensors != states:
            self.__use_sensors = states
            self.__use_sensors_names = [ str(x) for x in range( len(states) ) if self.__use_sensors[x] ]
            self.data.clear()

    def getUsePortsState(self):
        return self.__use_sensors

    def getNamings(self):
        return self.__use_sensors_names

    def getData(self):
        return self.data.getLast(), self.data.getSaved()


class SerialDataReceiver(object):
    __receivers = []

    def __new__(cls, *args, **kwargs):
        obj = super(cls.__bases__[1], cls).__new__(cls)
        SerialDataReceiver.__receivers.append(obj)
        return obj

    def getSerialData(self, data: list, saved_data: list):
        pass

    @classmethod
    def sendSerialData(cls, data: list, saved_data: list):
        for obj in cls.__receivers:
            if not hasattr(obj, "isVisible") or obj.isVisible():
                obj.getSerialData(data, saved_data)


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


serial_api = __SerialAPI()
