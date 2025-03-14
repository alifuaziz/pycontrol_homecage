
from PyQt5.QtWidgets import QApplication
from source.gui.MainGUI import MainGUI
from source.utils import get_path, custom_excepthook


from source.communication.access_control import Access_control

ac_board = Access_control(serial_port="COM3")
ac_board.load_framework()