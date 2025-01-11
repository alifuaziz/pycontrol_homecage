from pyqtgraph.Qt import QtGui


class MouseAdderTable(QtGui.QTableWidget):
    """ This table contains information about all mice currently running in the
        system """
    def __init__(self, GUI, parent=None):
        super(QtGui.QTableWidget, self).__init__(1, 7, parent=parent)

        self.header_names = ['Mouse_ID', 'RFID', 'Sex', 'Age', 'Experiment',
                             'Start_weight', 'Setup_ID']
        self.setHorizontalHeaderLabels(self.header_names)
        self.verticalHeader().setVisible(False)
        self.GUI = GUI
