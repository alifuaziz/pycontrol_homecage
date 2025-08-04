import time
from functools import partial
from serial import SerialException
import pandas as pd
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QTableWidget,
    QAbstractItemView,
    QTableWidgetItem,
    QPushButton,
)

from source.communication.access_control import Access_control
from source.communication.pycboard import PyboardError, Pycboard
from source.communication.system_handler import system_controller
from source.dialogs import CalibrationDialog, InformationDialog, DirectPyboardDialog

from ..utils import find_pyboards
import db as database


class SetupTable(QTableWidget):
    """This table contains information about the setups currently"""

    def __init__(self, tab=None):
        super(QTableWidget, self).__init__(1, 12, parent=None)
        self.header_names = [
            "Select",
            "Setup_ID",
            "Connection",
            "Access Control Test",
            "pyControl Test",
            "Experiment",
            "Protocol",
            "Mouse_training",
            "COM",
            "COM_AC",
            "in_use",
            "connected",
            "User",
            "AC_state",
            "Door_Mag",
            "Door_Sensor",
            "n_mice",
            "mice_in_setup",
        ]

        self.tab = tab
        self.setHorizontalHeaderLabels(self.header_names)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.select_column_idx = self.header_names.index("Select")
        self.connect_column_idx = self.header_names.index("Connection")  # column index of connect button
        self.integration_test_colum_idx = self.header_names.index("Access Control Test")
        self.pycontrol_test_column_idx = self.header_names.index("pyControl Test")

        self.fill_table()

        #### Functions for populating the table

    def fill_table(self) -> None:
        self.clearContents()
        self.setRowCount(len(database.setup_df))

        self.buttons = []
        for row_index, row in database.setup_df.iterrows():
            self.fill_table_row(row_index=row_index, row=row)

    def fill_table_row(self, row_index, row) -> None:
        self.populate_cells_from_database(row_index, row)

        # Connect Button
        connect_button = self._build_connect_button(row)
        self.buttons.append(connect_button)
        if self.tab is None:  # if this is the table in system overview
            connect_button.setEnabled(False)
        self.setCellWidget(row_index, self.connect_column_idx, connect_button)

        # Access Control Test Button
        access_control_test_button = self._build_access_control_test_button(row)
        self.buttons.append(access_control_test_button)
        self.setCellWidget(row_index, self.integration_test_colum_idx, access_control_test_button)

        # pyControl test button
        pycontrol_test_button = self._build_pycontrol_test_button(row)
        self.buttons.append(pycontrol_test_button)
        self.setCellWidget(row_index, self.pycontrol_test_column_idx, pycontrol_test_button)

        chkBoxItem = QTableWidgetItem()
        chkBoxItem.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
        chkBoxItem.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.setItem(row_index, self.select_column_idx, chkBoxItem)

    def populate_cells_from_database(self, row_index: int, row: pd.Series):
        for col_index in range(self.columnCount()):
            try:
                cHeader = self.header_names[col_index]
                self.setItem(
                    row_index,
                    col_index,
                    QTableWidgetItem(str(row[cHeader])),
                )
            except KeyError:
                pass

    #### Integration test button

    def _build_access_control_test_button(self, row: pd.Series) -> QPushButton:
        """
        Intantiate AccessControlIntegrationTestDialog
        """
        button = QPushButton("Access Control Test")
        button.name = [row["Setup_ID"], row["COM"], row["COM_AC"]]
        button.clicked.connect(self.start_access_control_test)
        return button

    def start_access_control_test(self):
        """Integration testing dialgog"""
        setup_id, com_, comAC_ = self.sender().name
        try:
            dialog = CalibrationDialog(access_control_pyboard=database.controllers[setup_id].AC)
            dialog.exec()
        except KeyError:
            info = InformationDialog(info_text="The setup has not been connected yet so can not be tested")
            info.exec()

    def _build_pycontrol_test_button(self, row: pd.Series) -> QPushButton:
        """Initialise pycontrol_Test button"""
        button = QPushButton("Task Testing")
        button.name = [row["Setup_ID"], row["COM"], row["COM_AC"], row["Protocol"]]
        button.clicked.connect(self.start_pycontrol_test)
        return button

    def start_pycontrol_test(self):
        """If the Protocol Column contains an entry which ends in a .prot file extension, you know that it is a protocol. So open a protocol dialog instead of the direct access control one."""
        setup_id, com_, comAC_, protocol = self.sender().name

        try:
            # if protocol.endswith(".prot"):
            #     dialog = DirectProtocolDialog(setup_id=setup_id)
            #     dialog.exec()
            # else:
            dialog = DirectPyboardDialog(setup_id=setup_id)
            dialog.exec()
        except KeyError:
            info = InformationDialog(info_text="The setup has not been connected yet so can not be tested")
            info.exec()

    #### Connect button

    def _build_connect_button(self, row: pd.Series) -> QPushButton:
        """
        Set properties of button that allows you to connect to the serial ports
        controlling one of the setups
        """
        if row["connected"]:
            buttonText = "Connected"
        else:
            buttonText = "Connect"

        button = QPushButton(buttonText)
        button.name = [row["Setup_ID"], row["COM"], row["COM_AC"]]
        button.clicked.connect(self.connect)
        return button

    def connect(self):
        """
        Connect to the to pyboards for the access control and the task control pyboards.

        Notes on sender().name.
        - This is the name metadata that came from the object that called the function. In this case it is the `cageTable._build_connect_button`
        that called this function.

        """
        try:
            setup_id, com_, comAC_ = self.sender().name

            print_func = partial(print, flush=True)

            print_func("Connecting to com:", com_)

            pycontrol_board = Pycboard(serial_port=com_, print_func=print_func)
            pycontrol_board.load_framework()
            access_control_board = Access_control(serial_port=comAC_, print_func=print_func)
            access_control_board.load_framework()
            SC = system_controller(
                PYC=pycontrol_board, AC=access_control_board, print_func=print_func, setup_ID=setup_id
            )

            send_name = self.sender().name
            self._fill_setup_df_row(send_name)
            database.controllers[setup_id] = SC
            time.sleep(0.05)
            self.tab.callibrate_dialog = CalibrationDialog(access_control_pyboard=access_control_board)
            # database.print_consumers[MessageRecipient.calibrate_dialog] = self.tab.callibrate_dialog.print_msg
            self.tab.callibrate_dialog.exec()
            # del database.print_consumers[MessageRecipient.calibrate_dialog]

            self.sender().setEnabled(False)
            self.fill_table()

            # Update the list_of_setups table.
            database.update_table_queue.append("system_tab.list_of_setups")

        except (PyboardError, SerialException) as e:
            info = InformationDialog(
                info_text="Failed to connect to pyboard. \
                \nConsider the following causes for a failed connection: \
                \n- 'Access Denied' The board can only be accessed by one program at a time. If a different REPL is connect it will block pyControlHomecage from connecting. \
                \n- 'Could not instantiate access control': Some problem with the hardware (e.g. the RFID reader handshake) causing the instantiation to fail. \
                \n- Hard resetting the pyboard (Some weird problem with the flash storage)"
            )
            info.exec()
            print(e, flush=True)
            print("Failed to connect", flush=True)

    def _fill_setup_df_row(self, sender_name: list[str]) -> None:
        _, com_, _ = sender_name
        database.setup_df["connected"].loc[database.setup_df["COM"] == com_] = True  # Connected to AC board
        database.setup_df["in_use"].loc[database.setup_df["COM"] == com_] = False  # Setup not in use on init
        database.setup_df["n_mice"].loc[database.setup_df["COM"] == com_] = 0  # Number of mice in setup on init

    def _refresh(self):
        """Refresh the table.

        This function checks if the ports connected"""
        ports = find_pyboards()
        ac_nr = self.header_names.index("COM")
        setup_nr = self.header_names.index("COM_AC")
        for row_idx in range(self.rowCount()):
            # Checks if the pyboards that are in the table are also connected to the host computer.
            # If they are, the ports are activate (and disabled if not).
            # Both the COM port for the access control and the experiment must be present together.
            if (self.item(row_idx, ac_nr).text() in ports) and (self.item(row_idx, setup_nr).text() in ports):
                self.cellWidget(row_idx, self.connect_column_idx).setEnabled(True)
            else:
                self.cellWidget(row_idx, self.connect_column_idx).setEnabled(False)
