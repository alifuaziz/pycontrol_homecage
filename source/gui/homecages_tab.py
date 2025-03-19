import os
import json
from dataclasses import dataclass, asdict
from source.gui.settings import user_folder
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QWidget,
    QGroupBox,
    QVBoxLayout,
    QTableWidget,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QPushButton,
    QSizePolicy,
    QHeaderView,
    QMessageBox,
)

from .utility import TableCheckbox
from .animals_tab import AnimalSettingsConfig, AnimalOverviewTable
from .setups_tab import Setup_config


@dataclass
class HomecageConifg:
    """Represents the CamerasTab settings for one camera"""

    name: str
    setup: str
    animals: list[AnimalSettingsConfig]


default_homecage_dict = {"name": "", "setup": None, "animals": None}


class Homecage_tab(QWidget):
    """Tab for naming homecages and assigning animals to homecages."""

    def __init__(self, parent=None):
        super(Homecage_tab, self).__init__(parent)
        self.GUI = parent
        self.save_path = os.path.join(user_folder("config"), "homecages.json")
        self.homecages = {}  # Dict of setups: {name: Homecage_table_item}
        self.preview_showing = False

        # Initialize_camera_groupbox
        self.camera_table_groupbox = QGroupBox("Homecage Table")
        self.homecage_table = HomecageOverviewTable(parent=self)
        self.homecage_table.setMinimumSize(1, 1)
        self.homecage_table.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.camera_table_layout = QVBoxLayout()
        self.camera_table_layout.addWidget(self.homecage_table)
        self.camera_table_groupbox.setLayout(self.camera_table_layout)

        self.page_layout = QVBoxLayout()
        self.page_layout.addWidget(self.camera_table_groupbox)
        self.setLayout(self.page_layout)

        # Load saved setup info.
        if not os.path.exists(self.save_path):
            self.saved_homecages = []
            default_animal = HomecageConifg(**default_homecage_dict)
            self.saved_homecages.append(default_animal)
        else:
            with open(self.save_path, "r") as file:
                homecage_list = json.load(file)
            self.saved_homecages = [HomecageConifg(**default_homecage_dict) for default_homecage_dict in homecage_list]

        for homecage in self.saved_homecages:
            self.homecages[homecage.name] = Homecage_table_item(
                self.homecage_table, name=homecage.name, animals=homecage.animals, setup=homecage.setup
            )

        self.refresh()
        self.setups_changed = False

    # Refresh timer / tab changing logic -------------------------------------------------------------------------------

    def tab_selected(self):
        """Called when tab selected."""
        self.currently_open_homecage = None
        
        self.refresh()

    def tab_deselected(self):
        if self.animal_table_open:
            self.anmial_overview_table.deleteLater() # deinit the tab
        if self.currently_open_homecage: 
            self.currently_open_homecage = None
    # Reading / Writing the Camera setups saved function --------------------------------------------------------

    def get_saved_homcage(self, name: str = None) -> HomecageConifg:
        """Get a saved CameraSettingsConfig object from a name or unique_id from self.saved_setups."""

        if name:
            try:
                return next(setup for setup in self.saved_homecages if setup.name == name)
            except StopIteration:
                pass
        return None

    def update_saved_setups(self, setup):
        """Updates the saved setups"""
        saved_setup = self.get_saved_homcage(name=setup.settings.name)
        # if saved_setup == setup.settings:
        #     return
        if saved_setup:
            self.saved_homecages.remove(saved_setup)
        # if the setup has a name
        # if setup.settings.label:
        # add the setup config to the saved setups list
        self.saved_homecages.append(setup.settings)
        # Save any setups in the list of setups
        if self.saved_homecages:
            with open(self.save_path, "w") as f:
                json.dump([asdict(setup) for setup in self.saved_homecages], f, indent=4)

    def refresh(self):
        """Check for new animals"""
        # Set the 'currently selected' homecage to be None
        pass

    def get_camera_labels(self) -> list[str]:
        """Get the labels of the available cameras. The label is the camera's user set name if available, else unique ID."""
        return [setup.get_label() for setup in self.homecages.values()]

    def get_camera_unique_id_from_label(self, camera_label: str) -> str:
        """Get the unique_id of the camera from the label"""
        for setup in self.homecages.values():
            if setup.settings.name == camera_label:
                return setup.settings.unique_id
            elif setup.settings.unique_id == camera_label:
                return setup.settings.unique_id
        return None

    def get_animal_settings_from_label(self, label: str) -> AnimalSettingsConfig:
        """Get the camera settings config datastruct from the setups table."""
        for setup in self.homecages.values():
            if setup.settings.name is None:
                query_label = setup.settings.unique_id
            else:
                query_label = setup.settings.name
            if query_label == label:
                return setup.settings
        return None


