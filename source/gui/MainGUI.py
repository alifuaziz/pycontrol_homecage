import os

from PyQt5.QtWidgets import QMainWindow, QTabWidget
from PyQt5 import QtCore

from source.communication.messages import MessageRecipient
from . import (
    MouseOverViewTab,
    SetupsOverviewTab,
    ProtocolAssemblyTab,
    SystemOverviewTab,
    ExperimentOverviewTab,
)
from source.dialogs import LoginDialog, AddUserDialog
import db as database


class MainGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.GUI_filepath = os.path.dirname(os.path.abspath(__file__))
        self.app = None  # Overwritten with QApplication instance in main.
        self.active_user = None
        self.setWindowTitle("pyControlHomeCage: Please log in")
        self.setGeometry(10, 30, 900, 800)  # Left, top, width, height.

        database.setup_df["connected"] = False

        # Initialise tabs
        self.mouse_tab = MouseOverViewTab(self)
        self.setup_tab = SetupsOverviewTab(self)
        self.protocol_tab = ProtocolAssemblyTab(self)
        self.system_tab = SystemOverviewTab(self)
        self.experiment_tab = ExperimentOverviewTab(self)
        # Add tabs to tab widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.addTab(self.system_tab, "System Overview")
        self.tab_widget.addTab(self.experiment_tab, "Experiments")
        self.tab_widget.addTab(self.mouse_tab, "Mouse Overview")
        self.tab_widget.addTab(self.setup_tab, "Setup Overview")
        self.tab_widget.addTab(self.protocol_tab, "Protocols")
        # Dict of table references
        self.table_map = {
            "system_tab.list_of_experiments": self.system_tab.experiement_overview_table,
            "system_tab.list_of_setups": self.system_tab.setup_table_widget,
            "experiment_tab.list_of_experiments": self.experiment_tab.list_of_experiments,
            "mouse_tab.list_of_mice": self.mouse_tab.mouse_table_widget,
            "setup_tab.list_of_setups": self.setup_tab.setup_table_widget,
        }

        database.print_consumers[MessageRecipient.system_overview] = self.system_tab.write_to_log

        self._disable_gui_pre_login()

        self.login = LoginDialog()
        self.add_user = AddUserDialog()

        self.system_tab.login_button.clicked.connect(self.change_user)
        self.system_tab.add_user_button.clicked.connect(self.add_user_)
        self.system_tab.logout_button.clicked.connect(self.logout_user)

        self.setCentralWidget(self.tab_widget)
        self.show()

        self._init_timer()

    # Refresh Logic --------------------------------------------------------------------

    def _init_timer(self) -> None:
        # Timer to regularly call refresh() when not running.
        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(100)

    def refresh(self) -> None:
        """
        Primary Refresh Function of the GUI.

        1. Checks for data from the pyboards currently running
        2. Refreshes the GUI tabs.
        3. Prints any messages that have entered the message queue
        """
        for controller in database.controllers.values():
            controller.check_for_data()

            if self.system_tab.plot_isactive:
                self.system_tab.experiment_plot.update()

        self.refresh_tabs()
        if database.update_table_queue:
            self._refresh_tables()

        if database.message_queue:
            self.print_dispatch()

    def refresh_tabs(self) -> None:
        """Refresh all tabs in the GUI"""
        self.setup_tab._refresh()
        self.experiment_tab._refresh()

    def _refresh_tables(self):
        """
        Function to handle the updating of tables from the database object.
        """
        # Update the tablse in order of the update tables queue.
        try:
            update_table = database.update_table_queue.pop(0)
            if update_table == "all":
                for table in self.table_map.values():
                    table.fill_table()
            else:
                self.table_map[update_table].fill_table()
        except IndexError as error:
            print(error)

    ### Printing Logic -------------------------------------------------------------------------

    def print_dispatch(self) -> None:
        """
        This function iterates over the list of print statements and dispatches them to the approprirate receivers

        Note: database.print_consumers is a callable function (which is why line 136 works to print data)
        """
        dispatched = []  # These are the messages that are dispatched
        for mix, msg in enumerate(list(database.message_queue)):
            if msg.recipient in database.print_consumers:
                database.print_consumers[msg.recipient](msg.text)
                dispatched.append(mix)

        # delete dispatched messages
        for ix in reversed(dispatched):
            del database.message_queue[ix]

        # This just ensures that this never grows out of control in terms of memory usage
        # if there is some bug the means messages for some consumer are not printed
        database.message_queue = database.message_queue[-50:]

    ### Login Functions ------------------------------------------------------------------------

    def _disable_gui_pre_login(self) -> None:
        self.mouse_tab.setEnabled(False)
        self.setup_tab.setEnabled(False)
        self.protocol_tab.setEnabled(False)
        self.system_tab.setup_groupbox.setEnabled(False)
        self.system_tab.log_groupbox.setEnabled(False)
        self.system_tab.experiment_groupbox.setEnabled(False)
        self.experiment_tab.setEnabled(False)

    def change_user(self) -> None:
        self.login.exec_()
        self.active_user = self.login.userID
        if self.active_user:
            self.setWindowTitle("pyControlHomecage: logged in as {}".format(self.active_user))
            self.mouse_tab.setEnabled(True)
            self.setup_tab.setEnabled(True)
            self.protocol_tab.setEnabled(True)
            self.system_tab.setup_groupbox.setEnabled(True)
            self.system_tab.log_groupbox.setEnabled(True)
            self.system_tab.experiment_groupbox.setEnabled(True)
            self.experiment_tab.setEnabled(True)

            # Login button update
            self.system_tab.logout_button.setEnabled(True)

    def add_user_(self) -> None:
        self.add_user.exec_()
        self.login = LoginDialog()

    def logout_user(self):
        self.active_user = None
        self.setWindowTitle("Not logged in")
        self.mouse_tab.setEnabled(False)
        self.setup_tab.setEnabled(False)
        self.protocol_tab.setEnabled(False)
        self.system_tab.setup_groupbox.setEnabled(False)
        self.system_tab.log_groupbox.setEnabled(False)
        self.system_tab.experiment_groupbox.setEnabled(False)
        self.system_tab.user_groupbox.setEnabled(True)
        self.experiment_tab.setEnabled(False)

        # Enable / disable login buttons appropriately
        self.system_tab.logout_button.setEnabled(False)
        self.system_tab.login_button.setEnabled(True)
        self.system_tab.add_user_button.setEnabled(True)
