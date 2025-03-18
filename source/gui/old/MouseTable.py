from functools import partial
from dataclasses import dataclass, asdict
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QLineEdit
import json
from ..utils import get_tasks
import db as database
from source.gui.settings import user_folder
from source.gui.utility import null_resize, cbox_update_options, cbox_set_item, TableCheckbox


@dataclass
class MouseProfile:
    """Represents the CamerasTab settings for one camera"""

    mouse_ID: str  # name
    RFID: int  # from the pin
    sex: str  # M / F
    age: int  # Weeks
    task: str


class MouseTable(QtWidgets.QTableWidget):
    """Table for specifying the setups and subjects used in experiment."""

    def __init__(self, config_experiment_tab):
        super(QtWidgets.QTableWidget, self).__init__(1, 4, parent=config_experiment_tab)
        self.setHorizontalHeaderLabels(["Mouse ID", "RFID", "Sex", "Age", "Task"])
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.cellChanged.connect(self.cell_changed)
        self.all_setups = set([])
        self.available_setups = []
        self.unallocated_setups = []
        self.subjects = []
        self.num_subjects = 0
        self.add_subject()
        self.config_experiment_tab = config_experiment_tab

    def reset(self):
        """Clear all rows of table."""
        for i in reversed(range(self.num_subjects)):
            self.removeRow(i)
        self.available_setups = sorted(list(self.all_setups))
        self.subjects = []
        self.num_subjects = 0

    def cell_changed(self, row, column):
        """If cell in subject row is changed, update subjects list and variables table."""
        if column == 2:
            self.update_subjects()
            self.config_experiment_tab.variables_table.update_available()

    def add_subject(self, setup=None, subject=None, do_run=None):
        """Add row to table allowing extra subject to be specified."""
        setup_cbox = QtWidgets.QComboBox()
        setup_cbox.addItems(self.available_setups if self.available_setups else ["select setup"])
        if self.unallocated_setups:
            setup_cbox.setCurrentIndex(self.available_setups.index(self.unallocated_setups[0]))
        setup_cbox.activated.connect(self.update_available_setups)
        remove_button = QtWidgets.QPushButton("remove")
        remove_button.setIcon(QtGui.QIcon("source/gui/icons/remove.svg"))
        ind = QtCore.QPersistentModelIndex(self.model().index(self.num_subjects, 2))
        remove_button.clicked.connect(lambda: self.remove_subject(ind.row()))
        add_button = QtWidgets.QPushButton("   add   ")
        add_button.setIcon(QtGui.QIcon("source/gui/icons/add.svg"))
        add_button.clicked.connect(self.add_subject)
        run_checkbox = TableCheckbox()
        if do_run is None:
            run_checkbox.setChecked(True)  # new subjects are set to "Run" by default
        else:
            run_checkbox.setChecked(do_run)
        self.setCellWidget(self.num_subjects, 0, run_checkbox)
        self.setCellWidget(self.num_subjects, 1, setup_cbox)
        self.setCellWidget(self.num_subjects, 3, remove_button)
        self.insertRow(self.num_subjects + 1)
        self.setCellWidget(self.num_subjects + 1, 3, add_button)
        if setup:
            cbox_set_item(setup_cbox, setup)
        if subject:
            subject_item = QtWidgets.QTableWidgetItem()
            subject_item.setText(subject)
            self.setItem(self.num_subjects, 2, subject_item)
        self.num_subjects += 1
        self.update_available_setups()
        null_resize(self)

    def remove_subject(self, subject_n):
        """Remove specified row from table"""
        if self.item(subject_n, 2):
            s_name = self.item(subject_n, 2).text()
            self.config_experiment_tab.variables_table.remove_subject(s_name)
        self.removeRow(subject_n)
        self.num_subjects -= 1
        self.update_available_setups()
        self.update_subjects()
        null_resize(self)

    def update_available_setups(self, i=None):
        """Update which setups are available for selection in dropdown menus."""
        selected_setups = set([str(self.cellWidget(s, 1).currentText()) for s in range(self.num_subjects)])
        self.available_setups = sorted(list(self.all_setups))
        self.unallocated_setups = sorted(list(self.all_setups - selected_setups))
        for s in range(self.num_subjects):
            cbox_update_options(self.cellWidget(s, 1), self.available_setups)

    def update_subjects(self):
        """Update the subjects list"""
        self.subjects = [str(self.item(s, 2).text()) for s in range(self.num_subjects) if self.item(s, 2)]

    def get_subjects_dict(self, filtered=False):
        """Return setups and subjects as a dictionary {subject:{'setup':setup,'run':run}}"""
        subjects_dict = {}
        for s in range(self.num_subjects):
            try:
                subject = str(self.item(s, 2).text())
            except AttributeError:
                return
            setup = str(self.cellWidget(s, 1).currentText())
            run = self.cellWidget(s, 0).isChecked()
            if filtered:
                if run:
                    subjects_dict[subject] = {"setup": setup, "run": run}  # add dict subject entry
            else:
                subjects_dict[subject] = {"setup": setup, "run": run}  # add dict subject entry
        return subjects_dict

    def set_from_dict(self, subjects_dict):
        """Fill table with subjects and setups from subjects_dict"""
        self.reset()
        for subject in subjects_dict:
            setup = subjects_dict[subject]["setup"]
            do_run = subjects_dict[subject]["run"]
            self.add_subject(setup, subject, do_run)
        self.update_available_setups()
        self.update_subjects()


class Mouse_table_item:
    """Class representing a singl mouse in the mouse table"""

    def __init__(self, mouse_table, mouse_id, RFID, sex, age, task):
        self.profile = MouseProfile(mouse_ID=mouse_id, RFID=RFID, sex=sex, age=age, task=task)
        self.mouse_table = mouse_table

        self.mouse_ID_edit = QLineEdit()
        if self.profile.mouse_ID:
            self.mouse_ID_edit.setText(self.profile.mouse_ID)
        else:
            self.mouse_ID_edit.setPlaceholderText("Set an mouse ID")
        self.mouse_ID_edit.editingFinished.connect(self.mouse_id_changed)

    def mouse_id_change(self):
        self.profile.mouse_ID = str(self.mouse_ID_edit.text())
        self.mouse_table.update_saved_profiles(self)
