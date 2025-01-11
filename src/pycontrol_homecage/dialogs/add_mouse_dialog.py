import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton
import pyqtgraph as pg

import pycontrol_homecage.db as database

class AddMouseDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Add Mouse Dialog')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.plotWidget = pg.PlotWidget()
        layout.addWidget(self.plotWidget)

        self.button = QPushButton('Close')
        self.button.clicked.connect(self.close)
        layout.addWidget(self.button)

        self.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = AddMouseDialog()
    dialog.show()
    sys.exit(app.exec_())