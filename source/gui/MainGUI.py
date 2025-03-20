import os
import platform
import ctypes
from serial.tools import list_ports
from PyQt5.QtWidgets import QMainWindow, QTabWidget
from PyQt5 import QtCore

# from source.communication.messages import MessageRecipient
# from . import (
# MouseOverViewTab,
# ProtocolAssemblyTab,
# SystemOverviewTab,
# ExperimentOverviewTab,
# )
# from source.dialogs import LoginDialog, AddUserDialog
from source.gui.settings import VERSION, get_setting, user_folder
from source.gui.run_task_tab import Run_task_tab
from source.gui.setups_tab import Setups_tab
from source.gui.animals_tab import Animals_tab
from source.gui.homecages_tab import Homecage_tab
import db as database

if platform.system() == "Windows":  # Needed on windows to get taskbar icon to display correctly.
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("pyControlHomeCage")


class MainGUI(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.setWindowTitle(f"pyControlHomeCage v{VERSION}")
        self.setGeometry(10, 30, 700, 800)  # Left, top, width, height.
        self.GUI_filepath = os.path.dirname(os.path.abspath(__file__))

        # Variables
        self.refresh_interval = 1000  # How often refresh method is called when not running (ms).
        self.available_tasks = None  # List of task file names in tasks folder.
        self.available_ports = None  # List of available serial ports.
        self.available_experiments = None  # List of experiment in experiments folder.
        self.available_tasks_changed = False
        self.available_experiments_changed = False
        self.available_ports_changed = False
        self.task_directory = user_folder("tasks")
        self.data_dir_changed = False
        self.current_tab_ind = 0  # Which tab is currently selected.
        self.app = app

        # Get a list of the ports         
        ports = set([c[0] for c in list_ports.comports() if ("Pyboard" in c[1]) or ("USB Serial Device" in c[1])])
        self.available_ports_changed = ports != self.available_ports
        if self.available_ports_changed:
            self.available_ports = ports

        print(self.available_ports)

        # Initialise tabs
        self.setups_tab = Setups_tab(self)
        self.homecage_tab = Homecage_tab(self)
        self.animals_tab = Animals_tab(self)
        self.run_task_tab = Run_task_tab(self)

        # Add tabs to tab widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.addTab(self.run_task_tab, "Run task")
        # self.tab_widget.addTab(self.animals_tab, "Experiments")
        self.tab_widget.addTab(self.setups_tab, "Setups")
        self.tab_widget.addTab(self.animals_tab, "Animals")
        self.tab_widget.addTab(self.homecage_tab, "Homecages")
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        self.setCentralWidget(self.tab_widget)
        self.show()

        # Timer
        self.refresh_timer = QtCore.QTimer()  # Timer to regularly call refresh() when not running.
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(self.refresh_interval)

        self.refresh()

    def refresh(self):

        self.run_task_tab.refresh()

    def on_tab_changed(self):
        """Delect, then reselect tabs"""
        self.current_tab_ind = self.tab_widget.currentIndex()
        if self.current_tab_ind == self.tab_widget.indexOf(self.homecage_tab):
            self.homecage_tab.tab_selected()
