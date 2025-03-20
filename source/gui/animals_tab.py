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


@dataclass
class AnimalSettingsConfig:
    """Represents the CamerasTab settings for one camera"""

    name: str
    RFID: str
    sex: int
    weight: float
    task: float
    training: bool


default_animal_settings = {
    "name": "",
    "RFID": "1234",
    "sex": 30,
    "weight": 100,
    "task": 0,
    "training": False,
}


class Animals_tab(QWidget):
    """Tab for naming cameras and editing camera-level settings."""

    def __init__(self, parent=None):
        super(Animals_tab, self).__init__(parent)
        self.GUI = parent
        self.save_path = os.path.join(user_folder("config"), "animals.json")
        self.animals_dict = {}  # Dict of setups: {RFID: Animal_table_item}
        self.animal_names = []  # List of the names of animals
        # Initialize_camera_groupbox
        self.animal_table_groupbox = QGroupBox("Animal table")
        self.animal_table = AnimalOverviewTable(parent=self)
        self.animal_table.setMinimumSize(1, 1)
        self.animal_table.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.animal_table_layout = QVBoxLayout()
        self.animal_table_layout.addWidget(self.animal_table)
        self.animal_table_groupbox.setLayout(self.animal_table_layout)

        self.page_layout = QVBoxLayout()
        self.page_layout.addWidget(self.animal_table_groupbox)
        self.setLayout(self.page_layout)

        # Load saved setup info.
        if not os.path.exists(self.save_path):
            self.saved_animals = []
            default_animal = AnimalSettingsConfig(**default_animal_settings)
            self.saved_animals.append(default_animal)
        else:
            with open(self.save_path, "r") as file:
                animal_list = json.load(file)
            self.saved_animals = [AnimalSettingsConfig(**animal_dict) for animal_dict in animal_list]

        for animal in self.saved_animals:
            self.animals_dict[animal.RFID] = Animal_table_item(
                self.animal_table,
                name=animal.name,
                RFID=animal.RFID,
                sex=animal.sex,
                weight=animal.weight,
                task=animal.task,
                training=animal.training,
            )

        self.refresh()
        self.update_available_animals()
        self.setups_changed = False

    # Refresh timer / tab changing logic -------------------------------------------------------------------------------

    def tab_selected(self):
        """Called when tab selected."""
        self.refresh()

    # Reading / Writing the Camera setups saved function --------------------------------------------------------

    def get_saved_setup(self, RFID: str = None) -> AnimalSettingsConfig:
        """Get a saved CameraSettingsConfig object from a name or unique_id from self.saved_setups."""

        if RFID:
            try:
                return next(settings for settings in self.saved_animals if settings.RFID == RFID)
            except StopIteration:
                pass
        return None

    def update_saved_setups(self, animal):
        """Updates the saved setups. This should include a check if"""

        saved_setup = self.get_saved_setup(RFID=animal.settings.RFID)
        # if saved_setup == setup.settings:
        #     return
        if saved_setup:
            self.saved_animals.remove(saved_setup)
        # if the setup has a name
        # if setup.settings.label:
        # add the setup config to the saved setups list
        self.saved_animals.append(animal.settings)
        # Save any setups in the list of setups
        if self.saved_animals:
            with open(self.save_path, "w") as f:
                json.dump([asdict(setup) for setup in self.saved_animals], f, indent=4)

    def update_available_animals(self):
        """Should be called when animals are added or renamed"""
        animal_names = [animal.settings.name for animal in self.animals_dict.values()]
        if animal_names != self.animal_names:
            self.available_animals_changed = True
            self.animal_names = animal_names
        else:
            self.available_animals_changed = False
        print("animal_names", self.animal_names)

    def refresh(self):
        """Check for new and removed cameras and updates the setups table."""
        pass

    def get_camera_labels(self) -> list[str]:
        """Get the labels of the available cameras. The label is the camera's user set name if available, else unique ID."""
        return [setup.get_label() for setup in self.animals_dict.values()]

    def get_camera_unique_id_from_label(self, camera_label: str) -> str:
        """Get the unique_id of the camera from the label"""
        for setup in self.animals_dict.values():
            if setup.settings.name == camera_label:
                return setup.settings.unique_id
            elif setup.settings.unique_id == camera_label:
                return setup.settings.unique_id
        return None

    def get_animal_settings_from_label(self, label: str) -> AnimalSettingsConfig:
        """Get the camera settings config datastruct from the setups table."""
        for setup in self.animals_dict.values():
            if setup.settings.name is None:
                query_label = setup.settings.unique_id
            else:
                query_label = setup.settings.name
            if query_label == label:
                return setup.settings
        return None

    def get_available_tasks(self):
        """get the list of tasks in the task folder"""
        tasks_folder = user_folder("tasks")
        return [f for f in os.listdir(tasks_folder) if f.endswith(".py")]


