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


default_homecage_dict = {"name": "", "setup": None, "animals": []}


class Homecage_tab(QWidget):
    """Tab for naming homecages and assigning animals to homecages."""

    def __init__(self, parent=None):
        super(Homecage_tab, self).__init__(parent)
        self.GUI = parent
        self.homecages = {}  # Dict of setups: {name: Homecage_table_item}
        self.homecage_names = []

        # Initialize_camera_groupbox
        self.camera_table_groupbox = QGroupBox("Homecage Table")
        self.homecage_table = HomecageOverviewTable(homecage_tab=self)
        self.homecage_table.setMinimumSize(1, 1)
        self.homecage_table.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.camera_table_layout = QVBoxLayout()
        self.camera_table_layout.addWidget(self.homecage_table)
        self.camera_table_groupbox.setLayout(self.camera_table_layout)

        self.page_layout = QVBoxLayout()
        self.page_layout.addWidget(self.camera_table_groupbox)
        self.setLayout(self.page_layout)

        # Load saved setup info.
        self.save_path = os.path.join(user_folder("config"), "homecages.json")
        if not os.path.exists(self.save_path):
            self.saved_homecages = [HomecageConifg(**default_homecage_dict)]
        else:
            with open(self.save_path, "r") as file:
                homecage_list = json.load(file)
            self.saved_homecages = [HomecageConifg(**default_homecage_dict) for default_homecage_dict in homecage_list]

        for homecage in self.saved_homecages:
            self.homecages[homecage.name] = Homecage_table_item(
                self.homecage_table, name=homecage.name, animals=homecage.animals, setup=homecage.setup
            )

        self.refresh()
        self.available_homecage_names_changed = False
        self.update_available_homecages()

    # Refresh timer / tab changing logic -------------------------------------------------------------------------------

    def tab_selected(self):
        """Called when tab selected."""
        self.currently_open_homecage = None

        self.refresh()

    def tab_deselected(self):
        if self.animal_table_open:
            self.anmial_overview_table.deleteLater()  # deinit the tab
        if self.currently_open_homecage:
            self.currently_open_homecage = None

    # Reading / Writing the Camera setups saved function --------------------------------------------------------

    def get_saved_homcage(self, name: str = None) -> HomecageConifg:
        """Get a saved CameraSettingsConfig object from a name or unique_id from self.saved_setups."""

        if name:
            try:
                return next(homecage for homecage in self.saved_homecages if homecage.name == name)
            except StopIteration:
                pass
        return None

    def update_saved_setups(self, setup):
        """Updates the saved setups"""
        saved_setup = self.get_saved_homcage(name=setup.homecage.name)
        # if saved_setup == setup.settings:
        #     return
        if saved_setup:
            self.saved_homecages.remove(saved_setup)
        # if the setup has a name
        # if setup.settings.label:
        # add the setup config to the saved setups list
        self.saved_homecages.append(setup.homecage)
        # Save any setups in the list of setups
        if self.saved_homecages:
            with open(self.save_path, "w") as f:
                json.dump([asdict(setup) for setup in self.saved_homecages], f, indent=4)

    def refresh(self):
        """Check for new animals"""
        # Set the 'currently selected' homecage to be None
        pass

    def update_available_homecages(self):
        """Called when homecages become available or are edited"""
        homecage_names = set([homecage.name for homecage in self.saved_homecages])
        if homecage_names != self.homecage_names:
            self.avaialble_homecages_changed = True
            self.homecage_names = homecage_names
        else:
            self.avaialble_homecages_changed = False

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

    def __init__(self, homecage_tab):
        super(HomecageOverviewTable, self).__init__(homecage_tab)
        self.homecage_tab = homecage_tab
        self.header_names = ["Name", "Setup", "Animals", "Assign New Animals"]  # read only bool
        self.setColumnCount(len(self.header_names))
        self.setRowCount(0)
        self.verticalHeader().setVisible(False)
        self.setHorizontalHeaderLabels(self.header_names)
        for i in range(len(self.header_names)):
            resize_mode = QHeaderView.ResizeMode.Stretch if i < 1 else QHeaderView.ResizeMode.ResizeToContents
            self.horizontalHeader().setSectionResizeMode(i, resize_mode)

        # Add new homecage button
        self.add_new_homecage_button = QPushButton("Add New Homecage")
        self.add_new_homecage_button.clicked.connect(self.add_homecage_row)
        self.insertRow(self.rowCount())
        self.setCellWidget(self.rowCount() - 1, 0, self.add_new_homecage_button)
        self.setSpan(self.rowCount() - 1, 0, 1, self.columnCount())

    def add_homecage_row(self):
        """Button to preview the camera in the row"""
        self.homecage_tab.homecages["name-for-homecage"] = Homecage_table_item(self, name="", setup="", animals=[])

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
        self.homecage_tab = homecage_setup_table.homecage_tab

        # Name edit
        self.name_edit = QLineEdit()
        if self.homecage.name:
            self.name_edit.setText(self.homecage.name)
        else:
            self.name_edit.setPlaceholderText("Set a name")
        self.name_edit.editingFinished.connect(self.homecage_name_changed)

        self.setup_edit = QComboBox()
        self.setup_edit.addItems(self.homecage_tab.GUI.setups_tab.get_saved_setups())
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
        if name and name not in [homecage.name for homecage in self.homecage_tab.saved_homecages]:
            self.homecage.name = name
        else:
            self.homecage.name = None
            self.name_edit.setText("")
            self.name_edit.setPlaceholderText("Set a name")
        self.homecage_tab.update_saved_setups(setup=self)
        self.homecage_tab.setups_changed = True
        self.homecage_tab.update_available_homecages()

    def setup_changed(self):
        pass

    def open_assign_animal_table(self):
        """Opens a table that can be used to assign animals to the homecage selected"""
        self.homecage_tab.animal_overview_table = AnimalOverviewTable(
            animals_tab=self.homecage_tab.GUI.animals_tab, mode="assign"
        )
        self.homecage_tab.page_layout.addWidget(self.homecage_tab.animal_overview_table)
        self.homecage_tab.currently_open_homecage = self.homecage
        # Assign the close animal table to the button now
        self.assign_animals.clicked.disconnect(self.open_assign_animal_table)
        self.assign_animals.clicked.connect(self.close_assign_animal_table)
        self.assign_animals.setText("Close animal tab")

    def close_assign_animal_table(self):
        print("running close function")
        self.homecage_tab.animal_overview_table.deleteLater()
        self.homecage_tab.page_layout.removeWidget(self.homecage_tab.animal_overview_table)
        self.homecage_tab.animal_overview_table = None
        self.homecage_tab.currently_open_homecage = None

    def get_label(self):
        """Return name if defined else unique ID."""
        return self.homecage.name
