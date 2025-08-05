import pandas as pd
import time

from PyQt6.QtWidgets import QApplication
from source.gui.MainGUI import MainGUI
from source.utils import get_path, custom_excepthook

from source.communication.system_handler import system_controller
from source.communication.access_control import Access_control
from source.communication.pycboard import Pycboard

mice_df = r"C:\Program Files\pycontrol_homecage\data\mice\mice.csv"
mice_data = pd.read_csv(mice_df)
print(mice_data.head())


print("Pycboard")
pyc_board = Pycboard("COM4")
# pyc_board.load_framework()
print("Acess Control")
ac_board = Access_control("COM5")
# ac_board.load_framework()

sc = system_controller(AC=ac_board, PYC=pyc_board)
# Instead of directly setting up the task, use the RFID signal read from the Access control board to setup the task
sc.process_data_AC(new_data=["state:allow_entry"])  # Reset Mouse data
sc.process_data_AC(new_data=["weight:50"])  # Set Mouse data to 50gstate:
sc.process_data_AC(new_data=["RFID:116000039961"])  # Set RFID
sc.process_data_AC(new_data=["state:enter_training_chamber"])
sc.process_data_AC(new_data=["state:mouse_training"])  # Handle the mouse training

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Keyboard interrupt received, stopping the framework.")
    pyc_board.stop_framework()