class HomecageOverviewTable(QTableWidget):
    """Table for displaying information and setting for connected cameras."""

    def __init__(self, parent, displaying_setup=None):
        super(HomecageOverviewTable, self).__init__(parent)
        self.setups_tab = parent
        self.displaying_setup = displaying_setup  # is diplaying_setup is present this table only display the status of the animals in the displayed setup.
        self.header_names = ["Name", "Setup", "Animals", "Assign New Animals"]  # read only bool
        self.setColumnCount(len(self.header_names))
        self.setRowCount(0)
        self.verticalHeader().setVisible(False)

        self.setHorizontalHeaderLabels(self.header_names)
        for i in range(len(self.header_names)):
            resize_mode = QHeaderView.ResizeMode.Stretch if i < 1 else QHeaderView.ResizeMode.ResizeToContents
            self.horizontalHeader().setSectionResizeMode(i, resize_mode)

        self.add_homecage_row()

    def add_homecage_row(self):
        """Button to preview the camera in the row"""
        self.homecages["name-for-homecage"] = Homecage_table_item(self, name="", setup="", animals=[])

    def remove(self, name):
        for row in range(self.rowCount()):
            if self.cellWidget(row, 1).text() == name:
                self.removeRow(row)
                break

    def refresh(self):
        """When called, the items in the HomcageOverviewTable are refreshed so updates can be seen"""
        for homecage in self.homcage_list:
            # update the GUI elements
            print("update homecage table not implemented")


class Homecage_table_item:
    """Class representing single camera in the Camera Tab table."""

    def __init__(self, homecage_setup_table, name, setup, animals):
        self.homecage = HomecageConifg(name=name, setup=setup, animals=animals)

        self.homecage_setups_table = homecage_setup_table
        self.homecage_tab = homecage_setup_table.setups_tab

        # Name edit
        self.name_edit = QLineEdit()
        if self.homecage.name:
            self.name_edit.setText(self.homecage.name)
        else:
            self.name_edit.setPlaceholderText("Set a name")
        self.name_edit.editingFinished.connect(self.homecage_name_changed)

        self.setup_edit = QComboBox()
        self.setup_edit.addItems([])
        self.setup_edit.currentIndexChanged.connect(self.setup_changed)
        self.animals = QLineEdit()
        if self.homecage.animals:
            self.animals.setText(", ".join(animal.name for animal in self.homecage.animals))
        else:
            self.name_edit.setPlaceholderText("No Animals Assigned")
        # Open Record button
        self.assign_animals = QPushButton("Assign Animals")
        self.assign_animals.clicked.connect(self.open_assign_animal_table)

        # Populate the table
        self.homecage_setups_table.insertRow(0)
        self.homecage_setups_table.setCellWidget(0, 0, self.name_edit)
        self.homecage_setups_table.setCellWidget(0, 1, self.setup_edit)
        self.homecage_setups_table.setCellWidget(0, 2, self.animals)
        self.homecage_setups_table.setCellWidget(0, 3, self.assign_animals)

    def homecage_name_changed(self):
        """Called when name text of setup is edited."""
        name = str(self.name_edit.text())
        if name and name not in [setup.settings.name for setup in self.homecage_tab.setups.values()]:
            self.homecage.name = name
        else:
            self.homecage.name = None
            self.name_edit.setText("")
            self.name_edit.setPlaceholderText("Set a name")
        self.homecage_tab.update_saved_setups(setup=self)
        self.homecage_tab.setups_changed = True

    def setup_changed(self):
        pass

    def open_assign_animal_table(self):
        """Opens a table that can be used to assign animals to the homecage selected"""
        self.homecage_tab.animal_overview_table = AnimalOverviewTable(parent=self, mode = 'assign')
        self.homecage_tab.page_layout.addWidget(self.animal_overview_table)
        self.homecage_tab.currently_open_homecage = self.homecage
        # Assign the close animal table to the button now
        self.assign_animals.clicked.connect(self.close_assign_animal_table)
        self.assign_animals.setText("Close animal tab")

    def close_assign_animal_table(self):
        if self.homecage_tab.animal_overview_table:
            self.homecage_tab.animal_overview_table.deleteLater()
            self.homecage_tab.animal_overview_table = None
            self.currently_open_homecage = None

    def get_label(self):
        """Return name if defined else unique ID."""
        return self.homecage.name
