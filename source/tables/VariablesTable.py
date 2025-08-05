from functools import partial
from typing import List

from PyQt6.QtWidgets import QTableWidget, QHeaderView, QPushButton, QComboBox, QTableWidgetItem
from PyQt6.QtCore import QPersistentModelIndex

from ..utils import (
    TableCheckbox,
    cbox_set_item,
    cbox_update_options,
    null_resize,
)


class VariablesTable(QTableWidget):
    """
    Table that tracks what variables a mouse currently running in a task has
    """

    def __init__(self, parent=None):
        super(QTableWidget, self).__init__(1, 7, parent=parent)
        self.headers = [
            "Variable",
            "Subject",
            "Value",
            "Persistent",
            "Summary",
            "Set",
            "",
        ]
        self.setHorizontalHeaderLabels(self.headers)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().setVisible(False)
        add_button = QPushButton("   add   ")
        self.setCellWidget(0, 5, add_button)
        self.n_variables = 0
        self.variable_names = []
        self.available_variables = []
        self.assigned = {
            v_name: [] for v_name in self.variable_names
        }  # Which subjects have values assigned for each variable.
        self.subject_variable_names = {}

    def remove_variable(self, variable_n: int) -> None:
        self.removeRow(variable_n)
        self.n_variables -= 1
        self.update_available()
        null_resize(self)

    def reset(self):
        """Clear all rows of table."""
        for i in reversed(range(self.n_variables)):
            self.removeRow(i)
        self.n_variables = 0
        self.assigned = {v_name: [] for v_name in self.variable_names}

    def add_variable(self, var_dict: dict = None) -> None:
        """Add a row to the variables table."""
        variable_cbox = QComboBox()
        variable_cbox.activated.connect(self.update_available)
        subject_cbox = QComboBox()
        subject_cbox.activated.connect(self.update_available)
        persistent = TableCheckbox()
        summary = TableCheckbox()
        set_var = TableCheckbox()

        set_var.checkbox.stateChanged.connect(partial(self.setVar_changed, self.n_variables))
        persistent.checkbox.stateChanged.connect(partial(self.persistent_changed, self.n_variables))
        remove_button = QPushButton("remove")
        ind = QPersistentModelIndex(self.model().index(self.n_variables, 2))
        remove_button.clicked.connect(lambda: self.remove_variable(ind.row()))
        add_button = QPushButton("   add   ")
        add_button.clicked.connect(self.add_variable)
        self.insertRow(self.n_variables + 1)
        self.setCellWidget(self.n_variables, 0, variable_cbox)
        self.setCellWidget(self.n_variables, 1, subject_cbox)
        self.setCellWidget(self.n_variables, 3, persistent)
        self.setCellWidget(self.n_variables, 4, summary)
        self.setCellWidget(self.n_variables, 5, set_var)
        self.setCellWidget(self.n_variables, 6, remove_button)
        self.setCellWidget(self.n_variables + 1, 6, add_button)
        if var_dict:  # Set cell values from provided dictionary.
            variable_cbox.addItems([var_dict["name"]])
            subject_cbox.addItems([var_dict["subject"]])
            value_item = QTableWidgetItem()
            value_item.setText(var_dict["value"])
            self.setItem(self.n_variables, 2, value_item)
            persistent.setChecked(var_dict["persistent"])
            summary.setChecked(var_dict["summary"])
            set_var.setChecked(var_dict["set"])
        else:
            variable_cbox.addItems(["select variable"] + self.available_variables)
            if self.n_variables > 0:  # Set variable to previous variable if available.
                v_name = str(self.cellWidget(self.n_variables - 1, 0).currentText())
                if v_name in self.available_variables:
                    cbox_set_item(variable_cbox, v_name)
                    subject_cbox.addItems(self.available_subjects(v_name))
        self.n_variables += 1
        self.update_available()
        null_resize(self)

    def persistent_changed(self, row: int) -> None:
        """A variables cannot be both persistent and set"""
        # print("updateing",row)
        self.cellWidget(row, 5).setChecked(False)
        self.item(row, 2).setText("auto")

    def setVar_changed(self, row: int) -> None:
        self.cellWidget(row, 3).setChecked(False)

    def update_available(self, i=None):
        # Find out what variable-subject combinations already assigned.
        self.assigned = {v_name: [] for v_name in self.variable_names}

        # to maintain consistency with main pycontrol, the way this works
        # is by setting variables assigned that
        for v_name in self.variable_names:
            for subject, vars_ in self.subject_variable_names.items():
                if v_name not in vars_:
                    self.assigned[v_name].append(subject)

        # print(self.assigned)
        for v in range(self.n_variables):
            v_name = self.cellWidget(v, 0).currentText()
            s_name = self.cellWidget(v, 1).currentText()
            if s_name and s_name not in self.subjects_in_group + ["all"]:
                cbox_set_item(self.cellWidget(v, 1), "", insert=True)
                continue
            if v_name != "select variable" and s_name:
                self.assigned[v_name].append(s_name)
        # Update the variables available:
        fully_asigned_variables = [v_n for v_n in self.assigned.keys() if "all" in self.assigned[v_n]]
        if self.subjects_in_group:
            fully_asigned_variables += [
                v_n for v_n in self.assigned.keys() if set(self.assigned[v_n]) == set(self.subjects_in_group)
            ]
        self.available_variables = sorted(list(set(self.variable_names) - set(fully_asigned_variables)), key=str.lower)
        # Update the available options in the variable and subject comboboxes.

        for v in range(self.n_variables):
            v_name = self.cellWidget(v, 0).currentText()
            s_name = self.cellWidget(v, 1).currentText()
            cbox_update_options(self.cellWidget(v, 0), self.available_variables)
            if v_name != "select variable":
                # If variable has no subjects assigned, set subjects to 'all'.
                if not self.assigned[v_name]:
                    self.cellWidget(v, 1).addItems(["all"])
                    self.assigned[v_name] = ["all"]
                    self.available_variables.remove(v_name)
                cbox_update_options(self.cellWidget(v, 1), self.available_subjects(v_name, s_name))

    def set_available_subjects(self, subjects: List[str]):
        self.subjects_in_group = subjects

    def set_variable_names(self, variable_names: List[str]):
        """ """
        if not self.variable_names:
            self.variable_names = variable_names
        else:
            # print(self.variable_names,variable_names)
            self.variable_names.extend(variable_names)
            self.variable_names = list(set(self.variable_names))

    def set_variable_names_by_subject(self, subject: str, variable_names: List[str]) -> None:
        """Allow tracking of which subject has which variables available
        to them in principle
        """
        self.subject_variable_names[subject] = variable_names

    def available_subjects(self, v_name, s_name=None):
        """Return sorted list of the subjects that are available for selection
        for the specified variable v_name given that subject s_name is already
        selected."""
        if (not self.assigned[v_name]) or self.assigned[v_name] == [s_name]:
            available_subjects = ["all"] + sorted(self.subjects_in_group)
        else:
            available_subjects = sorted(list(set(self.subjects_in_group) - set(self.assigned[v_name])))
        return available_subjects

    def variables_list(self) -> list[dict]:
        """Return the variables table contents as a list of dictionaries."""
        return [
            {
                "name": str(self.cellWidget(v, 0).currentText()),
                "subject": str(self.cellWidget(v, 1).currentText()),
                "value": str(self.item(v, 2).text()) if self.item(v, 2) else "",
                "persistent": self.cellWidget(v, 3).isChecked(),
                "summary": self.cellWidget(v, 4).isChecked(),
                "set": self.cellWidget(v, 5).isChecked(),
            }
            for v in range(self.n_variables)
        ]
