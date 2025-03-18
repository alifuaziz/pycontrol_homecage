import json
from pathlib import Path
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from source.gui.settings import get_setting, user_folder
from source.gui.utility import TableCheckbox, parallel_call
from source.gui.hardware_variables_dialog import Hardware_variables_editor
from source.communication.pycboard import Pycboard, PyboardError
from source.communication.access_control import Access_control
import random
import string
import os
from dataclasses import asdict, dataclass

# setup config -------------------------------------------------------------------


@dataclass
class Setup_config:
    name: str
    pyc_port: str
    ac_port: str


class Setups_tab(QtWidgets.QWidget):
    """The setups tab is used to name and configure setups, where one setup is one
    pyboard and connected hardware."""

    def __init__(self, GUI_main):
        super(QtWidgets.QWidget, self).__init__(GUI_main)

        # Variables
        self.GUI_main = GUI_main
        self.setups = {}  # Dictionary {serial_port:Setup_table_item}
        self.setup_names = []
        self.available_setups_changed = False

        # Select setups group box.
        self.setup_groupbox = QtWidgets.QGroupBox("Setups")

        self.select_all_checkbox = QtWidgets.QCheckBox("Select all")
        self.select_all_checkbox.stateChanged.connect(self.select_all_setups)

        self.setups_table = QtWidgets.QTableWidget(0, 5, parent=self)
        self.setups_table.setHorizontalHeaderLabels(
            ["Select", "Name", "Pycboard serial port", "AC board serial port", "Add/Remove"]
        )
        self.setups_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.setups_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setups_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.setups_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.setups_table.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.setups_table.verticalHeader().setVisible(False)
        self.setups_table.itemChanged.connect(lambda item: item.changed() if hasattr(item, "changed") else None)
        # Configuration buttons
        self.configure_group = QtWidgets.QGroupBox("Configure selected")
        load_fw_button = QtWidgets.QPushButton("Load frameworks")
        load_fw_button.setIcon(QtGui.QIcon("source/gui/icons/upload.svg"))
        load_hw_button = QtWidgets.QPushButton("Load hardware definition")
        load_hw_button.setIcon(QtGui.QIcon("source/gui/icons/upload.svg"))
        enable_flashdrive_button = QtWidgets.QPushButton("Enable flashdrive")
        enable_flashdrive_button.setIcon(QtGui.QIcon("source/gui/icons/enable.svg"))
        disable_flashdrive_button = QtWidgets.QPushButton("Disable flashdrive")
        disable_flashdrive_button.setIcon(QtGui.QIcon("source/gui/icons/disable.svg"))
        load_fw_button.clicked.connect(self.load_frameworks)
        load_hw_button.clicked.connect(self.load_hardware_definition)
        enable_flashdrive_button.clicked.connect(self.enable_flashdrive)
        disable_flashdrive_button.clicked.connect(self.disable_flashdrive)
        self.variables_btn = QtWidgets.QPushButton("Variables")
        self.variables_btn.setIcon(QtGui.QIcon("source/gui/icons/filter.svg"))
        self.variables_btn.clicked.connect(self.edit_hardware_vars)

        self.dfu_btn = QtWidgets.QPushButton("DFU mode")
        self.dfu_btn.setIcon(QtGui.QIcon("source/gui/icons/wrench.svg"))
        self.dfu_btn.clicked.connect(self.DFU_mode)

        config_layout = QtWidgets.QGridLayout()
        config_layout.addWidget(load_fw_button, 0, 0)
        config_layout.addWidget(load_hw_button, 1, 0)
        config_layout.addWidget(self.variables_btn, 0, 1)
        config_layout.addWidget(self.dfu_btn, 1, 1)
        config_layout.addWidget(enable_flashdrive_button, 0, 2)
        config_layout.addWidget(disable_flashdrive_button, 1, 2)
        self.configure_group.setLayout(config_layout)
        self.configure_group.setEnabled(False)

        select_layout = QtWidgets.QGridLayout()
        select_layout.addWidget(self.select_all_checkbox, 0, 0)
        select_layout.addWidget(self.setups_table, 1, 0, 1, 6)
        self.setup_groupbox.setLayout(select_layout)

        # Log textbox.
        self.log_textbox = QtWidgets.QTextEdit()
        self.log_textbox.setMinimumHeight(180)
        self.log_textbox.setFont(QtGui.QFont("Courier New", get_setting("GUI", "log_font_size")))
        self.log_textbox.setReadOnly(True)
        self.log_textbox.setPlaceholderText("pyControl output")

        # Clear log
        self.clear_output_btn = QtWidgets.QPushButton("Clear output")
        self.clear_output_btn.clicked.connect(self.log_textbox.clear)

        # # Main layout.
        self.setups_layout = QtWidgets.QGridLayout()
        self.setups_layout.addWidget(self.setup_groupbox, 0, 0)
        self.setups_layout.addWidget(self.configure_group, 1, 0)
        self.setups_layout.addWidget(self.log_textbox, 2, 0)
        self.setups_layout.addWidget(self.clear_output_btn, 3, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setups_layout.setRowStretch(0, 1)
        self.setups_layout.setRowStretch(2, 1)
        self.setLayout(self.setups_layout)

        # Load saved setup names.
        self.save_path = os.path.join(user_folder("config"), "setups.json")
        if not os.path.exists(self.save_path):
            self.saved_configs = []
            default_setup = Setup_config(name="Default Setup", pyc_port="", ac_port="")
            self.setups[default_setup.pyc_port] = Setup_table_item(default_setup, self)
        else:
            with open(self.save_path, "r") as file:
                cams_list = json.load(file)
            self.saved_configs = [Setup_config(**cam_dict) for cam_dict in cams_list]
            # for each saved_config initialize a setup object
            for config in self.saved_configs:
                self.setups[config.pyc_port] = Setup_table_item(config, self)
        self.update_available_setups()

    def print_to_log(self, print_string, end="\n"):
        self.log_textbox.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.log_textbox.insertPlainText(print_string + end)
        self.log_textbox.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.GUI_main.app.processEvents()

    def select_all_setups(self):
        if self.select_all_checkbox.isChecked():
            for setup in self.setups.values():
                if setup.select_checkbox.isEnabled():
                    setup.signal_from_rowcheck = False
                    setup.select_checkbox.setChecked(True)
                    setup.signal_from_rowcheck = True
        else:
            for setup in self.setups.values():
                if setup.select_checkbox.isEnabled():
                    setup.signal_from_rowcheck = False
                    setup.select_checkbox.setChecked(False)
                    setup.signal_from_rowcheck = True
        self.multi_config_enable()

    def multi_config_enable(self):
        """Configure which GUI buttons are active as a function of the setups selected."""
        self.select_all_checkbox.blockSignals(True)
        num_checked = 0
        for setup in self.setups.values():
            if setup.select_checkbox.isChecked():
                num_checked += 1
        if num_checked == 1:
            self.dfu_btn.setEnabled(True)
        else:
            self.dfu_btn.setEnabled(False)
        if len(self.get_selected_boards(has_name_filter=True)):
            self.variables_btn.setEnabled(True)
        else:
            self.variables_btn.setEnabled(False)
        if num_checked > 0:
            self.configure_group.setEnabled(True)
            if num_checked < len(self.setups.values()):  # some selected
                self.select_all_checkbox.setChecked(False)
            else:  # all selected
                self.select_all_checkbox.setChecked(True)
        else:  # none selected
            self.select_all_checkbox.setChecked(False)
            self.configure_group.setEnabled(False)
        self.select_all_checkbox.blockSignals(False)

    def update_available_setups(self):
        """Called when boards are plugged, unplugged or renamed."""
        setup_names = sorted([setup.config.name for setup in self.setups.values()])
        if setup_names != self.setup_names:
            self.available_setups_changed = True
            self.setup_names = setup_names
            self.multi_config_enable()
        else:
            self.available_setups_changed = False
        print("setup_names", setup_names)

    def get_saved_setup(self, name=None):
        """Get a saved CameraSettingsConfig object from a name or unique_id from self.saved_setups."""
        if name:
            try:
                return next(config for config in self.saved_configs if config.name == name)
            except StopIteration:
                pass
        return None

    def update_saved_setups(self, setup):
        """Updates the saved setups"""
        saved_setup = self.get_saved_setup(name=setup.config.name)
        # if saved_setup == setup.settings:
        #     return
        if saved_setup:
            self.saved_configs.remove(saved_setup)
        # if the setup has a name
        # if setup.settings.label:
        # add the setup config to the saved setups list
        self.saved_configs.append(setup.config)
        # Save any setups in the list of setups
        if self.saved_configs:
            with open(self.save_path, "w") as f:
                json.dump([asdict(setup) for setup in self.saved_configs], f, indent=4)

    def get_port(self, setup_name, pyc_board = True):
        """Return a setups serial port given the setups name."""
        if pyc_board:
            return next(setup.config.pyc_port for setup in self.setups.values() if setup.config.name == setup_name)
        else:
            return next(setup.config.ac_port for setup in self.setups.values() if setup.config.name == setup_name)
            
    def get_selected_boards(self, has_name_filter=False):
        """Return sorted list of setups whose select checkboxes are ticked."""
        return sorted(
            [setup for setup in self.setups.values() if setup.select_checkbox.isChecked()],
        )

    def get_selected_ac_boards(self, has_name_filter=False):
        """Return sorted list of setups whose select checkboxes are ticked."""
        return sorted(
            [setup.acboard for setup in self.setups.values() if setup.select_checkbox.isChecked()],
        )

    def disconnect(self):
        """Disconect from all pyboards, called on tab change."""
        if self.setups.values():
            parallel_call("disconnect", self.setups.values())

    def edit_hardware_vars(self):
        hardware_var_editor = Hardware_variables_editor(self)
        if not hardware_var_editor.get_hw_vars_from_task_files():
            warning_msg = (
                "There were no hardware variables found in your task files. "
                "To use a hardware variable, add a variable beginning with "
                "'hw_' to a task file for example 'v.hw_solenoid_dur = None'."
            )
            QtWidgets.QMessageBox.warning(
                self,
                "No hardware variables found",
                warning_msg,
                QtWidgets.QMessageBox.StandardButton.Ok,
            )
            return
        hardware_var_editor.exec()

    def load_frameworks(self):
        for setup_item in self.get_selected_boards():
            self.print_to_log("Loading pyControl framework...\n")
            setup_item.load_pyc_framework()
            self.print_to_log("Loading Access control framework...\n")
            setup_item.load_ac_framework()

    def enable_flashdrive(self):
        self.print_to_log("Enabling flashdrive...\n")
        parallel_call("enable_flashdrive", self.get_selected_boards())

    def disable_flashdrive(self):
        self.print_to_log("Disabling flashdrive...\n")
        parallel_call("disable_flashdrive", self.get_selected_boards())

    def DFU_mode(self):
        self.print_to_log("Enabling DFU mode...\n")
        parallel_call("DFU_mode", self.get_selected_boards())

    def load_hardware_definition(self):
        self.hwd_path = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select hardware definition:", user_folder("hardware_definitions"), filter="*.py"
        )[0]
        if self.hwd_path:
            self.print_to_log("Loading hardware definition...\n")
            parallel_call("load_hardware_definition", self.get_selected_boards())

    def add_row(self):
        """Function that adds another setup"""
        name = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        config = Setup_config(name=name, pyc_port="", ac_port="")
        self.setups[name] = Setup_table_item(config, self)
        self.update_available_setups()

    def remove_row(self):
        """Function that adds another setup"""
        # name = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        # self.setups[name] = Setup(name, self)
        # self.update_available_setups()
        print("not implemented")
        pass

    def get_unused_comports(self):
        if self.GUI_main.available_ports:
            unused_ports = list(self.GUI_main.available_ports.copy())
            # for setup in self.saved_configs:
            #     for port in self.GUI_main.available_ports:
            #         if port == setup.pyc_port or port == setup.ac_port:
            #             unused_ports.remove(port)
            return unused_ports
        else:
            return []


