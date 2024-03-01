from PyQt5.QtWidgets import QApplication
from application.widgets.w_main import MainWindow


if __name__ == '__main__':
    app = QApplication(['App', ])
    window = MainWindow()
    window.show()
    app.exec_()
