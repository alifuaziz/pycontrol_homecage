import os
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
from source.dialogs import LoginDialog, AddUserDialog
from source.gui.run_task_tab import Run_task_tab
from source.gui.setups_tab import Setups_tab
from source.gui.animals_tab import Animals_tab
import db as database


class MainGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.GUI_filepath = os.path.dirname(os.path.abspath(__file__))
        self.app = None  # Overwritten with QApplication instance in main.
        self.active_user = None
        self.setWindowTitle("pyControlHomeCage")
        self.setGeometry(10, 30, 900, 800)  # Left, top, width, height.


        self.available_ports = None
        ports = set([c[0] for c in list_ports.comports() if ("Pyboard" in c[1]) or ("USB Serial Device" in c[1])])
        self.available_ports_changed = ports != self.available_ports
        if self.available_ports_changed:
            self.available_ports = ports
            
        print(ports)
        # self.refresh()
        # Initialise tabs
        # self.run_task_tab = Run_task_tab(self)
        # self.homecage_tab = 
        self.setups_tab = Setups_tab(self)
        self.animals_tab = Animals_tab(self)

        # Add tabs to tab widget
        self.tab_widget = QTabWidget(self)
        # self.tab_widget.addTab(self.run_task_tab, "Run task")
        # self.tab_widget.addTab(self.animals_tab, "Experiments")
        self.tab_widget.addTab(self.setups_tab, "Setups")
        self.tab_widget.addTab(self.animals_tab, "Animals")

        self.setCentralWidget(self.tab_widget)
        self.show()
