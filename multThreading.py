from qtpy.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton
from qtpy.QtCore import Signal, QObject, QMetaObject, QThread


class WindowWorker(QObject):
    
    finished = Signal(str,str)
    def __init__(self):
        pass
    
    def run(self):
        self.finished.emit()