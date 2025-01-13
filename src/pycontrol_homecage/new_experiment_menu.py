import os
import time
from datetime import datetime

import pandas as pd
from pyqtgraph import Qt
from pyqtgraph.Qt import QtGui

from pycontrol_homecage.utils import get_tasks
from pycontrol_homecage.tables import (
    MouseListTable,
    NewExperimentSetupTable,
    VariablesTable,
)
import pycontrol_homecage.db as database


class new_experiment_dialog(QtGui.QDialog):
    """This Class represents a dialog that is used to configure the details of a new experiment"""

    def __init__(self, GUI, parent=None):
        super(new_experiment_dialog, self).__init__(parent)

        self.GUI = GUI
        self.setGeometry(100, 30, 1300, 600)  # Left, top, width, height.

        # Tempurary dataframe to store the setup information.
        self.df_setup_tmp = pd.DataFrame(
            columns=[
                "COM",
                "COM_AC",
                "Setup_ID",
                "in_use",
                "connected",
                "User",
                "Experiment",
                "Protocol",
                "Mouse_training",
                "Door",
                "n_mice",
            ]
        )

        # Tempruary dataframe to store the new mouse information
        self.df_mouse_tmp = pd.DataFrame(
            columns=[
                "Mouse_ID",
                "RFID",
                "Sex",
                "Age",
                "Experiment",
                "Protocol",
                "Stage",
                "Task",
                "User",
                "Start_date",
                "Current_weight",
                "Start_weight",
                "is_training",
                "is_assigned",
                "training_log",
                "Setup_ID",
                "in_system",
            ]
        )

        self.used_setups = []
        self.used_mice = []
        self.global_task = True
        self.running_protocol = False

        self.left_column = QtGui.QVBoxLayout()

        # Data related to experiment
        self.exp_name_groupbox = QtGui.QGroupBox("Status")

        self.expLabel = QtGui.QLabel()
        self.expLabel.setText("Experiment Name:")

        self.expName = QtGui.QLineEdit()

        self.protVtask = QtGui.QCheckBox("Run Protocol")
        self.protVtask.setChecked(False)
        self.protVtask.stateChanged.connect(self._prot_or_task)

        self.shared_protocol = QtGui.QCheckBox("Share Protocol")
        self.shared_protocol.setChecked(True)
        self.shared_protocol.stateChanged.connect(self._enable_prot_sel)

        self.protocol_combo = QtGui.QComboBox()
        self.available_tasks = get_tasks()
        self.protocol_combo.addItems(["Select Task"] + self.available_tasks)

        self.exp_GOButton = QtGui.QPushButton()  # First stage of specifying experiment whereby set name and (potentially) protocol
        self.exp_GOButton.setText("Set")
        self.exp_GOButton.clicked.connect(self.set_name)

        self.name_layout = QtGui.QHBoxLayout()
        self.name_layout2 = QtGui.QHBoxLayout()
        self.name_layout.addWidget(self.expLabel)
        self.name_layout.addWidget(self.expName)
        self.name_layout.addWidget(self.shared_protocol)
        self.name_layout.addWidget(self.protVtask)

        self.name_layout2.addWidget(self.protocol_combo)
        self.name_layout2.addWidget(self.exp_GOButton)

        self.nameVlayout = QtGui.QVBoxLayout()
        self.nameVlayout.addLayout(self.name_layout)
        self.nameVlayout.addLayout(self.name_layout2)
        self.exp_name_groupbox.setLayout(self.nameVlayout)

        # Column to add setups to the experiment
        self.setup_groupbox = QtGui.QGroupBox("Setups")

        self.setups_column = QtGui.QVBoxLayout()

        # populate this column

        # Controls for adding a setup to an experiment
        self.CAT = QtGui.QGroupBox("Add Setup")
        self.cat_layout = QtGui.QHBoxLayout()

        self.setup_combo = QtGui.QComboBox()
        self.available_setups = [
            rw["Setup_ID"]
            for kk, rw in database.setup_df.iterrows()
            if rw["connected"] and not rw["in_use"]
        ]
        self.setup_combo.addItems(["Select Setup"] + self.available_setups)
        self.setup_combo.currentTextChanged.connect(self.on_scb_changed)

        self.add_button = QtGui.QPushButton()
        self.add_button.setText("Add Setup")
        self.add_button.setEnabled(False)
        self.prot_label = Qt.QtWidgets.QLabel("Protocol:          ")  # protocol label
        self.exp_label = Qt.QtWidgets.QLabel("Experiemnt:         ")  # experiment label

        self.cat_layout.addWidget(self.setup_combo)
        self.cat_layout.addWidget(self.exp_label)
        self.cat_layout.addWidget(self.prot_label)

        self.cat_layout.addWidget(self.add_button)

        self.add_button.clicked.connect(self.add_cage)

        self.CAT.setLayout(self.cat_layout)

        #####################################################
        #############     Overview of setups     ############
        #####################################################
        self.CLT = NewExperimentSetupTable(GUI=self.GUI, tab=self)
        self.setups_column.addWidget(self.CAT, 1)
        self.setups_column.addWidget(self.CLT, 10)
        self.setup_groupbox.setLayout(self.setups_column)
        self.setup_groupbox.setEnabled(False)
        # self.CLT

        self.left_column.addWidget(self.exp_name_groupbox)
        self.left_column.addWidget(self.setup_groupbox)

        ###############################################################
        ###############################################################

        ####################################################
        #############      Mouse Adder Box      ############
        ####################################################

        self.MAT = QtGui.QGroupBox("Add Mouse")

        self.mat_layout = QtGui.QVBoxLayout()
        self.matL1 = QtGui.QHBoxLayout()
        self.matL2 = QtGui.QHBoxLayout()

        self.mouse_name_label = QtGui.QLabel("Mouse_ID:")
        self.mouse_name = QtGui.QLineEdit("")

        self.RFID_label = QtGui.QLabel("RFID:")
        self.RFID = QtGui.QLineEdit("")

        self.sex_label = QtGui.QLabel("Sex:")
        self.sex = QtGui.QComboBox()
        self.sex.addItems(
            [
                "F",
                "M",
            ]
        )

        self.age_label = QtGui.QLabel("Age (weeks):")
        self.age = QtGui.QLineEdit("")

        self.weight_label = QtGui.QLabel("Weight (g):")
        self.weight = QtGui.QLineEdit("")

        self.add_mouse_button = QtGui.QPushButton("Add Mouse")
        self.add_mouse_button.clicked.connect(self.add_mouse)

        self.mouse_prot = QtGui.QComboBox()
        self.mouse_prot.addItems(["Select Task"] + self.available_tasks)

        ###############################################################
        ###############################################################

        ####################################################
        ###########      Set Variables Table      ##########
        ####################################################
        self.filter_categories = ["Setup", "Mouse"]
        self.vars_filter_checkbox = QtGui.QCheckBox("Filter mice")

        self.vars_combo_type = QtGui.QComboBox()
        self.vars_combo_type.addItems(["Filter by"] + self.filter_categories)

        self.vars_combo_ID = QtGui.QComboBox()
        self.vars_combo_ID.addItems(["Filter by"] + self.filter_categories)

        # self.vars_hlayout1 = QtGui.QHBoxLayout(self)
        # self.vars_hlayout1.addWidget(self.vars_filter_checkbox)
        # self.vars_hlayout1.addWidget(self.vars_combo_type)
        # self.vars_hlayout1.addWidget(self.vars_combo_ID)
        # self.task_combo.currentIndexChanged.connect(self.picked_task)

        self.mouse_var_table = VariablesTable()

        ###############################################################
        ###############################################################

        self.matL1.addWidget(self.mouse_name_label)
        self.matL1.addWidget(self.mouse_name)

        self.matL1.addWidget(self.RFID_label)
        self.matL1.addWidget(self.RFID)

        self.matL1.addWidget(self.sex_label)
        self.matL1.addWidget(self.sex)

        self.matL2.addWidget(self.mouse_prot)
        self.matL2.addWidget(self.age_label)
        self.matL2.addWidget(self.age)

        self.matL2.addWidget(self.weight_label)
        self.matL2.addWidget(self.weight)
        self.matL2.addWidget(self.add_mouse_button)

        self.mat_layout.addLayout(self.matL1)
        self.mat_layout.addLayout(self.matL2)
        self.MAT.setLayout(self.mat_layout)

        self.MICE = QtGui.QGroupBox("Mouse Overview")
        self.mice_column = QtGui.QVBoxLayout()
        self.mouse_list_table = MouseListTable(tab=self)

        self.mice_column.addWidget(self.MAT)
        self.mice_column.addWidget(self.mouse_list_table)
        # self.mice_column.addLayout(self.vars_hlayout1)
        self.mice_column.addWidget(self.mouse_var_table)
        self.MICE.setLayout(self.mice_column)

        ####################################################
        #############      Run Experiments      ############
        ####################################################

        self.runGroup = QtGui.QGroupBox("Run")
        self.run_layout = QtGui.QHBoxLayout()
        self.run_button = QtGui.QPushButton("Run Protocol")
        self.run_button.clicked.connect(self.run_experiment)
        self.run_layout.addWidget(self.run_button)
        self.runGroup.setLayout(self.run_layout)

        self.right_column = QtGui.QVBoxLayout()
        self.right_column.addWidget(self.MICE)
        self.right_column.addWidget(self.runGroup)

        self.all_columns = QtGui.QHBoxLayout()
        self.all_columns.addLayout(self.left_column)
        self.all_columns.addLayout(self.right_column)

        self.vLayout = QtGui.QVBoxLayout(self)
        self.vLayout.addLayout(self.name_layout)
        self.vLayout.addLayout(self.all_columns)

        self.MICE.setEnabled(False)

    def _enable_prot_sel(self):
        if self.shared_protocol.isChecked():
            self.protocol_combo.setEnabled(True)
            self.exp_GOButton.setEnabled(False)
            self.global_task = True
        elif self.shared_protocol.isChecked() is False:
            self.protocol_combo.setEnabled(False)
            self.exp_GOButton.setEnabled(True)
            self.global_task = False

    def add_mouse(self):
        """Function to add a new mouse to the mouse dataframe."""

        try:
            NEW_RFID = int(self.RFID.text())
        except ValueError:
            QtGui.QMessageBox.warning(self, "Input Error", "RFID must be an integer.")
            return

        # get information from the GUI
        new_mouse_data = {
            "Mouse_ID": self.mouse_name.text(),
            "RFID": NEW_RFID,
            "Sex": self.sex.currentText(),
            "Age": self.age.text(),
            "Experiment": self.set_experiment_name,
        }

        # Check Mouse ID is allowed
        if (
            new_mouse_data["Mouse_ID"] in self.df_mouse_tmp["Mouse_ID"].values
            or new_mouse_data["Mouse_ID"] in database.mouse_df["Mouse_ID"].values
        ):
            QtGui.QMessageBox.warning(self, "Input Error", "Mouse ID already exists.")
            return
        # Check RFID is allowed
        if (
            new_mouse_data["RFID"] in self.df_mouse_tmp["RFID"].values
            or new_mouse_data["RFID"] in database.mouse_df["RFID"].values
        ):
            QtGui.QMessageBox.warning(self, "Input Error", "RFID already exists.")
            return

        entry_nr = len(self.df_mouse_tmp)
        # Initialise the new mouse row
        self.df_mouse_tmp.loc[entry_nr] = ["NA"] * len(self.df_mouse_tmp.columns)
        # Fill in the data for this mouse row
        self.df_mouse_tmp.loc[entry_nr]["Mouse_ID"] = new_mouse_data["Mouse_ID"]
        self.df_mouse_tmp.loc[entry_nr]["RFID"] = new_mouse_data["RFID"]
        self.df_mouse_tmp.loc[entry_nr]["Sex"] = new_mouse_data["Sex"]
        self.df_mouse_tmp.loc[entry_nr]["Age"] = new_mouse_data["Age"]
        self.df_mouse_tmp.loc[entry_nr]["Experiment"] = new_mouse_data["Experiment"]

        self.df_mouse_tmp.loc[entry_nr]["User"] = self.GUI.active_user
        self.df_mouse_tmp.loc[entry_nr]["Start_date"] = datetime.now().strftime(
            "%m/%d/%Y, %H:%M:%S"
        )
        self.df_mouse_tmp.loc[entry_nr]["Start_weight"] = self.weight.text()
        self.df_mouse_tmp.loc[entry_nr]["Current_weight"] = self.weight.text()

        self.df_mouse_tmp.loc[entry_nr]["is_training"] = False
        self.df_mouse_tmp.loc[entry_nr]["is_assigned"] = True

        if self.running_protocol:  # if you are going to run a whole protocol
            self.df_mouse_tmp.loc[entry_nr]["Protocol"] = self.mouse_prot.currentText()
            self.df_mouse_tmp.loc[entry_nr]["Task"] = "NA"
            self.df_mouse_tmp.loc[entry_nr]["Stage"] = 0
        else:  # if you are just running a task
            self.df_mouse_tmp.loc[entry_nr]["Task"] = self.mouse_prot.currentText()
            self.df_mouse_tmp.loc[entry_nr]["Protocol"] = (
                str(time.time()).replace(".", "") + "_task"
            )
            self.df_mouse_tmp.loc[entry_nr]["Stage"] = "NA"

        self.df_mouse_tmp.loc[entry_nr]["Setup_ID"] = self.CLT.selected_setups[0]
        self.mouse_list_table.fill_table()

    def _prot_or_task(self):
        if self.protVtask.isChecked():
            self.running_protocol = True
            self.protocol_combo.clear()
            self.available_tasks = [i for i in os.listdir(protocol_dir) if ".prot" in i]
            self.protocol_combo.addItems(["Select Protocol"] + self.available_tasks)

        else:
            self.running_protocol = False
            self.protocol_combo.clear()
            self.available_tasks = get_tasks(self.GUI.GUI_filepath)
            self.protocol_combo.addItems(["Select Task"] + self.available_tasks)

    def on_scb_changed(self):
        self.add_button.setEnabled(True)

    def set_name(self):
        # print(self.expName.text(),self.protocol_combo.currentIndex())
        if (self.expName.text() != "") and (
            (self.protocol_combo.currentIndex() != 0)
            or (self.shared_protocol.isChecked() is False)
        ):
            self.setup_groupbox.setEnabled(True)
            self.exp_name_groupbox.setEnabled(False)
            if self.shared_protocol.isChecked() is True:
                self.set_protocol = self.protocol_combo.currentText()
            else:
                self.set_protocol = None

            self.set_experiment_name = self.expName.text()
            self.prot_label.setText("Protocol: {}".format(self.set_protocol))
            self.exp_label.setText("Experiment: {}".format(self.set_experiment_name))
            # self.CAT._update_exp_params(self.set_protocol,self.set_experiment_name)

    def add_cage(self):
        if self.setup_combo.currentIndex() != 0:
            entry_nr = len(self.df_setup_tmp)

            # first fill row with NA
            self.df_setup_tmp.loc[entry_nr] = ["NA"] * len(self.df_setup_tmp.columns)

            COM = str(self.setup_combo.currentText())

            self.df_setup_tmp.loc[entry_nr]["Setup_ID"] = COM
            self.df_setup_tmp.loc[entry_nr]["Experiment"] = self.set_experiment_name
            self.df_setup_tmp.loc[entry_nr]["Protocol"] = self.set_protocol

            for col_name in database.setup_df.columns:
                if col_name not in ["Setup_ID", "Experiment", "Protocol"]:
                    val_ = database.setup_df.loc[
                        database.setup_df["Setup_ID"] == COM, col_name
                    ]

                    self.df_setup_tmp.loc[entry_nr][col_name] = val_.values[0]

        # print(self.exp_dialog.df_setup_tmp)
        self.CLT.fill_table()

    def _create_mouse_exp_log(self, mouse_ID):
        df_ = pd.DataFrame(
            columns=[
                "entry_time",
                "exit_time",
                "weight",
                "task",
                "Variables",
                "data_path",
            ]
        )
        pth_ = os.path.join(database.paths["mice_dir"], mouse_ID + ".csv")
        df_.to_csv(pth_)

    def run_experiment(self):
        """
        ADD WARNING IF YOU ARE DUPLICATING MOUSE NAMES OR RFIDS!!!!
        """
        ## Create all the paths for data
        exp_path = os.path.join(database.paths["data_dir"], self.set_experiment_name)
        if not os.path.isdir(exp_path):
            os.mkdir(exp_path)

            # update mouse information
            for ix, row in self.df_mouse_tmp.iterrows():
                mouse_exp_path = os.path.join(exp_path, row["Mouse_ID"])
                if not os.path.isdir(mouse_exp_path):
                    os.mkdir(mouse_exp_path)

                mouse_exp_task_path = os.path.join(mouse_exp_path, row["Protocol"])
                if not os.path.isdir(mouse_exp_task_path):
                    os.mkdir(mouse_exp_task_path)

                entry_nr = len(database.mouse_df)

                database.mouse_df.append(pd.Series(), ignore_index=True)
                # database.mouse_df.loc[entry_nr]
                for col in database.mouse_df.columns:
                    # conv_col_ix = self.mouse_df_tmp.col     #convereted column index
                    if col in self.df_mouse_tmp.columns:
                        database.mouse_df.loc[entry_nr, col] = row[col]

                self._create_mouse_exp_log(row["Mouse_ID"])

            database.mouse_df.to_csv(database.mouse_df.file_location)
            self.GUI.mouse_tab.mouse_table_widget.fill_table()

            # update experiment information
            entry_nr = len(database.exp_df)
            database.exp_df.append(pd.Series(), ignore_index=True)
            database.exp_df.loc[entry_nr, "Name"] = self.set_experiment_name
            database.exp_df.loc[entry_nr, "Setups"] = repr(
                self.df_setup_tmp["Setup_ID"].tolist()
            )
            database.exp_df.loc[entry_nr, "User"] = self.GUI.active_user
            database.exp_df.loc[entry_nr, "Protocol"] = self.set_protocol
            database.exp_df.loc[entry_nr, "Subjects"] = repr(
                self.df_mouse_tmp["Mouse_ID"].tolist()
            )
            database.exp_df.loc[entry_nr, "n_subjects"] = len(
                self.df_mouse_tmp["Mouse_ID"].values
            )
            database.exp_df.loc[entry_nr, "Active"] = True

            for stup in self.df_setup_tmp["Setup_ID"].values:
                database.setup_df.loc[database.setup_df["Setup_ID"] == stup, "User"] = (
                    self.GUI.active_user
                )

                database.setup_df.loc[
                    database.setup_df["Setup_ID"] == stup, "in_use"
                ] = "Y"

                database.setup_df.loc[
                    database.setup_df["Setup_ID"] == stup, "Experiment"
                ] = self.set_experiment_name
                database.setup_df.loc[
                    database.setup_df["Setup_ID"] == stup, "AC_state"
                ] = "allow_entry"
                database.setup_df.loc[
                    database.setup_df["Setup_ID"] == stup, "Door_Mag"
                ] = "0111"
                database.setup_df.loc[
                    database.setup_df["Setup_ID"] == stup, "Door_Sensor"
                ] = "1111"
                database.setup_df.loc[
                    database.setup_df["Setup_ID"] == stup, "Protocol"
                ] = self.set_protocol

                mices_ = (
                    self.df_mouse_tmp["Mouse_ID"]
                    .loc[self.df_mouse_tmp["Setup_ID"] == stup]
                    .values
                )
                database.setup_df.loc[
                    database.setup_df["Setup_ID"] == stup, "mice_in_setup"
                ] = str(mices_)[1:-1]

            database.exp_df.to_csv(database.exp_df.file_location)
            database.setup_df.to_csv(database.setup_df.file_location)
            self.GUI.setup_tab.setup_table_widget.fill_table()
            self.GUI.system_tab.setup_table_widget.fill_table()
            self.GUI.system_tab.experiement_overview_table.fill_table()

            self.accept()

        else:
            msg = QtGui.QMessageBox()
            msg.setIcon(QtGui.QMessageBox.Warning)
            msg.setText("This experiment already exists you need a unique experiment")
            msg.exec_()
