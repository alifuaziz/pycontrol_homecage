from pyqtgraph.Qt import QtGui


class MouseSummaryDialog(QtGui.QDialog):

    def __init__(self, parent=None):

        super(MouseSummaryDialog, self).__init__(parent)

        self.setGeometry(10, 30, 300, 200)  # Left, top, width, height.

        self.textName = QtGui.QLabel(self)
        self.textName.setText("Bleep bloop all sorts of summary information about")

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.textName)
