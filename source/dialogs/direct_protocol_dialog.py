from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QComboBox,
    QPushButton,
    QCheckBox,
    QTextEdit,
)
from PyQt5.QtGui import QFont, QTextCursor

import pandas as pd
import os

import db as database
from paths import paths
from source.communication.messages import MessageRecipient


class DirectProtocolDialog(QDialog):
    """Dialog that tests wether a protocol can run on a setup"""

    def __init__(self, setup_id, parent=None):
        super(DirectProtocolDialog, self).__init__(parent)
        pass
        self.setup_id = setup_id
        self.PYC = database.controllers[self.setup_id].PYC
        self.setup_df = database.setup_df
        self.paths = paths

        self.global_layout = QHBoxLayout(self)
        self.initialise_layout()

        self.initialise_protocol()

    def initialise_layout(self):
        pass

    def initialise_protocol(self):

        # Get the protocol
        self.protocol_name = self.setup_df.loc[self.setup_df["Setup_ID"] == self.setup_id, "Protocol"].values
        # Load in the protocol as a csv (even though it ends with a .prot)
        path = self.paths["protocol_dir"] + self.protocol_name
        self.protocol_df = pd.read_csv(path)

        # Get the list of tasks from the tasks column of the protocol
        self.tasks = self.protocol_df["tasks"].tolist()
        self.task_dir = self.paths["task_dir"]

        # Check if it is the tasks in the protocol list are valid tasks (they are in the tasks directory)#
        self.available_tasks = [
            task for task in self.tasks if os.path.isfile(os.path.join(self.task_dir, f"{task}.py"))
        ]

        # Add these tasks to a combobox to be tested with the pyboard

        pass

    def add_tasks_to_combo_box(self):
        """"""

    def upload_task(self, task):
        """Function to upload the selected task, to the PYC board"""
        pass