class AnimalOverviewTable(QTableWidget):
    """Table for displaying information and setting for connected cameras.
    Table modes
    'edit' : where animal details can be modified
    'assign' : where animals are assigned to homecage
    'view' : where animal status is viewed
    """

    def __init__(self, parent, mode="edit"):
        super(AnimalOverviewTable, self).__init__(parent)
        self.setups_tab = parent
        assert mode in ["edit", "assign", "view"], "Invalid mode"
        self.mode = mode
        headers = {
            "edit": [
                "Name",
                "RFID",
                "Sex",
                "Weight (g)",
                "Task",
                "Training",
                "Open Record",
                "New Animal",
            ],
            "assign": [
                "Name",
                "RFID",
                "Sex",
                "Weight (g)",
                "Task",
                "Training",
                "Assign to open homecage",
            ],
            "view": [
                "Name",
                "RFID",
                "Sex",
                "Weight (g)",
                "Task",
                "Training",
            ],
        }
        self.header_names = headers[self.mode]
        self.setColumnCount(len(self.header_names))
        self.setRowCount(0)
        self.insertRow(self.rowCount())
        add_button = QPushButton("Add New Animal")
        add_button.clicked.connect(self.add)
        self.setCellWidget(self.rowCount() - 1, len(self.header_names) - 1, add_button)
        self.verticalHeader().setVisible(False)

        self.setHorizontalHeaderLabels(self.header_names)
        for i in range(len(self.header_names)):
            resize_mode = QHeaderView.ResizeMode.Stretch if i < 2 else QHeaderView.ResizeMode.ResizeToContents
            self.horizontalHeader().setSectionResizeMode(i, resize_mode)

    def remove(self, rfid):
        for row in range(self.rowCount()):
            if self.cellWidget(row, 1).text() == rfid:
                self.removeRow(row)
                break

    def add(self):
        row_position = self.rowCount()
        self.insertRow(row_position)
        # Needs an idenfitier for itself.
        Animal_table_item(
            self,
            name="",
            RFID="",
            sex=0,
            weight=0,
            task="",
            training=False,
        )


