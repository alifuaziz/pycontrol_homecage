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
    "weight": 10000,
    "task": 0,
    "training": 1,
}


class Animals_tab(QWidget):
    """Tab for naming cameras and editing camera-level settings."""

    def __init__(self, parent=None):
        super(Animals_tab, self).__init__(parent)
        self.GUI = parent
        self.save_path = os.path.join(user_folder("config"), "animals.json")
        self.setups = {}  # Dict of setups: {RFID: Animal_table_item}
        self.preview_showing = False

        # Initialize_camera_groupbox
        self.camera_table_groupbox = QGroupBox("Camera Table")
        self.animal_table = AnimalOverviewTable(parent=self)
        self.animal_table.setMinimumSize(1, 1)
        self.animal_table.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.camera_table_layout = QVBoxLayout()
        self.camera_table_layout.addWidget(self.animal_table)
        self.camera_table_groupbox.setLayout(self.camera_table_layout)

        self.page_layout = QVBoxLayout()
        self.page_layout.addWidget(self.camera_table_groupbox)
        self.setLayout(self.page_layout)

        # Load saved setup info.
        if not os.path.exists(self.save_path):
            self.saved_setups = []
            default_animal = AnimalSettingsConfig(**default_animal_settings)
            self.saved_setups.append(default_animal)
        else:
            with open(self.save_path, "r") as file:
                animal_list = json.load(file)
            self.saved_setups = [AnimalSettingsConfig(**animal_dict) for animal_dict in animal_list]

        for animal in self.saved_setups:
            self.setups[animal.RFID] = Animal_table_item(
                self.animal_table,
                name=animal.name,
                RFID=animal.RFID,
                sex=animal.sex,
                weight=animal.weight,
                task=animal.task,
                training=animal.training,
            )

        self.refresh()
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
                return next(setup for setup in self.saved_setups if setup.RFID == RFID)
            except StopIteration:
                pass
        return None

    def update_saved_setups(self, setup):
        """Updates the saved setups"""
        saved_setup = self.get_saved_setup(RFID=setup.settings.RFID)
        # if saved_setup == setup.settings:
        #     return
        if saved_setup:
            self.saved_setups.remove(saved_setup)
        # if the setup has a name
        # if setup.settings.label:
        # add the setup config to the saved setups list
        self.saved_setups.append(setup.settings)
        # Save any setups in the list of setups
        if self.saved_setups:
            with open(self.save_path, "w") as f:
                json.dump([asdict(setup) for setup in self.saved_setups], f, indent=4)

    def refresh(self):
        """Check for new and removed cameras and updates the setups table."""
        # if not connected_cameras == self.setups.keys():
        #     # Add any new cameras setups to the setups (comparing unique_ids)
        #     for unique_id in set(connected_cameras) - set(self.setups.keys()):
        #         # Check if this unique_id has been seen before by looking in the saved setups database
        #         camera_settings_config: AnimalSettingsConfig = self.get_saved_setup(unique_id=unique_id)
        #         if camera_settings_config:
        #             # Instantiate the setup and add it to the setups dict
        #             self.setups[unique_id] = Animal_table_item(self.camera_table, **asdict(camera_settings_config))
        #         else:  # unique_id has not been seen before, create a new setup
        #             self.setups[unique_id] = Animal_table_item(
        #                 self.camera_table, **default_animal_settings, unique_id=unique_id
        #             )
        #         self.update_saved_setups(self.setups[unique_id])
        #     # Remove any setups that are no longer connected
        #     for unique_id in set(self.setups.keys()) - set(connected_cameras):
        #         # Sequence for removed a setup from the table (and deleting it)
        #         self.setups.pop(unique_id)
        #         self.camera_table.remove(unique_id)
        # self.n_setups = len(self.setups.keys())
        pass

    def get_camera_labels(self) -> list[str]:
        """Get the labels of the available cameras. The label is the camera's user set name if available, else unique ID."""
        return [setup.get_label() for setup in self.setups.values()]

    def get_camera_unique_id_from_label(self, camera_label: str) -> str:
        """Get the unique_id of the camera from the label"""
        for setup in self.setups.values():
            if setup.settings.name == camera_label:
                return setup.settings.unique_id
            elif setup.settings.unique_id == camera_label:
                return setup.settings.unique_id
        return None

    def get_animal_settings_from_label(self, label: str) -> AnimalSettingsConfig:
        """Get the camera settings config datastruct from the setups table."""
        for setup in self.setups.values():
            if setup.settings.name is None:
                query_label = setup.settings.unique_id
            else:
                query_label = setup.settings.name
            if query_label == label:
                return setup.settings
        return None

    def get_available_tasks(self):
        """get the list of tasks in the task folder"""
        pass


