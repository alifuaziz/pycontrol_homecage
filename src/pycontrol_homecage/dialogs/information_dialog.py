from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QApplication
import sys

class InformationDialog(QDialog):
    """
    pyqtgraph dialog box for displaying information text
    """
    def __init__(self, info_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Information")
        
        layout = QVBoxLayout()
        
        self.info_label = QLabel(info_text)
        layout.addWidget(self.info_label)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = InformationDialog("This is some information text.")
    dialog.exec()
    sys.exit(app.exec())