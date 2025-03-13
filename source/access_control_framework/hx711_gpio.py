from machine import Pin, enable_irq, disable_irq
import time


class HX711:
    # Class for controlling HX711 loadcell amplifier from Micropython pyboard.
    # Adapted from https://github.com/robert-hh/hx711-lopy

    def __init__(self, data_pin, clock_pin, gain=128):
        self.pSCK = Pin(clock_pin, mode=Pin.OUT)
        self.pOUT = Pin(data_pin, mode=Pin.IN, pull=Pin.PULL_DOWN)
        self.pSCK.value(False)

        self.GAIN = 0
        self.OFFSET = 0
        self.SCALE = 3500

        self.time_constant = 0.25
        self.filtered = 0

        self.set_gain(gain)

    def set_gain(self, gain):
        if gain == 128:
            self.GAIN = 1
        elif gain == 64:
            self.GAIN = 3
        elif gain == 32:
            self.GAIN = 2

        self.read()
        self.filtered = self.read()

    def read(self):
        # wait for the device being ready
        for _ in range(500):
            if self.pOUT() == 0:
                break
            time.sleep_ms(1)
        else:
            raise OSError("Sensor does not respond")

        # shift in data, and gain & channel info
        result = 0
        for j in range(24 + self.GAIN):
            state = disable_irq()
            self.pSCK(True)
            self.pSCK(False)
            enable_irq(state)
            result = (result << 1) | self.pOUT()

        # shift back the extra bits
        result >>= self.GAIN

        # check sign
        if result > 0x7FFFFF:
            result -= 0x1000000

        return result

    def read_average(self, times=3):
        sum = 0
        for i in range(times):
            sum += self.read()
        return sum / times

    def weigh(self, times=3):
        return (self.read_average(times) - self.OFFSET) / self.SCALE

    def tare(self, times=15):
        # Set the 0 value.
        self.OFFSET = self.read_average(times)

    def calibrate(self, weight=1, times=15):
        # Calibrate the scale using a known weight, must be done after scale has been tared.
        self.SCALE = (self.read_average(times) - self.OFFSET) / weight

    def power_down(self):
        self.pSCK.value(False)
        self.pSCK.value(True)

    def power_up(self):
        self.pSCK.value(False)
