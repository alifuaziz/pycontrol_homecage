from typing import List
from source.communication.messages import MessageRecipient

from PyQt5.QtWidgets import (
    QWidget,
    QMainWindow,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QScrollArea,
    QVBoxLayout,
    QMessageBox,
)
from PyQt5 import QtCore

from source.dialogs import (
    AreYouSureDialog,
    CageSummaryDialog,
    ConfigureBoxDialog,
    DirectPyboardDialog,
    InformationDialog,
)
from source.tables import SetupTable
from ..utils import find_pyboards
import db as database
from paths import paths


class SetupsOverviewTab(QWidget):
    def __init__(self, parent: QMainWindow = None):
        super(QWidget, self).__init__(parent)

        self.board = None
        self.configure_box_dialog = None

        # initialise each of the tab regions then bind them
        # to the overall layout
        self.CAT = QGroupBox("Add Setup")  # the main container
        self.cat_layout = QHBoxLayout()  # main layout class

        # Name the setup you want to add
        self.setup_name_label = QLabel("Setup Name:")
        self.setup_name = QLineEdit()
        # press button to add setup
        self.add_cage_button = QPushButton("Add setup")
        self.add_cage_button.clicked.connect(self.add_cage)

        self.cat_combo_box = QComboBox()  # select operant chamber pyboard
        self.cact_combo_box = QComboBox()  # select access control pyboard
        self.cat_layout.addWidget(self.setup_name_label)
        self.cat_layout.addWidget(self.setup_name)
        self.cat_layout.addWidget(self.cat_combo_box)
        self.cat_layout.addWidget(self.cact_combo_box)
        self.cat_layout.addWidget(self.add_cage_button)

        self.CAT.setLayout(self.cat_layout)

        # Main Layout Container
        self.cage_manager_layout = QHBoxLayout()
        self.remove_cage_button = QPushButton("Remove setup")
        self.remove_cage_button.clicked.connect(self.remove_selected_setups)
        self.update_cage_button = QPushButton("Update Connected setup")
        self.update_cage_button.clicked.connect(self.update_setup)
        self.check_beh_hardware_button = QPushButton("Access task pyboard")
        self.check_beh_hardware_button.clicked.connect(self.access_selected_task_pyboard)
        self.cage_summary_button = QPushButton("Get setup Summary")
        self.cage_summary_button.clicked.connect(self.get_summary)
        # Add to layout
        self.cage_manager_layout.addWidget(self.remove_cage_button)
        self.cage_manager_layout.addWidget(self.update_cage_button)
        self.cage_manager_layout.addWidget(self.check_beh_hardware_button)
        self.cage_manager_layout.addWidget(self.cage_summary_button)

        # define container for the cageTable
        self.scrollable_cage = QScrollArea()
        self.scrollable_cage.setWidgetResizable(True)
        self.scrollable_cage.horizontalScrollBar().setEnabled(False)
        self.cage_table_label = QLabel()
        self.cage_table_label.setText("List of setups")
        self.setup_table_widget = SetupTable(tab=self)
        self.scrollable_cage.setWidget(self.setup_table_widget)

        # Global Layout
        self.Vlayout = QVBoxLayout(self)
        self.Vlayout.addWidget(self.CAT, 1)
        self.Vlayout.addWidget(self.cage_table_label, 1)
        self.Vlayout.addLayout(self.cage_manager_layout, 1)
        self.Vlayout.addWidget(self.scrollable_cage, 15)

    def access_selected_task_pyboard(self) -> None:
        """Open interface to pyboard in the operant chamber that allows you to run tasks
        behavioural tasks on the pyboard"""

        self._is_any_setup_connected()

        checked_setup_idx = self._is_single_setup_selected()

        if checked_setup_idx:
            checked_setup_idx = checked_setup_idx[0]
            setup_col = self.setup_table_widget.header_names.index("Setup_ID")
            checked_setup_id = self.setup_table_widget.item(checked_setup_idx, setup_col).text()
            for k, G in database.controllers.items():
                if k == checked_setup_id:
                    self.direct_pyboard_dialog = DirectPyboardDialog(k)
                    # database.print_consumers[MessageRecipient.direct_pyboard_dialog] = self.direct_pyboard_dialog.print_msg
                    self.direct_pyboard_dialog.exec_()
                    # del database.print_consumers[MessageRecipient.direct_pyboard_box_dialog]
        else:
            info = InformationDialog(info_text="You must edit one setup at a time. You have selected 0 or >1 setup.")
            info.exec()

    def _is_single_setup_selected(self) -> List[int]:
        """
        Determine how many setups are selected for updates, must be exaclty one row

        Returns: row from the setups widget table
        """

        isChecked = []
        for row in range(self.setup_table_widget.rowCount()):
            # Check if the row is checked
            row_checked = (
                self.setup_table_widget.item(row, self.setup_table_widget.select_column_idx).checkState()
                == QtCore.Qt.Checked
            )
            # Append to list
            if row_checked:
                isChecked.append(row)

        return isChecked if len(isChecked) == 1 else []

    def _is_any_setup_connected(self) -> None:
        """Are any setups connected. Raises a flag if not setups are connected"""
        if len(database.controllers) == 0:
            boxM = QMessageBox()
            boxM.setIcon(QMessageBox.Information)
            boxM.setText("You must be connected to a setup to update it")
            boxM.exec()

    def update_setup(self) -> None:
        isChecked = []

        for row in range(self.setup_table_widget.rowCount()):
            isChecked.append(
                self.setup_table_widget.item(row, self.setup_table_widget.select_column_idx).checkState()
                == QtCore.Qt.Checked
            )

        if len(database.controllers) == 0:
            #
            info = InformationDialog(info_text="You must be connected to a setup to update it")

        if sum(isChecked) == 1:
            # Updating selected setups
            checked_row = isChecked.index(1)
            setup_col = self.setup_table_widget.header_names.index("Setup_ID")
            checked_setup_id = self.setup_table_widget.item(checked_row, setup_col).text()
            for k, G in database.controllers.items():
                if k == checked_setup_id:
                    #
                    self.configure_box_dialog = ConfigureBoxDialog(k)
                    database.print_consumers[MessageRecipient.configure_box_dialog] = (
                        self.configure_box_dialog.print_msg
                    )
                    self.configure_box_dialog.exec_()
                    del database.print_consumers[MessageRecipient.configure_box_dialog]

        else:
            # Wrong number of setups selected
            info = InformationDialog(
                info_text=f"You must edit one setup at a time. {isChecked} number of setups have been selected"
            )
            info.exec()

    def add_cage(self):
        entry_nr = len(database.setup_df)

        # add a check to see that something about the cage has been filled in
        if not (self.cat_combo_box.currentIndex() == 0 or self.setup_name.text() is None):
            # first fill row with NA
            database.setup_df.loc[entry_nr] = ["none"] * len(database.setup_df.columns)

            # get and set the USB port key
            COM = self.cat_combo_box.itemText(self.cat_combo_box.currentIndex())
            database.setup_df.loc[entry_nr, "COM"] = COM

            COM_AC = self.cact_combo_box.itemText(self.cact_combo_box.currentIndex())
            database.setup_df.loc[entry_nr, "COM_AC"] = COM_AC

            # get the name of the setup
            database.setup_df.loc[entry_nr, "Setup_ID"] = self.setup_name.text()

        # self.parent()._refresh_tables()
        database.update_table_queue = ["all"]

        database.setup_df.to_csv(paths["setup_dir_dataframe_filepath"])

    def _refresh(self):
        """Find which training setups are available"""

        if self._setups_have_changed():
            self.cat_combo_box.clear()
            self.cact_combo_box.clear()
            ports = [
                i
                for i in find_pyboards()
                if i not in (database.setup_df["COM"].tolist() + database.setup_df["COM_AC"].tolist())
            ]

            self.cat_combo_box.addItems(["Select Training Setup"] + list(ports))
            self.cact_combo_box.addItems(["Select Access Control"] + list(ports))

        self.setup_table_widget._refresh()

    def _setups_have_changed(self) -> bool:
        """
        Checks if the setups have been changed

        Returns: bool
        """
        ports = [
            i
            for i in find_pyboards()
            if i not in (database.setup_df["COM"].tolist() + database.setup_df["COM_AC"].tolist())
        ]
        prev = ["Select Training Setup"] + list(ports)
        new_prop_cat = [self.cat_combo_box.itemText(i) for i in range(self.cat_combo_box.count())]
        return new_prop_cat != prev

    def remove_selected_setups(self):
        """Remove cage from setups_df and CSV file"""
        isChecked = []
        for row in range(self.setup_table_widget.rowCount()):
            isChecked.append(
                self.setup_table_widget.item(row, self.setup_table_widget.select_column_idx).checkState() == 2
            )

        if any(isChecked):
            sure = AreYouSureDialog()
            sure.exec_()
            if sure.GO:
                fl = paths["setup_dir_dataframe_filepath"]

                database.setup_df = database.setup_df.drop(database.setup_df.index[isChecked])
                paths["setup_dir_dataframe_filepath"] = fl

                self.setup_table_widget.fill_table()
                # self.GUI.system_tab.setup_table_widget.fill_table()
        else:
            info = InformationDialog(info_text="No setups were selected to be removed")
            info.exec()

    def get_summary(self):
        """Get summary information for the set of selected mice"""

        isChecked = []
        for row in range(self.setup_table_widget.rowCount()):
            checked = self.setup_table_widget.item(row, 0).checkState() == 2
            isChecked.append(checked)

        if any(isChecked):
            sd = CageSummaryDialog()
            sd.show()
            sd.exec_()
        else:
            info = InformationDialog(info_text="No setups were selected to get a summary")
            info.exec()
