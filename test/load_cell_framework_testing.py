import pandas as pd
import time

from PyQt6.QtWidgets import QApplication
from source.gui.MainGUI import MainGUI
from source.utils import get_path, custom_excepthook

from source.communication.system_handler import system_controller
from source.communication.access_control import Access_control
from source.communication.pycboard import Pycboard

print("Access Control")
ac_board = Access_control("COM11")
# Load the AC folder to board
ac_board.load_framework(auto_run=True)
#
