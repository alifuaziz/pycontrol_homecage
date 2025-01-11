'''
Testing the system controller script outside the gui to see it if works as I expect it to. 
This also means I can avoid YW's execption handling. 
Testing the connect function in system_controller.
'''
# %% Imports

import time
from functools import partial # https://stackoverflow.com/questions/15331726/how-does-functools-partial-do-what-it-does

from pycontrol_homecage.com.system_handler import system_controller as SystemController
from pycontrol_homecage.com.pycboard import Pycboard
from pycontrol_homecage.com.access_control import Access_control
# Import the database
import pycontrol_homecage.db as database

# %% Define constants
# CONSTANTS
COM_AC = 'COM4'
COM_PYC = 'COM3'
SETUP_ID = 'setup1'

# %% Instantiate pycontrol_board and system_controller
# Re-defines the print function where the kwarg `flush` is always true. 
print_func = partial(print, flush=True)
# Datalogger class (This is the object that writes things to disk
system_controller = SystemController(print_func=print_func, setup_id=SETUP_ID)
# Instantiate Pycontrol board
pycontrol_board = Pycboard(serial_port=COM_PYC, 
                           print_func=print_func, data_logger=system_controller)
# Load the pycontrol_framework
pycontrol_board.load_framework()
time.sleep(0.05)
# ?? event queuing ??
database.connected_boards.append(pycontrol_board)
# %% Instantiate Access Control Board
# Instantiate Access_control
access_control = Access_control(serial_port=COM_AC, 
                                print_func=print_func,
                                data_logger=system_controller)
time.sleep(0.05)

# %% Add Pointers to both the pyb boards
# System controller gets access to the pycontrol board (That runs the operant box task)
system_controller.add_PYC(pycontrol_board)
# Add it also getes access to the access control board (That run the access control module)
system_controller.add_AC(access_control)


# %% Load access control framework to pycontrol board
# Load the access control framework on the access control board. 
access_control.load_framework()
# ?? event queuing ??
database.connected_access_controls.append(access_control)




# send_name = self.sender().name
# self._fill_setup_df_row(send_name)
# database.controllers[setup_id] = SC
# time.sleep(0.05)
# self.tab.callibrate_dialog = calibrate_dialog(ac=ac)
# # database.print_consumers[MessageRecipient.calibrate_dialog] = self.tab.callibrate_dialog.print_msg
# self.tab.callibrate_dialog.exec_()
# # del database.print_consumers[MessageRecipient.calibrate_dialog]

# self.sender().setEnabled(False)
# self.fill_table()
# # self.GUI.system_tab.list_of_setups.fill_table()
# database.update_table_queue.append("system_tab.list_of_setups")

# %%
