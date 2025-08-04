from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QComboBox,
    QPushButton,
    QCheckBox,
    QTextEdit,
)
from PyQt6.QtGui import QFont, QTextCursor

from ..utils import get_tasks
import db as database
from source.communication.messages import MessageRecipient


class DirectPyboardDialog(QDialog):
    """In this dialog, the idea is that you can directly run scripts on
    the pyboard. This is useful for e.g. flushing solenoids or testing
    a task.
    """

    def __init__(self, setup_id, parent=None):
        super(DirectPyboardDialog, self).__init__(parent)
        self.setGeometry(10, 30, 500, 200)  # Left, top, width, height.
        self.setup_id = setup_id
        self.selected_task = "None"

        # POint to PYC board
        self.board = database.controllers[self.setup_id].board
        self.reject = self._done

        # Layout
        layoutH = QHBoxLayout(self)
        self.task_combo = QComboBox()
        self.task_combo.addItems(["None"] + get_tasks())

        self.start_stop_button = QPushButton("Start")
        self.start_stop_button.clicked.connect(self.start_stop)

        # self.onClose_chechbox = QtGui.Qte
        self.onClose_chechbox = QCheckBox("Stop task when closing dialog?")
        self.onClose_chechbox.setChecked(True)

        layout2 = QVBoxLayout(self)
        layout2.addWidget(self.task_combo)
        layout2.addWidget(self.onClose_chechbox)
        layout2.addWidget(self.start_stop_button)

        self.log_textbox = QTextEdit()
        self.log_textbox.setFont(QFont("Courier", 9))
        self.log_textbox.setReadOnly(True)

        layoutH.addLayout(layout2)
        layoutH.addWidget(self.log_textbox)
        database.print_consumers[MessageRecipient.direct_pyboard_dialog] = self.print_msg

    def start_stop(self):
        """Button that allows you to start and stop task"""
        if self.start_stop_button.text() == "Start":
            self.selected_task = self.task_combo.currentText()
            if self.task_combo.currentText() != "None":
                self.print_msg("Uploading: " + str(self.selected_task))
                self.board.setup_state_machine(sm_name=self.selected_task)
                self.board.start_framework()
            self.start_stop_button.setText("Stop")
        elif self.start_stop_button.text() == "Stop":
            self.board.stop_framework()
            self.start_stop_button.setText("Start")

    def _done(self) -> None:
        if self.onClose_chechbox.isChecked():
            self.board.stop_framework()  # stop the framework

        del database.print_consumers[MessageRecipient.direct_pyboard_dialog]
        self.accept()  # close the dialog

    def print_msg(self, msg: str):
        """Function to accept data from the system handler"""
        self.log_textbox.moveCursor(QTextCursor.End)
        self.log_textbox.insertPlainText(str(msg) + "\n")
        self.log_textbox.moveCursor(QTextCursor.End)
