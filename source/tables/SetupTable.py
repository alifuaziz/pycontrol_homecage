import time
from functools import partial
from serial import SerialException
from PyQt6 import QtCore
from PyQt6.QtWidgets import QTableWidget, QAbstractItemView, QTableWidgetItem, QPushButton

from source.communication.access_control import Access_control
from source.communication.pycboard import PyboardError, Pycboard
from source.communication.system_handler import system_controller
from source.dialogs import CalibrationDialog, InformationDialog, DirectPyboardDialog

from ..utils import find_pyboards
import db as database
from PyQt6.QtWidgets import QMenu


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
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.select_column_idx = self.header_names.index("Select")
        self.connect_column_idx = self.header_names.index("Connection")  # column index of connect button
        self.fill_table()

    def fill_table(self):
        # Fill table
        self.clearContents()
        self.setRowCount(len(database.setup_df))
        self.buttons = []
        for row_index, row in database.setup_df.iterrows():
            # Set header names
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
            # Create Connect Button
            if row["connected"]:
                buttonText = "Connected"
            else:
                buttonText = "Connect"
            connect_button = QPushButton(buttonText)
            connect_button.name = [row["Setup_ID"], row["COM"], row["COM_AC"]]
            connect_button.clicked.connect(self.connect)
            connect_button.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            connect_button.customContextMenuRequested.connect(partial(self._show_connect_button_menu, row))
            connect_button.setToolTip("Right-click for more options")
            self.buttons.append(connect_button)
            if self.tab is None:  # if this is the table in system overview
                connect_button.setEnabled(False)
            self.setCellWidget(row_index, self.connect_column_idx, connect_button)
            # Create Checkbox button
            chkBoxItem = QTableWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.setItem(row_index, self.select_column_idx, chkBoxItem)

    #### Build Buttons

    def _show_connect_button_menu(self, row, pos):
        """
        Show a context menu for the connect button with additional actions.
        """

        connect_button_menu = QMenu()
        disconnect_action = connect_button_menu.addAction("Disconnect")
        calibration_action = connect_button_menu.addAction("Open Calibration Dialog")
        pycontrol_test_action = connect_button_menu.addAction("pyControl Test")
        access_control_test_action = connect_button_menu.addAction("Access Control Test")

        action = connect_button_menu.exec(self.sender().mapToGlobal(pos))
        setup_id = row["Setup_ID"]

        if action == disconnect_action:
            if setup_id in database.controllers:
                database.controllers[setup_id].disconnect()
                print(f"Disconnected from Setup {setup_id}")
                del database.controllers[setup_id]
                database.setup_df.loc[database.setup_df["Setup_ID"] == setup_id, "connected"] = False
                self.fill_table()
        elif action == calibration_action:
            if setup_id not in database.controllers:
                info = InformationDialog(info_text="The setup has not been connected yet so cannot be tested")
                info.exec()
            else:
                dialog = CalibrationDialog(access_control_pyboard=database.controllers[setup_id].AC)
                dialog.exec()
        elif action == pycontrol_test_action:
            if setup_id not in database.controllers:
                info = InformationDialog(info_text="The setup has not been connected yet so cannot be tested")
                info.exec()
            else:
                self.start_pycontrol_test()
        elif action == access_control_test_action:
            if setup_id not in database.controllers:
                info = InformationDialog(info_text="The setup has not been connected yet so cannot be tested")
                info.exec()
            else:
                self.start_access_control_test()

    # Test funcitons

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

    def start_access_control_test(self):
        """Integration testing dialgog"""
        setup_id, com_, comAC_ = self.sender().name
        try:
            dialog = CalibrationDialog(access_control_pyboard=database.controllers[setup_id].AC)
            dialog.exec()
        except KeyError:
            info = InformationDialog(info_text="The setup has not been connected yet so can not be tested")
            info.exec()

    #### Connect button

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
            # Attempt to disconnect any partially connected boards
            try:
                if "pycontrol_board" in locals() and pycontrol_board is not None:
                    print("Closing connection to pyControl board...")
                    pycontrol_board.close()
            except Exception as disconnect_error:
                print(f"Error disconnecting pycontrol_board: {disconnect_error}", flush=True)
            try:
                if "access_control_board" in locals() and access_control_board is not None:
                    print("Closing connection to Access Control board...")
                    access_control_board.close()
            except Exception as disconnect_error:
                print(f"Error disconnecting access_control_board: {disconnect_error}", flush=True)

            info = InformationDialog(
                info_text="Failed to connect to pyboard. \
                \nConsider the following causes for a failed connection: \
                \n- 'Access Denied' The board can only be accessed by one program at a time. If a different REPL is connect it will block pyControlHomecage from connecting. \
                \n- 'Could not instantiate access control': Some problem with the hardware (e.g. the RFID reader handshake) causing the instantiation to fail. \
                \n- Hard resetting the pyboard (Some problem with the flash storage)"
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
