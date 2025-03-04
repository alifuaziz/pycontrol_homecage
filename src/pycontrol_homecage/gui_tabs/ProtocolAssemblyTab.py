from PyQt5.QtWidgets import (
    QWidget,
    QMainWindow,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QComboBox,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QFileDialog,
)
import os
import json
from functools import partial
import pandas as pd

from pycontrol_homecage.utils import get_variables_from_taskfile, get_tasks
from pycontrol_homecage.utils import validate_lineedit_number
from pycontrol_homecage.tables import ProtocolTable
import pycontrol_homecage.db as database
from pycontrol_homecage.dialogs import InformationDialog


class ProtocolAssemblyTab(QWidget):
    """
    This tab is used to create protocols. These are multi step training
    protocols that use variables from pycontrol scripts to advance between
    different stages of training.
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    THIS CODE IS NOT REALLY TESTED
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    """

    def __init__(self, parent: QMainWindow = None):
        super(QWidget, self).__init__(parent)

        self.GUI = self.parent()

        self.protocol_df = pd.DataFrame()
        self.stage_row = pd.Series(dtype="float64")
        self.task_variables = []

        # Name protocol

        # add stage to protocol
        self.ATP = QGroupBox("Add new stage to protocol")

        self.protocol_namer = QLineEdit("")
        self.protocol_namer_button = QPushButton("Set protocol name")
        self.protocol_namer_button.clicked.connect(self.set_protocol_name)

        self.clear_button = QPushButton("Clear Protocol")
        self.clear_button.clicked.connect(self.clear_all)

        self.save_button = QPushButton("Save Protocol")
        self.save_button.clicked.connect(self.save_protocol)

        self.load_button = QPushButton("Load Protocol")
        self.load_button.clicked.connect(self.load_protocol)

        self.add_stage_button = QPushButton("Add task stage")
        self.add_stage_button.clicked.connect(self.append_stage_to_protocol)

        self.task_combo = QComboBox()

        self.task_set_button = QPushButton("Set")
        self.task_set_button.clicked.connect(self.set_stage_task)
        self.task_set_button.setEnabled(False)

        self.available_tasks = get_tasks()
        self.task_combo.addItems(["Select Task"] + self.available_tasks)
        self.task_combo.currentIndexChanged.connect(self.picked_task)

        # track value stuff
        self.trackV_label = QLabel("Track value")
        self.trackV_combo = QComboBox()
        self.trackV_add = QPushButton("Add")
        self.trackV_add.clicked.connect(self.trackV_change)
        self.trackV_combo.setEnabled(False)

        # threshold value stuff
        self.threshV_label = QLabel("Threshold")
        self.threshV_combo = QComboBox()
        self.threshV_add = QPushButton("Add")
        self.threshV_add.clicked.connect(self.threshV_change)
        self.threshV_add.setToolTip(
            "Add threshold value (Any of these conditions being met will make the mouse proceed to the next stage when the mouse re-enters the task room"
        )

        self.threshV_combo.setEnabled(False)
        self.threshV_value = QLineEdit()
        self.threshV_value.textChanged.connect(partial(validate_lineedit_number, self.threshV_value, self.threshV_add))

        # Default value stuff
        self.defaultV_label = QLabel("Default value")
        self.defaultV_combo = QComboBox()
        self.defaultV_add = QPushButton("Add")
        self.defaultV_add.clicked.connect(self.defaultV_change)
        self.defaultV_value = QLineEdit()
        self.defaultV_value.textChanged.connect(
            partial(validate_lineedit_number, self.defaultV_value, self.defaultV_add)
        )

        self.defaultV_combo.setEnabled(False)

        self.Hlayout1 = QHBoxLayout()
        self.Hlayout2 = QHBoxLayout()
        self.Hlayout3 = QHBoxLayout()
        self.Hlayout4 = QHBoxLayout()

        self.Hlayout1.addWidget(self.protocol_namer)
        self.Hlayout1.addWidget(self.protocol_namer_button)
        self.Hlayout1.addWidget(self.task_combo)
        self.Hlayout1.addWidget(self.task_set_button)

        self.Hlayout2.addWidget(self.threshV_label)
        self.Hlayout2.addWidget(self.threshV_combo)
        self.Hlayout2.addWidget(self.threshV_value)
        self.Hlayout2.addWidget(self.threshV_add)

        self.Hlayout3.addWidget(self.defaultV_label)
        self.Hlayout3.addWidget(self.defaultV_combo)
        self.Hlayout3.addWidget(self.defaultV_value)
        self.Hlayout3.addWidget(self.defaultV_add)

        self.Hlayout4.addWidget(self.trackV_label)
        self.Hlayout4.addWidget(self.trackV_combo)
        self.Hlayout4.addWidget(self.trackV_add)
        # self.Hlayout4.addWidget(self.add_stage_button)

        self.Vlayout_add = QVBoxLayout()
        self.Vlayout_add.addLayout(self.Hlayout1)
        self.Vlayout_add.addLayout(self.Hlayout2)
        self.Vlayout_add.addLayout(self.Hlayout3)
        self.Vlayout_add.addLayout(self.Hlayout4)
        self.Vlayout_add.addWidget(self.add_stage_button)

        self.ATP.setLayout(self.Vlayout_add)

        self.protocol_table = ProtocolTable(tab=self)

        self.dummy_overview = QGroupBox("Current Stage Overview")
        self.dummy_layout = QVBoxLayout()
        self.protocol_table_dummy = ProtocolTable(tab=self, nRows=1)
        self.dummy_layout.addWidget(self.protocol_table_dummy)
        self.dummy_overview.setLayout(self.dummy_layout)

        self.Vlayout = QVBoxLayout(self)

        self.Vlayout.addWidget(self.ATP, 4)
        self.Vlayout.addWidget(self.dummy_overview, 1)
        self.Vlayout.addWidget(self.protocol_table, 10)

        self.save_clear_layout = QHBoxLayout()
        self.save_clear_layout.addWidget(self.clear_button)
        self.save_clear_layout.addWidget(self.save_button)
        self.save_clear_layout.addWidget(self.load_button)
        self.Vlayout.addLayout(self.save_clear_layout)

    ### Setting / Reseting the protocol construction data

    def reset(self):
        self.task_variables = []
        self.stage_row = pd.Series(dtype="float64")

        self.trackV_combo.clear()

        self.defaultV_combo.clear()
        self.defaultV_value.clear()

        self.threshV_combo.clear()
        self.threshV_value.clear()

        self.task_combo.setCurrentIndex(0)
        self.defaultV_combo.setEnabled(False)
        self.trackV_combo.setEnabled(False)
        self.threshV_combo.setEnabled(False)
        self.protocol_table_dummy.reset()

    def clear_all(self):
        "Start a new protocol"
        self.protocol_name = ""
        self.protocol_namer.clear()
        self.protocol_namer.setEnabled(True)
        # Reset the protocol variables
        self.protocol_df = pd.DataFrame()
        self.stage_row = pd.Series(dtype="float64")
        self.task_variables = []

        self.protocol_table.reset()

        self.reset()

    def set_stage_task(self):
        """set task for a given stage"""
        pth = os.path.join(database.paths["task_dir"], self.task_combo.currentText() + ".py")
        self.stage_row = pd.Series(
            {
                # "stage_nr": len(self.protocol_dict.index),
                "task": self.task_combo.currentText(),
                "trackV": [],
                "threshV": [],
                "defaultV": [],
                # "done": False,
            }
        )

        task_variables = get_variables_from_taskfile(pth)
        self.task_variables = task_variables if task_variables is not None else ["No Variables"]

        self._add_pycontrol_variables_to_combo_boxes()

        self.defaultV_combo.setEnabled(True)
        self.trackV_combo.setEnabled(True)
        self.threshV_combo.setEnabled(True)
        self.protocol_table_dummy.fill_row(stage_data=self.stage_row)

    def _add_pycontrol_variables_to_combo_boxes(self):
        """From the"""
        # Add the variables from the variable dict from the pyControl Task to all the combo boxes
        for combo_box, stage_dict_key in [
            (self.trackV_combo, "trackV"),
            (self.threshV_combo, "threshV"),
            (self.defaultV_combo, "defaultV"),
        ]:
            combo_box.addItems(
                ["Select"]
                + [v.replace("v.", "") for v in self.task_variables if v not in self.stage_row[stage_dict_key]]
            )

    ### Adding and removing task stages to overral protocol

    def append_stage_to_protocol(self):
        """Add Stage"""
        # self.protocol_dict[str(len(self.protocol_dict))] = self.stage_row.copy()
        self.protocol_df = pd.concat([self.protocol_df, self.stage_row.to_frame().T], ignore_index=True)
        # (Re)Fill the table with the new protocol dataframe
        self.protocol_table.fill_table(protocol_df=self.protocol_df)

        self.reset()

    def remove_stage_from_protocol(self, row_number: pd.Series):
        """Remove a stage based on the stage_idx
        If there stage is still temp then reset the temp.
        If the stage is part of the overall table, the remove it from that
        """

        self.protocol_df = self.protocol_df.drop(row_number).reset_index(drop=True)
        # Re-fill the table with the udpated protocold_dict
        self.protocol_table.fill_table(self.protocol_df)
        self.reset()

    def trackV_change(self):
        # if (
        #     self.trackV_combo.currentText() == "Select"
        # ):
        #     info = InformationDialog(info_text=f"Please select a value to track: {self.trackV_combo.currentText()} ")
        #     info.exec_()
        #     return
        # else:
        self.stage_row["trackV"].append(self.trackV_combo.currentText())
        self.trackV_combo.clear()
        self.trackV_combo.addItems(
            ["Select"] + [i.replace("v.", "") for i in self.task_variables if i not in self.stage_row["trackV"]]
        )
        self.trackV_combo.setCurrentIndex(0)
        self.protocol_table_dummy.fill_row(self.stage_row)

    def threshV_change(self):
        # if (
        #     self.trackV_combo.currentText() == "Select"
        # ):
        #     info = InformationDialog(info_text=f"Please select a value to track: {self.trackV_combo.currentText()}")
        #     info.exec_()
        #     return
        # else:
        self.stage_row["threshV"].append([self.threshV_combo.currentText(), self.threshV_value.text()])
        self.threshV_combo.clear()
        self.threshV_combo.addItems(
            ["Select"] + [i.replace("v.", "") for i in self.task_variables if i not in self.stage_row["threshV"][0]]
        )
        self.threshV_combo.setCurrentIndex(0)
        self.protocol_table_dummy.fill_row(self.stage_row)

    def defaultV_change(self):
        """"""
        self.stage_row["defaultV"].append([self.defaultV_combo.currentText(), self.defaultV_value.text()])
        self.defaultV_combo.clear()
        self.defaultV_combo.addItems(
            ["Select"] + [i.replace("v.", "") for i in self.task_variables if i not in self.stage_row["defaultV"][0]]
        )
        self.defaultV_combo.setCurrentIndex(0)
        self.protocol_table_dummy.fill_row(self.stage_row)

    def picked_task(self):
        """stupid helper to only allow selecting task once one has been selected"""
        if self.task_combo.currentText() != "Select Task":
            self.task_set_button.setEnabled(True)

    def set_protocol_name(self):
        """Sets the name of the protocol"""
        if self.protocol_namer.text() != "":
            protocol_name_temp = self.protocol_namer.text()
        else:
            info = InformationDialog(info_text="You must enter a name")
            info.exec_()
            return

        # Check if the protocol name is taken in the protocol directory
        protocol_dir = database.paths["protocol_dir"]
        if protocol_name_temp + ".prot" in os.listdir(protocol_dir):
            info = InformationDialog(
                info_text=f"Protocol name {protocol_name_temp}.prot already exists. Please choose a different name."
            )
            info.exec_()
            return

        self.protocol_name = protocol_name_temp
        self.protocol_namer.setEnabled(False)

    def _refresh(self):
        pass

    def save_protocol(self):
        save_path = os.path.join(database.paths["protocol_dir"], self.protocol_name + ".prot")
        print("Saving protocol:", save_path)
        # Save the protocal as a CSV with the extension as .prot
        self.protocol_df.to_csv(save_path)

    def load_protocol(self):
        protocol_dir = database.paths["protocol_dir"]
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Protocol File",
            protocol_dir,
            "Protocol Files (*.prot);;All Files (*)",
            options=options,
        )
        if file_name:
            self.protocol_df = pd.read_csv(file_name, index_col=0)
            self.protocol_table.fill_table(protocol_df=self.protocol_df)
            self.reset()
