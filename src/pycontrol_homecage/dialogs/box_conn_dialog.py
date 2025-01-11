from pyqtgraph.Qt import QtGui


class BoxConnectionDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(BoxConnectionDialog, self).__init__(parent)
        self.textbox = QtGui.QLineEdit(self)
        self.textbox.setText("You must be connected to the setup to update it")
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.textbox)