# setup class --------------------------------------------------------------------


class Setup_table_item:
    """Class representing one setup in the setups table."""

    def __init__(self, config, setup_tab):
        """Setup is intilised when board is plugged into computer."""

        self.config = config
        self.setup_tab = setup_tab

        self.pyc_board = None
        self.ac_board = None
        self.delay_printing = False

        # Select Check box
        self.select_checkbox = TableCheckbox()
        self.select_checkbox.checkbox.stateChanged.connect(self.checkbox_handler)

        # Name
        self.name_edit = QtWidgets.QLineEdit(self.config.name)
        self.name_edit.setPlaceholderText("name required if you want to edit setup variables")
        self.name_edit.textChanged.connect(self.name_changed)
        # Add remove button
        self.add_remove_button = QtWidgets.QPushButton("Add/Remove")
        self.add_remove_button.clicked.connect(self.setup_tab.add_row)
        self.add_remove_button.setEnabled(True)

        # pycboard
        self.pyc_board_item = QtWidgets.QComboBox()
        self.pyc_board_item.addItems(self.setup_tab.get_unused_comports())
        self.pyc_board_item.currentIndexChanged.connect(self.pyc_board_changed)
        self.pyc_board_item.setCurrentText(self.config.pyc_port)
        # AC board
        self.ac_board_item = QtWidgets.QComboBox()
        self.ac_board_item.currentIndexChanged.connect(self.ac_board_changed)
        self.ac_board_item.addItems(self.setup_tab.get_unused_comports())
        self.ac_board_item.setCurrentText(self.config.ac_port)

        self.setup_tab.setups_table.insertRow(0)
        self.setup_tab.setups_table.setCellWidget(0, 0, self.select_checkbox)
        self.setup_tab.setups_table.setCellWidget(0, 1, self.name_edit)
        self.setup_tab.setups_table.setCellWidget(0, 2, self.pyc_board_item)
        self.setup_tab.setups_table.setCellWidget(0, 3, self.ac_board_item)
        self.setup_tab.setups_table.setCellWidget(0, 4, self.add_remove_button)
        self.signal_from_rowcheck = True

    # Name edit

    def name_changed(self):
        """If name entry in table is blank setup name is set to serial port."""
        name = str(self.name_edit.text())
        self.config.name = name
        self.setup_tab.update_available_setups()
        self.setup_tab.update_saved_setups(self)

    # Add new setup button function

    def check_valid_setup(self):
        """If anything in this table is change, this check should be run"""
        return True

    # Available pybaord functions
    def pyc_board_changed(self):
        # if the pyboard is changed
        self.config.pyc_port = self.pyc_board_item.currentText()
        self.setup_tab.update_saved_setups(self)
        # Option to add the setup if you want and if its valid
        self.add_remove_button.setEnabled(self.check_valid_setup())

    def ac_board_changed(self):
        # if the pyboard is changed
        self.config.ac_port = self.ac_board_item.currentText()
        self.setup_tab.update_saved_setups(self)
        # Option to add the setup if you want and if its valid
        self.add_remove_button.setEnabled(self.check_valid_setup())

    # Pyboard firmware functions ---------------------------------------------

    def checkbox_handler(self):
        if self.signal_from_rowcheck:
            self.setup_tab.multi_config_enable()

    def print(self, print_string, end="\n"):
        """Print a string to the log prepended with the setup name."""
        if self.delay_printing:
            self.print_queue.append((print_string, end))
            return
        self.setup_tab.print_to_log(f"\n{self.config.name}: " + print_string)

    def start_delayed_print(self):
        """Store print output to display later to avoid error
        message when calling print from different thread."""
        self.print_queue = []
        self.delay_printing = True

    def end_delayed_print(self):
        """Print output stored in print queue to log with setup
        name and horisontal line above."""
        self.delay_printing = False
        if self.print_queue:
            self.setup_tab.print_to_log(f"{self.config.name} " + "-" * 70)
            for p in self.print_queue:
                self.setup_tab.print_to_log(*p)
            self.setup_tab.print_to_log("")  # Add blank line.

    def pyc_connect(self):
        """Instantiate pyboard object, opening serial connection to board."""
        self.print("\nConnecting to pyControl board.")
        try:
            self.pyc_board = Pycboard(self.config.pyc_port, print_func=self.print)
        except PyboardError:
            self.print("\nUnable to connect.")

    def pyc_disconnect(self):
        if self.pyc_board:
            self.pyc_board.close()
            self.pyc_board = None

    def ac_connect(self):
        self.print("\nConnecting to Access Control board.")
        try:
            self.ac_board = Access_control(self.config.ac_port, print_func=self.print)
        except PyboardError:
            self.print("\nUnable to connect.")

    def ac_disconnect(self):
        if self.ac_board:
            self.ac_board.close()
            self.ac_board = None

    def unplugged(self):
        """Called when a board is physically unplugged from computer.
        Closes serial connection and removes row from setups table."""
        if self.pyc_board:
            self.pyc_board.close()
        self.setup_tab.setups_table.removeRow(self.pyc_board_item.row())
        del self.setup_tab.setups[self.pyc_port]

    def load_pyc_framework(self):
        if not self.pyc_board:
            self.pyc_connect()
        if self.pyc_board:
            self.pyc_board.load_framework()

    def load_ac_framework(self):
        if not self.ac_board:
            self.ac_connect()
        if self.ac_board:
            self.ac_board.load_framework()

    def load_hardware_definition(self):
        if not self.pyc_board:
            self.pyc_connect()
        if self.pyc_board:
            self.pyc_board.load_hardware_definition(self.setup_tab.hwd_path)

    def DFU_mode(self):
        """Enter DFU mode"""
        self.select_checkbox.setChecked(False)
        if not self.pyc_board:
            self.pyc_connect()
        if self.pyc_board:
            self.pyc_board.DFU_mode()
            self.pyc_board.close()

    def enable_flashdrive(self):
        self.select_checkbox.setChecked(False)
        if not self.pyc_board:
            self.pyc_connect()
        if self.pyc_board:
            self.pyc_board.enable_mass_storage()
            self.pyc_board.close()
            self.pyc_board = None

    def disable_flashdrive(self):
        self.select_checkbox.setChecked(False)
        if not self.pyc_board:
            self.pyc_connect()
        if self.pyc_board:
            self.pyc_board.disable_mass_storage()
            self.pyc_board.close()
            self.pyc_board = None
