import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pandas as pd
import cgitb
cgitb.enable( format = 'text')

def show_table(tableWidget, data=[], columns=[], df=[]):
    '''dataFrame 或者  list'''
    try:
        cols = len(columns) if columns else 0
        rows = len(data)
        if isinstance(df, pd.core.frame.DataFrame):
            columns = list(df.columns)
            cols = len(columns)
            rows = len(df)
        tableWidget.horizontalHeader().setVisible(True)  # 行头
        tableWidget.verticalHeader().setVisible(False)  # 列头
        # tableWidget.setSortingEnabled(True)  # 头排序
        tableWidget.setAlternatingRowColors(True)  # 设置间隔色
        tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)  # 单行
        tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)  # 不能编辑
        tableWidget.setRowCount(0)  # 行数
        tableWidget.setColumnCount(0)  # 列数
        tableWidget.setHorizontalHeaderLabels(columns)  # 字段名
        tableWidget.horizontalHeader().setStyleSheet("QHeaderView::section{background:rgb(85, 170, 255);}")  # 头颜色
        tableWidget.horizontalHeader().setVisible(True)  # 行头
        tableWidget.verticalHeader().setVisible(False)  # 列头
        tableWidget.setRowCount(rows)  # 行数
        tableWidget.setColumnCount(cols)  # 列数
        if isinstance(df, pd.core.frame.DataFrame):
            n = 0
            for i, row in df.iterrows():
                for j, x in enumerate(list(row)):
                    tableWidget.setItem(n, j, QTableWidgetItem(str(x)))
                n += 1
        elif data:
            for i, row in enumerate(data):
                for j, x in enumerate(row):
                    tableWidget.setItem(i, j, QTableWidgetItem(str(x)))
        for i in range(tableWidget.rowCount()):
            tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # 平均宽度
            tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # 平均宽度
            # QTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents) 设置自适应列宽
            # tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            # 设置tableWidget所有列的默认行高为20。
            # tableWidget.verticalHeader().setDefaultSectionSize(100)
            # 设置tableWidget所有行的默认列宽为20
            # tableWidget.horizontalHeader().setDefaultSectionSize(20)
            # tableWidget.verticalHeader().setMinimumHeight(100) 最新高度
    except Exception as e:
        print(e, e.__traceback__.tb_lineno)
class Gui1(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('软件程序')
        self.setWindowIcon(QApplication.style().standardIcon(13))

        self.resize(800,600)
        #最小化，最大化，关闭串口
        self.setWindowFlags(Qt.WindowMaximizeButtonHint|Qt.WindowMinimizeButtonHint|Qt.WindowCloseButtonHint)



        self.edit=QLineEdit()
        self.btn=QPushButton('确定')
        self.plain=QPlainTextEdit()


        hlayout=QHBoxLayout()
        hlayout.addWidget(self.edit) #stretch=5
        hlayout.addWidget(self.btn)
        #hlayout.addStretch(1)

        vlayout = QVBoxLayout()
        vlayout.addLayout(hlayout)
        vlayout.addWidget(self.plain)
        #vlayout.addStretch(1)



        self.setLayout(vlayout)
        self.btn.clicked.connect(self.do_work)
    def do_work(self):
        print(self.edit.text())
        self.plain.appendPlainText(self.edit.text())
class Gui2(QMainWindow):
    def __init__(self):
        '''
        app=QApplication(sys.argv)
        c=XXX()
        c.show()
        sys.exit(app.exec_())

        '''
        super().__init__()
        self.setWindowFlag(Qt.WindowMinMaxButtonsHint)

        self.resize(800,600)

        #设置样式
        qssStyle='''
        QPushButton{background-color:lightblue}
        StatusBar{background-color:green}
        '''
        self.setStyleSheet(qssStyle)
        self.setWindowTitle('软件程序')
        #设置logo
        self.setWindowIcon(QIcon('123.png'))
        self.setWindowIcon(QApplication.style().standardIcon(13))
        # 最小化，最大化，关闭串口
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        #菜单栏
        menubar= self.menuBar()
        menu1=menubar.addMenu('系统菜单')
        edit = menu1.addMenu("Edit")
        edit.addAction('xxx')
        edit.triggered[QAction].connect(self.action)


        self.edit=QLineEdit()
        self.btn=QPushButton('确定')
        self.plain=QPlainTextEdit()


        hlayout=QHBoxLayout()
        hlayout.addWidget(self.edit) #stretch=5
        hlayout.addWidget(self.btn)
        #hlayout.addStretch(1)

        vlayout = QVBoxLayout()
        vlayout.addLayout(hlayout)
        vlayout.addWidget(self.plain)
        #vlayout.addStretch(1)


        mainbox=QGroupBox()
        mainbox.setLayout(vlayout)

        self.setCentralWidget(mainbox)


        self.btn.clicked.connect(self.do_work)

        self.comNum = QLabel()
        self.baudNum = QLabel()
        self.statusBar().addPermanentWidget(self.comNum, stretch=0)
        self.statusBar().addPermanentWidget(self.baudNum, stretch=0)

        self.showBar('hello')

    def action(self):
        self.dl = QDialog(self)
        self.dl.setWindowTitle('xxx')
        self.dl.setWindowFlag(Qt.WindowCloseButtonHint)
        self.dl_edit = QLineEdit()
        self.dl_btn = QPushButton('yes')
        self.dl_btn.clicked.connect(lambda :print('111'))
        dl_hlayout=QHBoxLayout()
        dl_hlayout.addWidget(self.dl_edit)
        dl_hlayout.addWidget(self.dl_btn)

        dl_vlayout=QVBoxLayout()
        dl_vlayout.addLayout(dl_hlayout)
        self.dl.setLayout(dl_vlayout)
        self.dl.open()

    def showBar(self,msg,a='123',b='333'):
        self.statusBar().showMessage(msg)
        self.comNum.setText('串口号：{}'.format(a))
        self.baudNum.setText('波特率：{}'.format(b))
    def do_work(self):
        print(self.edit.text())
        self.statusBar().showMessage('hello')
        self.plain.appendPlainText(self.edit.text())
if __name__ == '__main__':
    app=QApplication(sys.argv)
    c=Gui2()
    c.show()
    sys.exit(app.exec_())


