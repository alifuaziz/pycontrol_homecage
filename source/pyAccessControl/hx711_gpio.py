from machine import Pin, enable_irq, disable_irq
import time
from .drift_corrector import DriftCorrector


class HX711:
    # Class for controlling HX711 loadcell amplifier from Micropython pyboard.
    # Adapted from https://github.com/robert-hh/hx711-lopy
    # Add loadcell drift calculations to this!

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


class HX711_drift_corrected(HX711):
    """
    HX711_drift_corrected: Drift-corrected weight measurements using HX711.

    - Extends HX711 with baseline drift correction via DriftCorrector.
    - Useful for stable, accurate animal weighing over time.

    Attributes:
    - drift_corrector: Handles baseline drift correction.

    Args:
    - data_pin (int): HX711 data GPIO (default: 22)
    - clock_pin (int): HX711 clock GPIO (default: 21)
    - gain (int): HX711 gain (default: 128)
    - tau (float): Drift corrector time constant (default: 20)
    - animal_weight (float): Expected animal weight in grams (default: 10)

    Methods:
    - weigh(times=3, timestamp=None, rfid_read=False): Returns drift-corrected weight.
    """

    def __init__(self, data_pin=22, clock_pin=21, gain=128, tau=1 / 1000000, animal_weight=10):
        super().__init__(data_pin=data_pin, clock_pin=clock_pin, gain=gain)
        self.drift_corrector = DriftCorrector(loadcell=self, tau=tau, initial_baseline=0, animal_weight=animal_weight)

    def weigh(self, times=3, timestamp=None, rfid_read=False):
        """
        Drift-corrected weight measurement.
        :param times: number of readings to average
        :param timestamp: either time.time() or RTC().datetime()
        :param rfid_read: if an RFID read confirms animal presence
        :return: drift-corrected weight in grams
        """
        self.raw_weight = super().weigh(times)

        # Get current time if not passed
        if timestamp is None:
            timestamp = time.time()

        baseline, corrected_weight, animal_in_cage = self.drift_corrector.update(
            timestamp=timestamp, measurement=self.raw_weight, rfid_read=rfid_read
        )
        return corrected_weight

    def tare(self, times=15):
        super().tare(times)
        self.drift_corrector.baseline = 0  # Should set the value to 0 since the loadcell has been tared

    def calibrate(self, weight=1, times=15, timestamp=None, rfid_read=False):
        super().calibrate(weight=weight, times=times)
        corrected_weight = self.weigh(times=times, timestamp=timestamp, rfid_read=rfid_read)
        # After calibration, set the drift corrector's baseline estimate to the current corrected weight
        # self.drift_corrector.baseline_estimate = corrected_weight

    def get_time(self):
        return time.localtime()
