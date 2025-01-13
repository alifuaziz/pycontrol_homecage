# GUI
from PyQt5.QtWidgets import (
    QDialog,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
)
from PyQt5.QtGui import QFont, QTextCursor

# repo
import pycontrol_homecage.db as database
from pycontrol_homecage.com.messages import MessageRecipient
from pycontrol_homecage.com.access_control import Access_control


class CalibrationDialog(QDialog):
    """
    Simple dialog box that allows you to tare and callibrate the scales of the access control module.
    - This is primarily just an wrapper around the functions of the Access_control pyboard, with an output
    that writes to a the dialog box itself.
    Parameter
    ==============
    Access_control: A wrapper around the pyboard class that has specific functions for
    """

    def __init__(self, access_control_pyboard: Access_control = None):
        super(CalibrationDialog, self).__init__(None)

        self.access_control = access_control_pyboard
        self.reject = self._done

        self.setGeometry(10, 30, 400, 200)  # Left, top, width, height.

        self._setup_buttons()
        self._setup_calibration_weight_lineedit()
        self._set_dialog_layout()
        database.print_consumers[MessageRecipient.calibrate_dialog] = self.print_msg

    def _setup_buttons(self) -> None:
        self.buttonDone = QPushButton("Done")
        self.buttonDone.clicked.connect(self._done)

        self.buttonTare = QPushButton("Tare", self)
        self.buttonTare.clicked.connect(self.tare)

        self.buttonWeigh = QPushButton("Weigh", self)
        self.buttonWeigh.clicked.connect(self.weigh)

        self.buttonCal = QPushButton("callibrate", self)
        self.buttonCal.clicked.connect(self.callibrate)

    def _setup_calibration_weight_lineedit(self) -> None:
        self.calibration_weight = QLineEdit("")
        self.log_textbox = QTextEdit()
        self.log_textbox.setFont(QFont("Courier", 9))
        self.log_textbox.setReadOnly(True)

    def _set_dialog_layout(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self.buttonWeigh)
        layout.addWidget(self.buttonTare)
        layout.addWidget(self.calibration_weight)
        layout.addWidget(self.buttonCal)
        layout.addWidget(self.buttonDone)

        layoutH = QHBoxLayout(self)

        layoutH.addLayout(layout)
        layoutH.addWidget(self.log_textbox)

    def tare(self) -> None:
        """Tell access control module to tare the scales"""
        self.access_control.serial.write(b"tare")

    def callibrate(self) -> None:
        """Tell access control module to callibrate the scales"""
        cw = self.calibration_weight.text()
        str_ = "calibrate:" + cw
        self.access_control.serial.write(str_.encode())

        # write to
        self.log_textbox.moveCursor(QTextCursor.End)
        self.log_textbox.insertPlainText(
            "Target calibration weight: " + str(cw) + "g\n"
        )
        self.log_textbox.moveCursor(QTextCursor.End)

    def weigh(self) -> None:
        self.access_control.serial.write(b"weigh")

    def _done(self) -> None:
        del database.print_consumers[MessageRecipient.calibrate_dialog]
        self.accept()

    def print_msg(self, msg: str) -> None:
        "print weighing messages"
        self.log_textbox.moveCursor(QTextCursor.End)

        if "calT" in msg:
            self.log_textbox.insertPlainText(
                "Weight after Tare: " + msg.replace("calT:", "") + "g\n"
            )
        elif "calW" in msg:
            self.log_textbox.insertPlainText(
                "Weight: " + msg.replace("calW:", "") + "g\n"
            )
        if "calC" in msg:
            self.log_textbox.insertPlainText(
                "Measured post-calibration weight: " + msg.replace("calC:", "") + "g\n"
            )
        self.log_textbox.moveCursor(QTextCursor.End)
