import time
from functools import partial

from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
)
from serial import SerialException
import pandas as pd

from pycontrol_homecage.com.access_control import Access_control
from pycontrol_homecage.com.pycboard import PyboardError, Pycboard
from pycontrol_homecage.com.system_handler import system_controller

# from pycontrol_homecage.com.messages import MessageRecipient
from pycontrol_homecage.dialogs import (
    CalibrationDialog,
    InformationDialog,
    DirectPyboardDialog,
    DirectProtocolDialog,
)
from pycontrol_homecage.utils import find_pyboards
import pycontrol_homecage.db as database


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
        self.setEditTriggers(QTableWidget.NoEditTriggers)

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
        chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        chkBoxItem.setCheckState(QtCore.Qt.Unchecked)
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
            dialog.exec_()
        except KeyError:
            info = InformationDialog(info_text="The setup has not been connected yet so can not be tested")
            info.exec_()

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
            #     dialog.exec_()
            # else:
            dialog = DirectPyboardDialog(setup_id=setup_id)
            dialog.exec_()
        except KeyError:
            info = InformationDialog(info_text="The setup has not been connected yet so can not be tested")
            info.exec_()

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
            # if the setup has had an attempted reconnect. Reconnect requires that any pyboards that have been connected are released
            try:
                if database.controllers[setup_id]:
                    # disconnect the access control
                    access_control_board = database.connected_access_controls[setup_id]
                    access_control_board.close()
                    # Remove from dictionary
                    del database.connected_access_controls[setup_id]

                    # disconnect the pycontrol_board
                    pycontrol_board = database.connected_pycontrol_boards[setup_id]
                    pycontrol_board.close()
                    # remove from dictionary
                    del database.connected_pycontrol_boards[setup_id]
            except Exception:
                print(
                    "One of the two boards hadn't been connnected or properly initalised so it did not appear the the dicts."
                )
                print("So it can't be removed.")
            # Button metadata

            print_func = partial(print, flush=True)
            SC = system_controller(print_func=print_func, setup_id=setup_id)
            print("Connecting to com:", com_, flush=True)
            board = Pycboard(com_, print_func=print_func, data_logger=SC)

            board.load_framework()
            time.sleep(0.05)
            database.connected_pycontrol_boards[setup_id] = board
            access_control_board = Access_control(comAC_, print_func=print_func, data_logger=SC)
            time.sleep(0.05)
            # System controller gets access to the pycontrol board (That runs the operant box task)
            SC.add_PYC(board)
            # Add it also getes access to the access control board (That run the access control module)
            SC.add_AC(access_control_board)

            # Load the access control framework on the access control board.
            access_control_board.load_framework()
            database.connected_access_controls[setup_id] = access_control_board

            send_name = self.sender().name
            self._fill_setup_df_row(send_name)
            database.controllers[setup_id] = SC
            time.sleep(0.05)
            self.tab.callibrate_dialog = CalibrationDialog(access_control_pyboard=access_control_board)
            # database.print_consumers[MessageRecipient.calibrate_dialog] = self.tab.callibrate_dialog.print_msg
            self.tab.callibrate_dialog.exec_()
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
            info.exec_()
            print(e, flush=True)
            print("Failed to connect", flush=True)

    def _fill_setup_df_row(self, sender_name: list[str]) -> None:
        """
        Alif guessing:
        The default of the connection is:
        - Once connected, that entry in the table should reflect this.
        - If it has just been connected, the setup is not in use.
        - IF it has just been connected, the setups also has no mice in it ()


        """
        _, com_, _ = sender_name
        # Connnected to the pyboard
        database.setup_df["connected"].loc[database.setup_df["COM"] == com_] = True
        # The setups starts off not in use?
        database.setup_df["in_use"].loc[database.setup_df["COM"] == com_] = False
        # Number of mice set to 0?
        database.setup_df["n_mice"].loc[database.setup_df["COM"] == com_] = 0

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
