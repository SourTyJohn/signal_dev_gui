from PyQt5.QtGui import QFont


# graph view
POINTS_AT_ONCE = 100

# data
SAVED_DATA_LIMIT = 200  # SAVED_DATA_LIMIT >= POINTS_AT_ONCE
DATA_DIVIDER = '\t'

# analyze
MAX_DEVIATION_REST = 0.0150
MAX_DEVIATION_RISING = 0.250
DEVIATION_POINTS = 100
RECENT_DEVIATION_POINTS = 5
DO_NORMALIZE = True
RESTRAIN_K = 0.05

# serial com-port
READ_SPEED = 9600  # char / sec

PORT_READ_DELAY = 200  # ms
WRITE_TO_FILE_DELAY = 200  # ms
UI_UPDATE_DELAY = 200  # ms

# versions info
PROGRAM_VER = "1.1_Vector"
DEVICE_VER = "TGS_UnoWiFi_Proto"

# files
FILE_DEFAULTS = "*.txt"
SCRIPT_DEFAULTS = "*.py"
FILE_FORMAT = """[HEADER]
    version_program: {0}
    version_sensor: {1}
    date: {2}
    time: {3}
    use_sensors: {4}
[DATA]
{5}""".format(PROGRAM_VER, DEVICE_VER, "{0}", "{1}", "{2}", "{3}")
HEADER_ROWS = FILE_FORMAT.count("\n")
SKIP_COLUMNS = 2


FONT_SMALL_DEF = QFont("MS Sans Serif", 10, 1)

INFO_COLUMNS = 2
