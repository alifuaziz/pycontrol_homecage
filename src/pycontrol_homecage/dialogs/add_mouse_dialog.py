import sys
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QPushButton,
    QGroupBox,
    QLabel,
    QLineEdit,
    QComboBox,
)

# import pycontrol_homecage.db as database
from pycontrol_homecage.utils import get_available_experiments, get_available_setups

class AddMouseDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.mouse_info_layout = QVBoxLayout()
        self.initUI()

        self.pageLayout()

    def initUI(self):
        self.setWindowTitle("Add a new mouse!")
        self.setGeometry(100, 100, 600, 400)

        self.mouse_groupbox = QGroupBox("New Mouse")
        self.label_mouse_id = QLabel()
        self.label_mouse_id.setText("Mouse ID:")
        self.input_mouse_id = QLineEdit(self)

        self.label_mouse_rfid = QLabel()
        self.label_mouse_rfid.setText("Mouse RFID:")
        self.input_mouse_rfid = QLineEdit(self)

        self.label_experiment = QLabel()
        self.label_experiment.setText("Experiment:")
        self.combo_experiment = QComboBox(self)
        # Replace with the eperiement list
        self.combo_experiment.addItems(get_available_experiments())

        # Setup
        self.label_setup = QLabel()
        self.label_setup.setText("Setup:")
        self.combo_setup = QComboBox(self)
        # Replace with the setup list
        self.combo_setup.addItems(get_available_setups())

        self.mouse_info_layout.addWidget(self.label_mouse_id)
        self.mouse_info_layout.addWidget(self.input_mouse_id)
        self.mouse_info_layout.addWidget(self.label_mouse_rfid)
        self.mouse_info_layout.addWidget(self.input_mouse_rfid)
        self.mouse_info_layout.addWidget(self.label_experiment)
        self.mouse_info_layout.addWidget(self.combo_experiment)
        self.mouse_info_layout.addWidget(self.label_setup)
        self.mouse_info_layout.addWidget(self.combo_setup)

        self.mouse_groupbox.setLayout(self.mouse_info_layout)

        self.add_mouse_button = QPushButton("Add New Mouse")
        self.add_mouse_button.clicked.connect(self.add_mouse)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)

    def add_mouse(self):
        """Add mouse, taking infomation from this page. This function will look very similar to the
        new_experiment_dialog.add_mouse button... so is workth thinking about that. Maybe their functionality could be moved to a util funciton."""
        pass

    def pageLayout(self):
        # Set layout
        self.dialog_layout = QVBoxLayout(self)
        self.dialog_layout.addWidget(self.mouse_groupbox)
        self.dialog_layout.addWidget(self.cancel_button)
        self.setLayout(self.dialog_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = AddMouseDialog()
    dialog.show()
    sys.exit(app.exec_())