class AnimalOverviewTable(QTableWidget):
    """Table for displaying information and setting for connected cameras."""

    def __init__(self, parent, mode="edit"):

        super(AnimalOverviewTable, self).__init__(parent)
        self.setups_tab = parent
        assert mode in ["edit", "assign", "view"], "Invalid mode"
        self.mode = mode
        """Table modes:
        'edit' : where animal details can be modified
        'assign' : where animals are assigned to homecage
        'view' : where animal status is viewed
        """
        if self.mode == "edit":
            self.header_names = [
                "Name",
                "RFID",
                "Sex",
                "Weight (g)",
                "Task",
                "Training",
                "Open Record",
                "New Animal",
            ]  # read only bool
        elif self.mode == "assign":
            self.header_names = [
                "Name",
                "RFID",
                "Sex",
                "Weight (g)",
                "Task",
                "Training",
                "Assign to open homecage",
            ]  # read only bool
        self.setColumnCount(len(self.header_names))
        self.setRowCount(0)
        self.verticalHeader().setVisible(False)

        self.setHorizontalHeaderLabels(self.header_names)
        for i in range(len(self.header_names)):
            resize_mode = QHeaderView.ResizeMode.Stretch if i < 2 else QHeaderView.ResizeMode.ResizeToContents
            self.horizontalHeader().setSectionResizeMode(i, resize_mode)

        self.add_animal_row()

    def add_animal_row(self):
        """Button to preview the camera in the row"""
        new_animal = Animal_table_item(
            self,
            name="",
            RFID="",
            sex=0,
            weight=0,
            task="",
            training=False,
        )

    def remove(self, rfid):
        for row in range(self.rowCount()):
            if self.cellWidget(row, 1).text() == rfid:
                self.removeRow(row)
                break


class Animal_table_item:
    """Class representing single camera in the Camera Tab table."""

    def __init__(self, setups_table, name, RFID, sex, weight, task, training):
        self.settings = AnimalSettingsConfig(name=name, RFID=RFID, sex=sex, weight=weight, task=task, training=training)

        self.setups_table = setups_table
        self.setups_tab = setups_table.setups_tab
        self.setups_tab.preview_showing = False

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
        # Set the min and max values of the spinbox
        self.weight_edit.setRange(0, 100)
        if self.settings.weight:
            self.weight_edit.setValue(int(self.settings.weight))
        self.weight_edit.valueChanged.connect(self.animal_weight_changed)

        # Exposure time edit
        self.sex_edit = QComboBox()
        self.sex_edit.addItems(["Male", "Female"])
        if self.settings.weight:
            self.sex_edit.setCurrentText(str(self.settings.weight))
        self.sex_edit.currentIndexChanged.connect(self.animal_sex_changed)

        # Animal task
        self.animal_task = QComboBox()
        self.animal_task.addItems(
            [f for f in os.listdir(user_folder("tasks")) if f.endswith(".py")]
        )  # list of task in the task folder
        self.animal_task.activated.connect(self.animal_task_changed)

        self.animal_training_checkbox = TableCheckbox()
        self.animal_training_checkbox.setChecked(bool(self.settings.training))
        self.animal_training_checkbox.setEnabled(False)

        # Open Record button
        self.open_record_button = QPushButton("Open Record")
        self.open_record_button.clicked.connect(self.open_record_file)

        # Preview button.
        self.removed_animal_row = QPushButton("Remove Animal")
        self.removed_animal_row.clicked.connect(self.remove_animal_row)

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
            self.setups_table.setCellWidget(0, 7, self.removed_animal_row)
        elif self.setups_table.mode == "assign":
            self.setups_table.setCellWidget(0, 6, self.assign_homecage_row)

    def animal_name_changed(self):
        """Called when name text of setup is edited."""
        name = str(self.name_edit.text())
        if name and name not in [
            setup.settings.name
            for setup in self.setups_tab.setups.values()
            if setup.settings.RFID != self.settings.RFID
        ]:
            self.settings.name = name
        else:
            self.settings.name = None
            self.name_edit.setText("")
            self.name_edit.setPlaceholderText("Set a name")
        self.setups_tab.update_saved_setups(setup=self)
        self.setups_tab.setups_changed = True

    def get_label(self):
        """Return name if defined else unique ID."""
        return self.settings.name if self.settings.name else self.settings.RFID

    def animal_weight_changed(self):
        """Called when fps text of setup is edited."""
        self.settings.sex = int(self.weight_edit.text())
        self.setups_tab.update_saved_setups(setup=self)
        if self.setups_tab.preview_showing:
            self.setups_tab.camera_preview.camera_api.set_frame_rate(self.settings.sex)
        self.sex_edit.setRange(*self.camera_api.get_exposure_time_range(self.settings.sex))

    def animal_sex_changed(self):
        """"""
        self.settings.weight = int(self.sex_edit.text())
        self.setups_tab.update_saved_setups(setup=self)
        if self.setups_tab.preview_showing:
            self.setups_tab.camera_preview.camera_api.set_exposure_time(self.settings.weight)
        self.weight_edit.setRange(*self.camera_api.get_frame_rate_range(self.settings.weight))

    def animal_task_changed(self):
        """Change the pixel format"""
        self.settings.pixel_format = self.animal_task.currentText()
        self.setups_tab.update_saved_setups(setup=self)
        if self.setups_tab.preview_showing:
            self.setups_tab.camera_preview.camera_api.set_pixel_format(self.settings.pixel_format)

    def animal_training_changed(self):
        """Called when the downsampling factor of the seutp is edited"""
        self.settings.downsampling_factor = int(self.animal_training_checkbox.currentText())
        self.setups_tab.update_saved_setups(setup=self)

    def assign_homecage_row(self): 
        """Called to assign to the currently open homecage"""
        self.homecage_tab.currently_open_homecage.animals.append(self.settings) # Append animal to list of homecage animals
        self.homecage_table.refresh() # refresh the homecage table to reflect changes
        # Reorder the animals tab based on which homecage is open
        print('Animal table reordering not implemented yet')        
        
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
            self.setups_tab.setups.pop(self.settings.RFID)
            self.setups_tab.update_saved_setups(self)
            self.setups_tab.refresh()
