import sys
from qtpy.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QTabWidget
)
from qtpy.QtGui import QTextCursor, QTextCharFormat, QColor
from winController import *
from qtpy.QtCore import *
from qtpy.QtCore import Signal, QObject, QMetaObject, Qt , QTimer

class MainWindow(QWidget):
    def __init__(self,controller):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget(self)
        self.layout.addWidget(self.tab_widget)
        #self.add_new_tab("firstTab","text1","text2")
        self.controller = controller   
        self.controller.addNewTab.connect(self.addNewTab)
        self.controller.setTextLeft.connect(self.setTextLeft)
        self.controller.setTextRight.connect(self.setTextRight)
        self.controller.highlightLine.connect(self.highlightLine)
        self.controller.getRightTextByTabName.connect(self.getRightTextByTabName)
        self.widgetsByTab = list(tuple())
        self.IsLeftSlidePress = False
        self.IsRightSlidePress = False
        self.projectId = ""
  
    @Slot(str,str)
    def getRightTextByTabName(self,righttext,tabname):
        if ".pplc" in tabname:
            tabname = tabname.rstrip(".pplc")
        for widgets in self.widgetsByTab :
            if tabname in widgets[0]:
                tabName,text_zone_left,text_zone_right,leftScroll,rightScroll,button1,button2,button3, = widgets
                righttext = text_zone_right.toPlainText()
            else:
                righttext = ""
    
    @Slot(str,int,str,bool)
    def highlightLine(self,action,lineNumber,tabname,isleft):
        for widgets in self.widgetsByTab :
            if tabname in widgets[0]:                
                tabName,text_zone_left,text_zone_right,leftScroll,rightScroll,button1,button2,button3, = widgets
        
        if isleft:
            text_edit = text_zone_left
        else:
            text_edit = text_zone_right
        
        if action == "remove" :
            hColor = QColor("red")
        elif action == "add":
            hColor = QColor("green")
        elif action == "change":
            hColor = QColor("orange")
            
        cursor = text_edit.textCursor() 
        
        block = text_edit.document().findBlockByLineNumber(lineNumber)  
        if block.isValid():
            cursor.setPosition(block.position())
            text_edit.setTextCursor(cursor)
            cursor.select(QTextCursor.BlockUnderCursor)
        
        format = QTextCharFormat()
        format.setBackground(hColor) 

        cursor.mergeCharFormat(format)
        text_edit.setTextCursor(cursor)
    
    def setComparator(self,comparator):
        self.comparator = comparator
    
    def setProjectId(self,projectid):
        self.projectId = projectid
    
    def setProjectPath(self,path):
        self.path = path
               
    @Slot()
    def setOnMergeClicked(self):
        sender = self.sender()
        for widgets in self.widgetsByTab :
            if sender == widgets[6]:
                tabname = widgets[0]
                path = self.path +self.projectId
                self.comparator.mergeTexts(widgets[1].toPlainText(),widgets[2].toPlainText(),tabname,path)
                
            
    @Slot(str,str)     
    def setTextLeft(self,tabname,textLeft):
        for widgets in self.widgetsByTab :
            if tabname in widgets[0]:                
                tabName,text_zone_left,text_zone_right,leftScroll,rightScroll,button1,button2,button3, = widgets
                text_zone_left.setText(textLeft)
                
    @Slot(str,str)
    def setTextRight(self,tabname,textRight):
        for widgets in self.widgetsByTab :
            if tabname in widgets[0]:               
                tabName,text_zone_left,text_zone_right,leftScroll,rightScroll,button1,button2,button3, = widgets
                text_zone_right.setText(textRight)
        
    @Slot(str,str,str) 
    def addNewTab(self,tabName,textLeft,textRight) -> bool:
        # Create a new QWidget for the tab
        new_tab = QWidget()
        
        # Create the layout for the tab
        tab_layout = QVBoxLayout()
        
        # Add the two large text zones (QTextEdit widgets)
        text_zone_left = QTextEdit(new_tab)
        text_zone_right = QTextEdit(new_tab)
        
        text_zone_left.setReadOnly(True)
        text_zone_right.setReadOnly(True)
        
        text_zone_left.setText(textLeft)
        text_zone_right.setText(textRight)
        
        
        # Layout to place the two text zones side by side
        text_layout = QHBoxLayout()
        text_layout.addWidget(text_zone_left)
        text_layout.addWidget(text_zone_right)
        
        
        tab_layout.addLayout(text_layout)
        text_zone_left.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        text_zone_right.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        text_zone_left.setLineWrapMode(QTextEdit.NoWrap)
        text_zone_right.setLineWrapMode(QTextEdit.NoWrap)
        
        text_zone_left.verticalScrollBar().valueChanged.connect(self.synchScroll2)
        text_zone_right.verticalScrollBar().valueChanged.connect(self.synchScroll1)
        
        # Layout to hold the three buttons below
        button_layout = QHBoxLayout()
        button1 = QPushButton("Pull", new_tab)
        button2 = QPushButton("Merge", new_tab)
        button3 = QPushButton("Local", new_tab)
        
        button2.clicked.connect(self.setOnMergeClicked)
        
        button_layout.addWidget(button1)
        button_layout.addWidget(button2)
        button_layout.addWidget(button3)
        
        # Add the button layout to the main tab layout
        tab_layout.addLayout(button_layout)
        
        # Set the layout for the new tab
        new_tab.setLayout(tab_layout)
        
        # Add the new tab to the tab widget
        tab_index = self.tab_widget.addTab(new_tab, tabName)
        self.tab_widget.setCurrentIndex(tab_index)
        
        widgets = (tabName,text_zone_left,text_zone_right,text_zone_left.verticalScrollBar(),text_zone_right.verticalScrollBar(),button1,button2,button3)
        self.widgetsByTab.append(widgets)
        
        return True
    
    @Slot(int)
    def synchScroll1(self,value):
        sender = self.sender()        
        for widgets in self.widgetsByTab :
            if widgets[4] == sender:                    
                widgets[1].verticalScrollBar().setValue(value)
                widgets[1].textChanged.emit()
                
    @Slot(int)
    def synchScroll2(self,value):
        sender = self.sender()
        for widgets in self.widgetsByTab :
            if widgets[3] == sender:     
                widgets[4].setValue(value)
       