import math
import time


class DriftCorrector:
    """
    Correcting the loadcell drift.
    See: https://nvlpubs.nist.gov/nistpubs/jres/102/3/j23bar.pdf for theortical reason why it could exist.
    """

    def __init__(
        self, loadcell, tau=20, initial_baseline=0, initial_timestamp=None, animal_weight=10, animal_in_cage=False
    ):
        """
        tau: decay parameter for exponetial moving average
        initial_weight: inital baseline estimate of the loadcell weight (grams)
        animal_weight: weight of a animal (grams)
        """
        self.loadcell = loadcell
        self.baseline_estimate = initial_baseline
        self.weight_measurement = 0
        self.TAU = tau
        self.mouse_weight = animal_weight
        self.THRES_RATIO = 0.4
        self.animal_in_cage = False
        # self.animal_in_cage = animal_in_cage
        self.last_timestamp = initial_timestamp

    def update(self, timestamp, measurement: float = None, rfid_read: bool = False):
        """
        measurement: weight measurement from loadcell (grams)
        timestamp: when the measurement came into the class
        returns:
            tuple[baseline estimate, weight measurement]
        """
        # Convert timestamp tuple into int
        if isinstance(timestamp, tuple):
            if len(timestamp) == 9:
                timestamp = time.mktime(timestamp)
        # Use timestamp instead of sample rate to update the EMA
        if self.last_timestamp is None:
            # self.last_timestamp = time.mktime(timestamp)
            self.last_timestamp = timestamp
        dt = timestamp - self.last_timestamp
        self.last_timestamp = timestamp
        alpha = 1 - pow(math.e, -dt / self.TAU)  # alpha = 1 - exp(-dt/tau)

        # Update EMA & baseline weight
        if not self.animal_in_cage:
            self.baseline_estimate += alpha * (measurement - self.baseline_estimate)
        # Calculate the weight measurement
        self.weight_measurement = measurement - self.baseline_estimate

        return self.baseline_estimate, self.weight_measurement, self.animal_in_cage
