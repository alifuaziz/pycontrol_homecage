import pandas as pd
import time

from PyQt5.QtWidgets import QApplication
from source.gui.MainGUI import MainGUI
from source.utils import get_path, custom_excepthook

from source.communication.system_handler import system_controller
from source.communication.access_control import Access_control
from source.communication.pycboard import Pycboard

mice_df = r"C:\Users\alifa\OneDrive - Nexus365\Documents\Homecage Software Development\fork\pycontrol_homecage\data\mice\mice.csv"
mice_data = pd.read_csv(mice_df)
print(mice_data.head())


print("Pycboard")
pyc_board = Pycboard("COM8")
pyc_board.load_framework()
print("Acess Control")
ac_board = Access_control("COM3")
ac_board.load_framework()

sc= system_controller(AC=ac_board, PYC=pyc_board)
print(mice_data.iloc[0]['Task'])

#### Direct interface with pyc_board does not do logging of data correctly ### This should be interfaced with via the system_controller.
# This will allow use of the
pyc_board.load_hardware_definition(r"C:\Users\alifa\OneDrive - Nexus365\Documents\Homecage Software Development\fork\pycontrol_homecage\hardware_definitions\hardware_definition_9_poke_boxes.py")
pyc_board.setup_state_machine("2step",uploaded=False)
pyc_board.start_framework()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Keyboard interrupt received, stopping the framework.")
    pyc_board.stop_framework()

