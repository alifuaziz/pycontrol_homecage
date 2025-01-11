from PyQt5.QtWidgets import QDialog, QPushButton, QComboBox, QVBoxLayout, QApplication
# from pyqtgraph.Qt import QtGui
from pycontrol_homecage.utils import get_users
import sys


class LoginDialog(QDialog):
    """ Simple dialog window so that you can log in """
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)

        self.setGeometry(10, 30, 300, 200)  # Left, top, width, height.

        self.setWindowTitle('Login Selection')

        self.userID = None
        self.login_button = QPushButton('Login', self)
        self.login_button.clicked.connect(self.handle_login)
        self.combo = QComboBox()
        self.users = get_users()
        self.combo.addItems(['Select User'] + self.users)

        layout = QVBoxLayout(self)
        layout.addWidget(self.combo)
        layout.addWidget(self.login_button)

    def handle_login(self):
        if self.combo.currentText() != 'Select User':
            self.userID = self.combo.currentText()
            self.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = LoginDialog()
    if dialog.exec():
        print(f"Logged in as: {dialog.userID}")
    sys.exit(app.exec())