from .data_logger import Data_logger


class homecage_logger(Data_logger):
    """This class builds on the data_logger class and adds functionality for
    starting and stopping sessions based on the entry of mice in and out
    of the training box. It should be connected to both the pycboard class
    of a given setup as well as the access_control class in order to function
    correctly
    """

    def __init__(self, sm_info=None, print_func=None, data_consumers=[]):
        self.data_file = None
        self.print_func = print_func
        self.data_consumers = data_consumers
        self.mice_in_setup = []
        self.n_mice = len(self.mice_in_setup)
        self.mouse_training = False
        self.A1_ = True
        self.exit_door_open = False

    def get_mouse_in_cage(self):
        pass

    def _start_new_session(self):
        pass
