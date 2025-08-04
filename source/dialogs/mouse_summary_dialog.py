import sys
from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout
from PyQt6.QtWidgets import QApplication


class MouseSummaryDialog(QDialog):

    def __init__(self, parent=None):

        super(MouseSummaryDialog, self).__init__(parent)

        self.setGeometry(10, 30, 300, 200)  # Left, top, width, height.

        self.textName = QLabel(self)
        self.textName.setText("Bleep bloop all sorts of summary information about a mouse")

        layout = QVBoxLayout(self)
        layout.addWidget(self.textName)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = MouseSummaryDialog()
    dialog.show()
    sys.exit(app.exec())
