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
from pycontrol_homecage.dialogs import CalibrationDialog
from pycontrol_homecage.utils import find_setups
import pycontrol_homecage.db as database


class SetupTable(QTableWidget):
    """This table contains information about the setups currently"""

    def __init__(self, tab=None):
        super(QTableWidget, self).__init__(1, 12, parent=None)
        self.header_names = [
            "Select",
            "Setup_ID",
            "Connection",
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

        self.select_col_ix = self.header_names.index("Select")
        self.connect_col_ix = self.header_names.index(
            "Connection"
        )  # column index of connect button

        self.fill_table()

    def fill_table(self) -> None:
        self.clearContents()
        self.setRowCount(len(database.setup_df))

        self.buttons = []
        for row_index, row in database.setup_df.iterrows():
            self.fill_table_row(row_index=row_index, row=row)

    def fill_table_row(self, row_index, row) -> None:
        self.populate_cells_from_database(row_index, row)

        button = self._build_connect_button(row)
        self.buttons.append(button)

        if self.tab is None:  # if this is the table in system overview
            button.setEnabled(False)

        self.setCellWidget(row_index, self.connect_col_ix, button)

        chkBoxItem = QTableWidgetItem()
        chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        chkBoxItem.setCheckState(QtCore.Qt.Unchecked)
        self.setItem(row_index, self.select_col_ix, chkBoxItem)

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

    def _build_connect_button(self, row: pd.Series):
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
            # Button metadata
            setup_id, com_, comAC_ = self.sender().name

            print_func = partial(print, flush=True)
            SC = system_controller(print_func=print_func, setup_id=setup_id)
            print("Connecting to com:", com_, flush=True)
            board = Pycboard(com_, print_func=print_func, data_logger=SC)

            board.load_framework()
            time.sleep(0.05)
            database.connected_boards.append(board)
            ac = Access_control(comAC_, print_func=print_func, data_logger=SC)
            time.sleep(0.05)
            # System controller gets access to the pycontrol board (That runs the operant box task)
            SC.add_PYC(board)
            # Add it also getes access to the access control board (That run the access control module)
            SC.add_AC(ac)

            # Load the access control framework on the access control board.
            ac.load_framework()
            database.connected_access_controls.append(ac)

            send_name = self.sender().name
            self._fill_setup_df_row(send_name)
            database.controllers[setup_id] = SC
            time.sleep(0.05)
            self.tab.callibrate_dialog = CalibrationDialog(access_control_pyboard=ac)
            # database.print_consumers[MessageRecipient.calibrate_dialog] = self.tab.callibrate_dialog.print_msg
            self.tab.callibrate_dialog.exec_()
            # del database.print_consumers[MessageRecipient.calibrate_dialog]

            self.sender().setEnabled(False)
            self.fill_table()
            # self.GUI.system_tab.list_of_setups.fill_table()
            database.update_table_queue.append("system_tab.list_of_setups")

        except (PyboardError, SerialException) as e:
            print(e, flush=True)
            print("Failed to connect", flush=True)

    def _fill_setup_df_row(self, sender_name: list[str]) -> None:
        """
        Just fill that row of the df

        send_name: the list of metadata associated with the button press.

        """
        _, com_, _ = sender_name
        database.setup_df["connected"].loc[database.setup_df["COM"] == com_] = True
        database.setup_df["in_use"].loc[database.setup_df["COM"] == com_] = False
        database.setup_df["connected"].loc[database.setup_df["COM"] == com_] = True
        database.setup_df["n_mice"].loc[database.setup_df["COM"] == com_] = 0

    def _refresh(self):
        ports = find_setups()

        ac_nr = self.header_names.index("COM")
        setup_nr = self.header_names.index("COM_AC")
        for row_nr in range(self.rowCount()):
            if (self.item(row_nr, ac_nr).text() in ports) and (
                self.item(row_nr, setup_nr).text() in ports
            ):
                self.cellWidget(row_nr, self.connect_col_ix).setEnabled(True)
            else:
                self.cellWidget(row_nr, self.connect_col_ix).setEnabled(False)
