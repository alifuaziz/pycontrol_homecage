import time, sys, os, csv, datetime

sys.path.append(r"C:\Program Files\pycontrol_homecage")
from PyQt6.QtWidgets import QApplication
from source.gui.MainGUI import MainGUI
from source.utils import get_path, custom_excepthook

from source.communication.system_handler import system_controller
from source.communication.access_control import Access_control
from source.communication.pycboard import Pycboard

# Open comport to access control
print("Access Control")
ac_board = Access_control("COM5")
ac_board.load_framework(auto_run=False)  # Load the AC folder to board
ac_board.exec("from pyAccessControl.hx711_gpio import HX711_drift_corrected as HX711")
ac_board.exec("import time")
ac_board.exec('loadcell = HX711(data_pin="X7", clock_pin="X8", gain=128)')
input("Please remove all items from the scale and press Enter to continue...")
ac_board.exec("loadcell.tare()")
ac_board.eval("loadcell.baseline")

weight = input("Please enter the weight for calibration (in grams): ")
ac_board.exec("loadcell.calibrate({})".format(weight))

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs("./weight_data", exist_ok=True)
filename = f"./weight_data/weight_log_{timestamp}.csv"
print(f"Opening weight log: {filename}")

with open(filename, "a", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(
        ["Timestamp Tuple", "Raw Weight", "Corrected Weight"]
    )  # Open CSV file for recording the information
    try:
        while True:
            corrected_weight = ac_board.eval("loadcell.weigh()").decode()
            ac_board.eval("loadcell.update_baseline()")
            raw_weight = ac_board.eval("loadcell.raw_weight").decode()
            timestamp_tuple = ac_board.eval("time.localtime()")
            baseline = ac_board.eval("loadcell.baseline")
            print(f"Raw: {raw_weight} | Baseline: {baseline} | Corrected: {corrected_weight}")
            writer.writerow([timestamp_tuple, raw_weight, corrected_weight])
            # Run faster to test the rate of updating
            if int(time.time()) % 10 == 0:
                time.sleep(0.2)  # Every 10 seconds, sample faster
            else:
                time.sleep(1)
    except KeyboardInterrupt:
        print("Closing weight log and exiting.")
