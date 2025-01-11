"""
This file has 2 important function
1. restart_experiment
2. stop_experiment

A lot of these functions are making sure the state of the experiment is correctly changed

"""

from typing import List, Optional

import pandas as pd
from PyQt5 import QtWidgets


from pycontrol_homecage.tables import ExperimentOverviewTable
from pycontrol_homecage.dialogs import AreYouSureDialog, InformationDialog
import pycontrol_homecage.db as database


class ExperimentOverviewTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(QtWidgets.QWidget, self).__init__(parent)
        self._init_buttons()
        self._set_button_layout()
        self.list_of_experiments = ExperimentOverviewTable(only_active=False)

        self._set_global_layout()

    def _init_buttons(self) -> None:
        self.new_experiment_button = QtWidgets.QPushButton("Start new Experiment")
        self.new_experiment_button.setToolTip(
            "Start a new experiment by adding mice to the connected setups"
        )
        self.new_experiment_button.clicked.connect(self.new_experiment)
        self.restart_experiment_button = QtWidgets.QPushButton("Restart Experiment")
        self.restart_experiment_button.clicked.connect(self.restart_experiment)
        self.stop_experiment_button = QtWidgets.QPushButton("Stop Experiment")
        self.stop_experiment_button.clicked.connect(self.stop_experiment)
        self.stop_experiment_button.setToolTip(
            "Button for stopping one experiment at a time. It stops the first one selected only"
        )

    def _set_button_layout(self) -> None:
        self.Hlayout = QtWidgets.QHBoxLayout()
        self.Hlayout.addWidget(self.new_experiment_button)
        self.Hlayout.addWidget(self.restart_experiment_button)
        self.Hlayout.addWidget(self.stop_experiment_button)

    def _set_global_layout(self) -> None:
        self.Vlayout = QtWidgets.QVBoxLayout(self)
        self.Vlayout.addLayout(self.Hlayout)
        self.Vlayout.addWidget(self.list_of_experiments)

    def new_experiment(self) -> None:
        """Button for starting a new experiment
        NOTE: Note implemented
        """
        # Raise dialog box that no boxes have been checked.
        dialog = InformationDialog(info_text="Function not implemented")
        dialog.exec()

    def restart_experiment(self) -> None:
        """Restart an experiment that is currently active that was running before"""

        selected_experiment = self._get_experiment_check_status()

        if selected_experiment:
            sure = AreYouSureDialog()
            sure.exec_()
            if sure.GO:
                # Update the experiment to be updated.
                exp_row = database.exp_df.loc[
                    database.exp_df.exp_df["Name"] == selected_experiment
                ]
                self._update_experiment_status(
                    experiment_name=selected_experiment, status=True
                )
                # Update the mice to be assigned to the experiment.
                mice_in_experiment = self._get_mice_in_experiment(exp_row=exp_row)
                self._update_mice(mice_in_exp=mice_in_experiment, assigned=True)
                # Update the setup(s) so that it is assigned to the experiement
                setups = self._get_setups_in_experiment(exp_row=exp_row)
                self._update_setups(
                    setups_in_exp=setups, experiment=selected_experiment
                )
                self._reset_tables()

    def stop_experiment(self):
        """
        Function for stopping one experiment at a time. It stops the first one selected only.
        """
        selected_experiment = self._get_experiment_check_status()

        # cannot abort multiple experiments simultaneously
        if selected_experiment:
            sure = AreYouSureDialog()
            sure.exec_()
            if sure.GO:
                # Update the experiment df to deactivate it
                exp_row = database.exp_df.loc[
                    database.exp_df["Name"] == selected_experiment
                ]
                self._update_experiment_status(selected_experiment, False)
                # Update the mice in the experiment to not be assigned to an experiment.
                mice_in_experiment = self._get_mice_in_experiment(exp_row)
                self._update_mice(mice_in_exp=mice_in_experiment, assigned=False)
                # Update the setups to be be assigned to no experiements.
                setups = self._get_setups_in_experiment(exp_row)
                self._update_setups(setups_in_exp=setups, experiment=None)

            self._reset_tables()

    def _update_experiment_status(self, experiment_name: str, status: bool) -> None:
        """
        Update experiement dataframe to reflect if these experiment is active or not.

        Params
        =======
        experiment_name: str
        status: bool
        """
        database.exp_df.loc[database.exp_df["Name"] == experiment_name, "Active"] = (
            status
        )

    def _get_mice_in_experiment(self, exp_row: pd.Series) -> List[str]:
        """Returns a list of mice in an experiement as a list of strings"""
        return eval(exp_row["Subjects"].values[0])

    def _get_setups_in_experiment(self, exp_row: pd.Series) -> List[str]:
        """Returns the list of Setups as a list of strings"""
        # setups = eval(exp_row['Setups'].values[0].replace(' ',',')) this may be better
        return eval(exp_row["Setups"].values[0])

    def _get_experiment_check_status(self) -> Optional[str]:
        """
        This function retrieves the name of the first experiment that is checked in a list of
        experiments.
        :return: The `_get_experiment_check_status` method returns the ID of the first checked
        experiment from the list of experiments if there is at least one experiment checked. If no
        experiments are checked, it returns `None`.
        """
        isChecked = []
        checked_ids = []
        name_col = self.list_of_experiments.header_names.index("Name")

        for row in range(self.list_of_experiments.rowCount()):
            checked = self.list_of_experiments.item(row, 0).checkState() == 2
            if checked:
                checked_ids.append(self.list_of_experiments.item(row, name_col).text())
                isChecked.append(checked)

        return checked_ids[0] if checked_ids else None

    def _reset_tables(self):
        self.parent._reset_tables()

    def _update_mice(self, mice_in_exp: List[str], assigned: bool = False):
        """Update the mice in the `mouse_df` to be assigned to an experiment. Save that dataframe to disk

        Args:
            mice_in_exp (List[str]): _description_
            assigned (bool, optional): _description_. Defaults to False.
        """
        for mouse in mice_in_exp:
            # Update status of mouse
            database.mouse_df.loc[
                database.mouse_df["Mouse_ID"] == mouse, "is_assigned"
            ] = assigned
            database.mouse_df.loc[
                database.mouse_df["Mouse_ID"] == mouse, "in_system"
            ] = assigned
            # Save to disk
            database.mouse_df.to_csv(database.mouse_df.file_location)

    def _update_setups(self, setups_in_exp, experiment=None):
        """Update the `setups_df`  to be assigned to tne experiment (argument to the function).
        Save this updated table to disk.
        """
        for setup in setups_in_exp:
            # Update which experiment is the setup is assigned to.
            database.setup_df.loc[
                database.setup_df["Setup_ID"] == setup, "Experiment"
            ] = experiment
            # If the setup has an experiment, then it is also in use.
            database.setup_df.loc[database.setup_df["Setup_ID"] == setup, "in_use"] = (
                experiment is not None
            )
            database.setup_df.to_csv(database.setup_df.file_location)

    def _refresh(self):
        pass

    def _get_checks(self, table):
        pass
