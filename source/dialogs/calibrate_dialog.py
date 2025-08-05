# GUI
from PyQt6.QtWidgets import (
    QDialog,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QGridLayout,
)
from PyQt6.QtGui import QFont, QTextCursor

# repo
import db as database
from source.communication.messages import MessageRecipient
from source.communication.access_control import Access_control
import sys
from functools import partial
from PyQt6.QtWidgets import QApplication


class CalibrationDialog(QDialog):
    """
    Simple dialog box that allows you to tare and callibrate the scales of the access control module.
    - This is primarily just an wrapper around the functions of the Access_control pyboard, with an output
    that writes to a the dialog box itself.
    Parameter
    ==============
    Access_control: A wrapper around the pyboard class that has specific functions for calibrating the loadcell which is connected to the access control.
    """

    def __init__(self, access_control_pyboard: Access_control = None):
        super(CalibrationDialog, self).__init__(None)

        self.access_control = access_control_pyboard
        self.reject = self._done
        # Window parameters
        self.setGeometry(10, 30, 500, 200)  # Left, top, width, height.
        self.setWindowTitle(f"Load Cell Calibration Dialog for Access Control: {self.access_control.serial_port}")
        self.setWhatsThis(
            "This is a dialog box that is currently connected to the access control.\nThe buttons below directly inteface with the loadcell on the pyboard.\n You should calibrate the scales so that your measurement units are correct!"
        )

        # GUI
        self.page_layout = QHBoxLayout(self)
        self._setup_buttons()
        self._set_dialog_layout()
        self._init_rfid_layout()
        self._init_door_layout()
        self._setup_calibration_weight_lineedit()
        database.print_consumers[MessageRecipient.calibrate_dialog] = self.print_msg

    def _setup_buttons(self) -> None:
        self.buttonDone = QPushButton("Close dialog")
        self.buttonDone.clicked.connect(self._done)

        self.buttonTare = QPushButton("Tare", self)
        self.buttonTare.clicked.connect(self.tare)

        self.buttonWeigh = QPushButton("Weigh", self)
        self.buttonWeigh.clicked.connect(self.weigh)

        self.buttonCal = QPushButton("Callibrate", self)
        self.buttonCal.clicked.connect(self.callibrate)

    def _setup_calibration_weight_lineedit(self) -> None:
        log_groupbox = QGroupBox("Log")
        log_layout = QVBoxLayout()

        self.log_textbox = QTextEdit()
        self.log_textbox.setFont(QFont("Courier", 9))
        self.log_textbox.setReadOnly(True)

        log_layout.addWidget(self.log_textbox)
        log_groupbox.setLayout(log_layout)

        self.page_layout.addWidget(log_groupbox)

    def _init_rfid_layout(self):
        """Vertical Layout for RFID"""
        rfid_groupbox = QGroupBox("RFID")
        rfid_layout = QHBoxLayout()
        rfid_button = QPushButton("Test RFID Scanner")
        rfid_button.clicked.connect(self.rfid_scan)
        rfid_layout.addWidget(rfid_button)
        rfid_groupbox.setLayout(rfid_layout)
        self.page_layout.addWidget(rfid_groupbox)

    def _init_door_layout(self):
        """Grid for the access control doors, RFID, Load cell calirabtation, log for the output (e.g. the value read by the rfid coil)"""
        door_layout_groupbox = QGroupBox("Door")

        door_layout = QGridLayout()
        task_room_enter_open = QPushButton("Enter Task Room: Open")
        task_room_enter_open.clicked.connect(partial(self.door_magnets, 1, "open"))
        task_room_enter_close = QPushButton("Enter Task Room: Close")
        task_room_enter_close.clicked.connect(partial(self.door_magnets, 1, "close"))
        task_room_exit_open = QPushButton("Exit Task Room: Open")
        task_room_exit_open.clicked.connect(partial(self.door_magnets, 2, "open"))
        task_room_exit_close = QPushButton("Exit Task Room: Close")
        task_room_exit_close.clicked.connect(partial(self.door_magnets, 2, "close"))

        access_control_enter_open = QPushButton("Enter Access Control: Open")
        access_control_enter_open.clicked.connect(partial(self.door_magnets, 3, "open"))
        access_control_enter_close = QPushButton("Enter Access Control: Close")
        access_control_enter_close.clicked.connect(partial(self.door_magnets, 3, "close"))
        access_control_exit_open = QPushButton("Exit Access Control: Open")
        access_control_exit_open.clicked.connect(partial(self.door_magnets, 4, "open"))
        access_control_exit_close = QPushButton("Exit Access Control: Close")
        access_control_exit_close.clicked.connect(partial(self.door_magnets, 4, "close"))

        # Add buttons to layout
        door_layout.addWidget(task_room_enter_open, 0, 0)
        door_layout.addWidget(task_room_exit_open, 0, 1)
        door_layout.addWidget(task_room_enter_close, 0, 2)
        door_layout.addWidget(task_room_exit_close, 0, 3)

        door_layout.addWidget(access_control_enter_open, 1, 0)
        door_layout.addWidget(access_control_exit_open, 1, 1)
        door_layout.addWidget(access_control_enter_close, 1, 2)
        door_layout.addWidget(access_control_exit_close, 1, 3)
        door_layout_groupbox.setLayout(door_layout)
        self.page_layout.addWidget(door_layout_groupbox)

    def _set_dialog_layout(self) -> None:
        load_cell_groupbox = QGroupBox("Loadcell")
        load_cell_layout = QVBoxLayout()
        load_cell_layout.addWidget(self.buttonWeigh)
        load_cell_layout.addWidget(self.buttonTare)

        self.calibration_weight = QLineEdit("")
        self.calibration_weight.setPlaceholderText("Enter calibration weight (g)")

        self.rowHoriLayout = QHBoxLayout()
        self.rowHoriLayout.addWidget(self.calibration_weight)
        self.rowHoriLayout.addWidget(self.buttonCal)

        load_cell_layout.addLayout(self.rowHoriLayout)
        load_cell_layout.addWidget(self.buttonDone)

        load_cell_groupbox.setLayout(load_cell_layout)
        self.page_layout.addWidget(load_cell_groupbox)

    def tare(self) -> None:
        """Tell access control module to tare the scales"""
        self.access_control.serial.write(b"tare")

    def callibrate(self) -> None:
        """Tell access control module to callibrate the scales. Defines what a unit of measurement is"""

        # Get text from the calibration textbox a
        cw = self.calibration_weight.text()
        # "calibrate" keyword calles the pycontrol's loadcell.calibrate() function to be called.
        str_ = "calibrate:" + cw
        # Write the calibration weight to serial port.
        self.access_control.serial.write(str_.encode())
        self.write_to_log_textbox(text="Target calibration weight: " + str(cw) + "g\n")

    def write_to_log_textbox(self, text: str = None) -> None:
        """write to log"""
        self.log_textbox.moveCursor(QTextCursor.MoveOperation.End)
        self.log_textbox.insertPlainText(text)
        self.log_textbox.moveCursor(QTextCursor.MoveOperation.End)

    def weigh(self) -> None:
        self.access_control.serial.write(b"weigh")

    def _done(self) -> None:
        del database.print_consumers[MessageRecipient.calibrate_dialog]
        self.accept()

    def door_magnets(self, door_idx: int = None, state: str = None):
        """Checking the locking and unlocking of the doors
        Two tests required:
        1. Should activate magnet_pin for each of the doors
        2. Should be able to read the signal pins for each of the doors.
        """
        # Construct message
        msg = f"door{door_idx}_{str(state)}"
        # write encoded message
        self.access_control.serial.write(msg.encode())

    def rfid_scan(self):
        """Does it scan the correct RFID correctly?

        CODE CALLED from the access control
        ============
        rfid = AC_handler.rfid.read_tag()
        pyb.delay(50)
        """
        self.access_control.serial.write(b"read_tag")

    def print_msg(self, msg: str) -> None:
        """Print the messages from the access control serial port to the cal dialog box"""
        self.log_textbox.moveCursor(QTextCursor.MoveOperation.End)

        if "calT" in msg:
            self.log_textbox.insertPlainText("Weight after Tare: " + msg.replace("calT:", "") + "g\n")
        if "calW" in msg:
            self.log_textbox.insertPlainText("Weight: " + msg.replace("calW:", "") + "g\n")
        if "calC" in msg:
            self.log_textbox.insertPlainText("Measured post-calibration weight: " + msg.replace("calC:", "") + "g\n")
        if "RFID:" in msg:
            self.log_textbox.insertPlainText("Measure RFID: " + msg.replace("RFID:"))
        if "mag" in msg:
            self.log_textbox.insertPlainText("Door info: " + msg.replace("mag", ""))
        self.log_textbox.moveCursor(QTextCursor.MoveOperation.End)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    access_control = Access_control(serial_port="COM7")  # Assuming you have a way to initialize this
    dialog = CalibrationDialog(access_control)
    dialog.show()
    sys.exit(app.exec())
