from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout


class CageSummaryDialog(QDialog):

    def __init__(self, parent=None):

        super(CageSummaryDialog, self).__init__(parent)

        self.setGeometry(10, 30, 300, 200)  # Left, top, width, height.

        self.textName = QLabel(self)
        self.textName.setText("Bleep bloop all sorts of summary information about")

        layout = QVBoxLayout(self)
        layout.addWidget(self.textName)