class Animal_table_item:
    """Class representing single camera in the Camera Tab table."""

    def __init__(self, setups_table, name, RFID, sex, weight, task, training, config_valid=True):
        self.settings = AnimalSettingsConfig(name=name, RFID=RFID, sex=sex, weight=weight, task=task, training=training)

        self.setups_table = setups_table
        self.animals_tab = setups_table.setups_tab
        self.config_valid = config_valid

        # Name edit
        self.name_edit = QLineEdit()
        if self.settings.name:
            self.name_edit.setText(self.settings.name)
        else:
            self.name_edit.setPlaceholderText("Set a name")
        self.name_edit.editingFinished.connect(self.animal_name_changed)
        # RFID edit
        self.rfid_edit = QLineEdit()
        self.rfid_edit.setReadOnly(True)
        if self.settings.RFID:
            self.rfid_edit.setText(self.settings.RFID)
        # Weight edit
        self.weight_edit = QSpinBox()
        self.weight_edit.setRange(0, 100)
        if self.settings.weight:
            self.weight_edit.setValue(int(self.settings.weight))
        self.weight_edit.valueChanged.connect(self.animal_weight_changed)
        # Exposure time edit
        self.sex_edit = QComboBox()
        self.sex_edit.addItems(["Male", "Female"])
        if self.settings.weight:
            self.sex_edit.setCurrentText(str(self.settings.sex))
        self.sex_edit.currentIndexChanged.connect(self.animal_sex_changed)
        # Animal task
        self.animal_task = QComboBox()
        self.animal_task.addItems(
            [f for f in os.listdir(user_folder("tasks")) if f.endswith(".py")]
        )  # list of task in the task folder
        self.animal_task.activated.connect(self.animal_task_changed)
        # Table Checkbox to show if animal is running
        self.animal_training_checkbox = TableCheckbox()
        self.animal_training_checkbox.setChecked(bool(self.settings.training))
        self.animal_training_checkbox.setEnabled(False)
        # Open Record button
        self.open_record_button = QPushButton("Open Record")
        self.open_record_button.clicked.connect(self.open_record_file)
        # Preview button.
        self.add_remove_row = QPushButton("Remove Animal")
        self.add_remove_row.clicked.connect(self.remove_animal_row)
        # Assign button
        self.assign_homecage_row = QPushButton("Assign Homecage")
        self.assign_homecage_row.clicked.connect(self.assign_homecage)

        # Populate the table. This should be populated based on the table mode
        self.setups_table.insertRow(0)
        self.setups_table.setCellWidget(0, 0, self.name_edit)
        self.setups_table.setCellWidget(0, 1, self.rfid_edit)
        self.setups_table.setCellWidget(0, 2, self.sex_edit)
        self.setups_table.setCellWidget(0, 3, self.weight_edit)
        self.setups_table.setCellWidget(0, 4, self.animal_training_checkbox)
        self.setups_table.setCellWidget(0, 5, self.animal_task)
        if self.setups_table.mode == "edit":
            self.setups_table.setCellWidget(0, 6, self.open_record_button)
            self.setups_table.setCellWidget(0, 7, self.add_remove_row)
        elif self.setups_table.mode == "assign":
            self.setups_table.setCellWidget(0, 6, self.assign_homecage_row)

    def animal_name_changed(self):
        """Called when name text of setup is edited."""
        name = str(self.name_edit.text())
        if name and name not in [
            settings.name for settings in self.animals_tab.saved_animals if settings.RFID != self.settings.RFID
        ]:
            self.settings.name = name
        else:
            self.settings.name = None
            self.name_edit.setText("")
            self.name_edit.setPlaceholderText("Set a name")
        self.animals_tab.update_saved_setups(animal=self)
        self.animals_tab.setups_changed = True
        self.animals_tab.update_available_animals()

    def get_label(self):
        """Return name if defined else unique ID."""
        return self.settings.name if self.settings.name else self.settings.RFID

    def animal_weight_changed(self):
        """Called when fps text of setup is edited."""
        self.settings.weight = float(self.weight_edit.text())
        self.animals_tab.update_saved_setups(animal=self)
        self.check_valid_animal_config()

    def animal_sex_changed(self):
        """"""
        self.settings.sex = self.sex_edit.currentText()
        self.animals_tab.update_saved_setups(animal=self)
        self.check_valid_animal_config()

    def animal_task_changed(self):
        """Change the pixel format"""
        self.settings.task = self.animal_task.currentText()
        self.animals_tab.update_saved_setups(animal=self)
        self.check_valid_animal_config()

    def animal_training_changed(self):
        """Called when the downsampling factor of the seutp is edited"""
        self.settings.training = self.animal_training_checkbox.isChecked()
        self.animals_tab.update_saved_setups(animal=self)
        self.check_valid_animal_config()

    def assign_homecage(self):
        """Called to assign to the currently open homecage"""
        self.homecage_tab.currently_open_homecage.animals.append(
            self.settings
        )  # Append animal to list of homecage animals
        self.homecage_table.refresh()  # refresh the homecage table to reflect changes
        # Reorder the animals tab based on which homecage is open
        print("Animal table reordering not implemented yet")

    def open_record_file(self):
        """Open a .txt file when the button is clicked."""
        file_path = os.path.join(user_folder("records"), f"{self.settings.RFID}.txt")
        if os.path.exists(file_path):
            os.startfile(file_path)
        else:
            print(f"Record file for {self.settings.RFID} does not exist.")

    def remove_animal_row(self):
        """"""
        reply = QMessageBox.question(
            self.setups_table,
            "Remove Animal",
            f"Are you sure you want to remove the animal with RFID {self.settings.RFID}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.setups_table.removeRow(self.setups_table.indexAt(self.rfid_edit.pos()).row())
            self.animals_tab.saved_animals.pop(self.settings.RFID)
            self.animals_tab.update_saved_setups(self)
            self.check_valid_animal_config()
            self.animals_tab.refresh()

    def check_valid_animal_config(self):
        """Return true if the animal is valid and can be added"""
        name = self.name_edit.text()  # Check if the name has not been used before
        RFID = self.rfid_edit.text()  # the RFID is an int value
        sex = self.sex_edit.currentText()  # on of m / f
        weight = self.weight_edit.value()  # spinbox should be a value above 10 below 100
        task = self.animal_task.currentText()  # python file exists in the tasks files
        training = self.animal_training_checkbox.isChecked()  # should be false

        if name and RFID.isdigit() and sex in ["Male", "Female"] and 10 <= weight <= 100:
            task_path = os.path.join(user_folder("tasks"), task)
            if os.path.isfile(task_path) and not training:
                # Add animal button is set to be enabled.
                self.assign_homecage_row.setEnabled(True)
                self.animals_tab.update_saved_setups(self)
                self.add_remove_row.setText("Remove Row")
        self.assign_homecage_row.setEnabled(False)
