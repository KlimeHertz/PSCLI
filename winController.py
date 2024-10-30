from qtpy.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton
from qtpy.QtCore import Signal, QObject, QMetaObject

class WindowController(QObject):
    addNewTab = Signal(str,str,str)
    setTextLeft = Signal(str,str)
    setTextRight = Signal(str,str)
    highlightLine = Signal(str,int,str,bool)
    getRightTextByTabName = Signal(str,str)

    def __init__(self):
        super().__init__()