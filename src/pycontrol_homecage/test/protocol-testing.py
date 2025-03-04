'''
Script for testing whether protocols change for a mouse.

Tested: 
- Script is able to set pycontrol task from the .prot file (and load in the .prot file)

Not tested: 
- Progressing the stage to a new stage
- Loading in the mouse_log_df variables from a previous pycontrol session and loading then into the new instances of the state mahcien. 

'''
from pycontrol_homecage.com.system_handler import system_controller
from pycontrol_homecage.com.pycboard import Pycboard
import pycontrol_homecage.db as database

pyc = Pycboard(serial_port='COM7')

sh = system_controller(
    setup_id='setup1'
)
MOUSE = "first-protocol-mouse"

sh._handle_allow_entry()
sh.mouse_data["RFID"] = 98765432120

sh.add_PYC(pyc=pyc)

mouse_row = database.mouse_df.loc[database.mouse_df["Mouse_ID"] == MOUSE]
print(mouse_row)


sh.run_mouse_protocol(
    mouse_info_row=mouse_row
)

pyc.close()
print("Script has ended")