# from .hx711_spi import HX711
from .hx711_gpio import HX711
from .RWD_QT import RWD_QT
import time


class Access_control_upy:
    # Class instantiated on the pyboard mounted on the Access Control 1.1 PCB.

    def __init__(self):
        self.loadcell = HX711(data_pin="X7", clock_pin="X8", gain=128)
        self.rfid = RWD_QT(bus=6, cts="X21")
