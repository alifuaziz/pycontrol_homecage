from .hx711_gpio import HX711_drift_corrected as HX711
from .uRFID import uRFID


class Access_control_upy:
    # Class instantiated on the pyboard mounted on the Access Control 1.1 PCB.

    def __init__(self):
        self.loadcell = HX711(data_pin="X7", clock_pin="X8", gain=128, tau=1, thres=10)
        self.rfid = uRFID(bus=6)
