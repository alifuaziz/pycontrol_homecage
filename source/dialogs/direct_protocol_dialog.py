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

import pandas as pd
import os

import db as database
from source.gui.settings import user_folder
from source.communication.messages import MessageRecipient


class DirectProtocolDialog(QDialog):
    """Dialog that tests wether a protocol can run on a setup"""

    def __init__(self, setup_id, parent=None):
        super(DirectProtocolDialog, self).__init__(parent)
        pass
        self.setup_id = setup_id
        self.board = database.controllers[self.setup_id].board
        self.setup_df = database.setup_df
        self.global_layout = QHBoxLayout(self)

        # Initialise Layout
        # Get the protocol
        self.protocol_name = self.setup_df.loc[self.setup_df["Setup_ID"] == self.setup_id, "Protocol"].values
        # Load in the protocol as a csv (even though it ends with a .prot)
        path = self.user_folder("protocol_dir") + self.protocol_name
        self.protocol_df = pd.read_csv(path)

        # Get the list of tasks from the tasks column of the protocol
        self.tasks = self.protocol_df["tasks"].tolist()
        self.task_dir = self.user_folder("task_dir")
        # Check if it is the tasks in the protocol list are valid tasks (they are in the tasks directory)#
        self.available_tasks = [
            task for task in self.tasks if os.path.isfile(os.path.join(self.task_dir, f"{task}.py"))
        ]

    def add_tasks_to_combo_box(self):
        """"""

    def upload_task(self, task):
        """Function to upload the selected task, to the pyControl board"""
        pass
