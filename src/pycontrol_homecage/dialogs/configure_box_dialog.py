import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QTextEdit, QFileDialog
from PyQt5.QtGui import QFont, QTextCursor

import pycontrol_homecage.db as database
from paths import paths
from pycontrol_homecage.com.messages import MessageRecipient


class ConfigureBoxDialog(QDialog):
    """Dialog window that allows you to upload hardware definitions etc"""

    def __init__(self, setup_id, parent=None):
        super(ConfigureBoxDialog, self).__init__(parent)
        self.setGeometry(10, 30, 500, 200)  # Left, top, width, height.
        layoutH = QHBoxLayout(self)

        self.load_framework_button = QPushButton("Load Pycontrol \nframework", self)
        self.load_framework_button.clicked.connect(self.load_framework)

        self.load_ac_framework_button = QPushButton("Load Access control \nframework", self)
        self.load_ac_framework_button.clicked.connect(self.load_ac_framework)
        self.load_hardware_definition_button = QPushButton("Load hardware definition", self)
        self.load_hardware_definition_button.clicked.connect(self.load_hardware_definition)
        self.disable_flashdrive_button = QPushButton("Disable flashdrive")
        layout2 = QVBoxLayout(self)
        layout2.addWidget(self.load_framework_button)
        layout2.addWidget(self.load_hardware_definition_button)
        layout2.addWidget(self.disable_flashdrive_button)
        layout2.addWidget(self.load_ac_framework_button)

        self.ac = database.controllers[self.setup_id].AC
        self.reject = self._done

        # self.setGeometry(10, 30, 400, 200) # Left, top, width, height.
        self.buttonDone = QPushButton("Done")
        self.buttonDone.clicked.connect(self._done)
        self.buttonTare = QPushButton("Tare", self)
        self.buttonTare.clicked.connect(self.tare)
        self.buttonWeigh = QPushButton("Weigh", self)
        self.buttonWeigh.clicked.connect(self.weigh)
        self.calibration_weight = QLineEdit("")
        self.buttonCal = QPushButton("callibrate", self)
        self.buttonCal.clicked.connect(self.callibrate)
        self.log_textbox = QTextEdit()
        self.log_textbox.setFont(QFont("Courier", 9))
        self.log_textbox.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addWidget(self.buttonWeigh)
        layout.addWidget(self.buttonTare)
        layout.addWidget(self.calibration_weight)
        layout.addWidget(self.buttonCal)
        layout.addWidget(self.buttonDone)

        layoutH.addLayout(layout2)
        layoutH.addLayout(layout)
        layoutH.addWidget(self.log_textbox)
        database.print_consumers[MessageRecipient.configure_box_dialog] = self.print_msg

    def load_ac_framework(self):

        self.log_textbox.insertPlainText("Loading access control framework...")
        database.controllers[self.setup_id].AC.reset()
        database.controllers[self.setup_id].AC.load_framework()
        self.log_textbox.insertPlainText("done!")

    def load_framework(self):
        self.log_textbox.insertPlainText("Loading framework...")
        self.log_textbox.moveCursor(QTextCursor.End)
        self.log_textbox.insertPlainText("done!")
        self.log_textbox.moveCursor(QTextCursor.End)

    def disable_flashdrive(self):
        database.controllers[self.setup_id].PYC.disable_flashdrive()

        hwd_path = QFileDialog.getOpenFileName(
            self,
            "Select hardware definition:",
            os.path.join(paths["config_dir"], "hardware_definition.py"),
            filter="*.py",
        )[0]

        self.log_textbox.insertPlainText("uploading hardware definition...")
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)

        database.controllers[self.setup_id].PYC.load_hardware_definition(hwd_path)
        self.log_textbox.insertPlainText("done!")
        # setup.load_hardware_definition(hwd_path)

    def tare(self):
        self.ac.serial.write(b"tare")

    def callibrate(self):
        cw = self.calibration_weight.text()
        str_ = "calibrate:" + cw
        self.ac.serial.write(str_.encode())

        self.log_textbox.moveCursor(QTextCursor.End)
        self.log_textbox.insertPlainText("Target calibration weight: " + str(cw) + "g\n")
        self.log_textbox.moveCursor(QTextCursor.End)

    def weigh(self):
        self.ac.serial.write(b"weigh")

    def _done(self):
        del database.print_consumers[MessageRecipient.configure_box_dialog]
        self.accept()

    def print_msg(self, msg: str):
        "print weighing messages"
        self.log_textbox.moveCursor(QTextCursor.End)

        if "calT" in msg:
            self.log_textbox.insertPlainText("Weight after Tare: " + msg.replace("calT:", "") + "g\n")
        elif "calW" in msg:
            self.log_textbox.insertPlainText("Weight: " + msg.replace("calW:", "") + "g\n")
        if "calC" in msg:
            self.log_textbox.insertPlainText("Measured post-calibration weight: " + msg.replace("calC:", "") + "g\n")
        self.log_textbox.moveCursor(QTextCursor.End)
