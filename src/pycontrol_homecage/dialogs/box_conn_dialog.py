from PyQt5.QtWidgets import QDialog, QLineEdit, QVBoxLayout


class BoxConnectionDialog(QDialog):

    def __init__(self, parent=None):
        super(BoxConnectionDialog, self).__init__(parent)
        self.textbox = QLineEdit(self)
        self.textbox.setText("You must be connected to the setup to update it")
        layout = QVBoxLayout(self)
        layout.addWidget(self.textbox)
