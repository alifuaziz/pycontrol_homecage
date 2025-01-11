'''
File for testing if the access control can recieve signals 
'''
import time
from pycontrol_homecage.com.access_control import Access_control 
from pycontrol_homecage.com.pycboard       import Pycboard 
from pycontrol_homecage.com.system_handler import system_controller as System_Controller
# Datalogger
system_controller = System_Controller()
# Access Control
access_control = Access_control(
    serial_port = 'COM4',
    data_logger = system_controller
)
pycontrol_board = Pycboard(
    serial_port='COM3',
    data_logger=system_controller
)
# Connect parts together
system_controller.add_AC(ac=access_control)
system_controller.add_PYC(pyc=pycontrol_board)

# Write the testing file to the pyb
access_control.load_test_framework()

# Every 100ms read from the pyboard (This is what the GUI does.)
try: 
    while True:
        access_control.print_data()
        access_control.process_data()
        time.sleep(1)

except KeyboardInterrupt:
    print("Keyboard interrupt received. Exiting...")
    access_control.close()
