from PyQt5.QtWidgets import QDialog, QPushButton, QLabel, QHBoxLayout, QVBoxLayout
from pycontrol_homecage.utils import get_users


class AreYouSureDialog(QDialog):
    def __init__(self, parent=None):
        super(AreYouSureDialog, self).__init__(parent)

        self.setGeometry(10, 30, 300, 100)  # Left, top, width, height.
        self.users = get_users()

        self.yesButton = QPushButton("Yes", self)
        self.noButton = QPushButton("No", self)

        self.yesButton.clicked.connect(self.handleYes)
        self.noButton.clicked.connect(self.handleNo)

        self.Question = QLabel()
        self.Question.setText("Are you sure?")
        self._set_dialog_layout()

    def _set_dialog_layout(self) -> None:
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addWidget(self.noButton)
        self.buttonLayout.addWidget(self.yesButton)

        layoutV = QVBoxLayout(self)
        layoutV.addWidget(self.Question)
        layoutV.addLayout(self.buttonLayout)

    def handleYes(self) -> None:
        self.GO = True
        self.accept()

    def handleNo(self) -> None:
        self.GO = False
        self.accept()
