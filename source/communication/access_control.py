import os
import re
import time
import inspect
from datetime import datetime

from serial import SerialException
from .pyboard import Pyboard, PyboardError
from .pycboard import Pycboard, _djb2_file, _receive_file
from .system_handler import system_controller
import db as database
from source.gui.settings import user_folder
from source.communication.messages import (
    MessageRecipient,
    MessageSource,
    emit_print_message,
)

# ----------------------------------------------------------------------------------------
#  Access_control class.
# ----------------------------------------------------------------------------------------


class Access_control(Pycboard):
    """Inherits from Pycboard and replaces pyControl functionality with Access Control specific behaviour.
    This allows interface with the access control hardward"""

    def __init__(self, serial_port, print_func=print):
        self.serial_port = serial_port
        self.print = print_func  # Function used for print statements.
        self.data_logger = None  # This is set to the system_controller. Ideally this would be done on initalisation, this leads to cicular dependancy

        # Init variables
        self.prev_read = None
        self.rfid = None
        self.weight = None
        self.status = {"serial": None, "framework": None, "usb_mode": None}

        self._init_logger()
        # Initialise Serial connection
        try:
            super().__init__(self.serial_port, baudrate=115200)
            self.status["serial"] = True
            self.reset()  # Soft resets pyboard.
            self.unique_ID = eval(self.eval("pyb.unique_id()").decode())
            v_tuple = eval(
                self.eval("sys.implementation.version if hasattr(sys, 'implementation') else (0,0,0)").decode()
            )
            self.micropython_version = float("{}.{}{}".format(*v_tuple))
        except SerialException as e:
            print("Could not connect to pyboard")
            self.status["serial"] = False
            raise (e)

    def reset(self):
        """Enter raw repl (soft reboots), imports modules"""
        self.enter_raw_repl()  # Soft resets pyboard.
        self.exec(inspect.getsource(_djb2_file))  # define djb2 hashing function.
        self.exec(inspect.getsource(_receive_file))  # define receive file function.
        self.exec("import os; import gc; import sys; import pyb")
        self.status["usb_mode"] = self.eval("pyb.usb_mode()").decode()
        if (
            self.data_logger
        ):  # This is required since the system handler requires both the pycboard and the acboard to init
            self.data_logger.reset()

    def _init_logger(self) -> None:
        """
        This function opens the file which the data from the pyboard is written to. The self.process_data() function then
        writes the data that is returned the host computer to
        """
        try:
            name_ = database.setup_df.loc[database.setup_df["COM_AC"] == self.serial_port, "Setup_ID"].values[0]
        except IndexError:
            available_controls = database.setup_df["COM_AC"].tolist()
            raise IndexError(
                f"No entry found in setups_df for COM_AC = {self.serial_port}. Available access controls: {available_controls}"
            )
        now = datetime.now().strftime("-%Y-%m-%d-%H%M%S")
        self.logger_dir = user_folder("AC_logger_dir")
        self.logger_path = os.path.join(self.logger_dir, name_ + "_" + now + ".txt")

        database.setup_df.loc[database.setup_df["COM_AC"] == self.serial_port, "logger_path"] = self.logger_path
        database.setup_df.to_csv(user_folder("setup_dir_dataframe_filepath"))

        with open(self.logger_path, "w") as f:
            f.write("Start" + "\n")
            f.write(now + "\n")

    # ------------------------------------------------------------------------------------
    # Access Control operations.
    # ------------------------------------------------------------------------------------

    def load_framework(self, auto_run=True) -> None:
        """
        Copy the Access Control framework folder to the micropython board.
        if auto_run = True:
            The Firmware automatically starts
        """
        self.print("\nTransfering Access Control framework to pyboard.", end="")
        self.transfer_folder(
            user_folder("access_control_dir"), file_type="py", show_progress=True
        )  # upload access control framework
        self.transfer_file(
            os.path.join("source", "pyAccessControl", "main_script_for_pyboard.py"),
            "main.py",
        )
        try:  # Instantiate Hardware definition into pyboard
            self.exec("from pyAccessControl.access_control_1_0 import Access_control_upy")
        except PyboardError as e:
            print("Could not import access control upy modules.")
            raise (e)
        try:
            self.exec("access_control = Access_control_upy()")
        except PyboardError as e:
            print("Could not instantiate Access_control.")
            raise (e)
        try:  # Begin Running
            if auto_run:
                self.print("\nBeginning Access Control framework...")
                self.exec("from main import handler")
                self.exec_raw_no_follow("handler().run()")
        except PyboardError as e:
            raise (e)
        print("OK")

    def process_data(self):
        """Here process data from buffer to update dataframes
        This is not where the data updates anything about the states of the
        """
        # Just send each message as being 16 characters long. That way
        # can just check padding. Should be fine

        if self.serial.inWaiting() > 0:
            read = str(self.serial.read(self.serial.inWaiting()))

            messages = re.findall("start_(.*?)_end", read)
            print(f"messages:{messages}")
            for msg in messages:
                print(f"msg:{msg}")
                with open(self.logger_path, "a") as f:
                    f.write(msg + "_" + datetime.now().strftime("-%Y-%m-%d-%H%M%S") + "\n")

            for msg in messages:
                # This is a horrible information flow. The point is simply to print
                # into the calibrate dialog
                if "cal" in msg:
                    """
                    datbase.print_consumers is a list of callable functions. They are specifically being used to print to
                    different parts of the GUI depending on what the recipient of the message should be.
                    The reason for the if statement below is that these print functions are only used if they are defined during the initalisation.
                    If they are not then the `emit_print_message` function can not work.
                    """
                    if MessageRecipient.calibrate_dialog in database.print_consumers:
                        emit_print_message(
                            print_text=msg,
                            target=MessageRecipient.calibrate_dialog,
                            data_source=MessageSource.ACBoard,
                        )
                    if MessageRecipient.configure_box_dialog in database.print_consumers:
                        emit_print_message(
                            print_text=msg,
                            target=MessageRecipient.configure_box_dialog,
                            data_source=MessageSource.ACBoard,
                        )

                # The message is passed to another function to be 'processed'
                self.data_logger.process_data_AC(messages)

    # ------------------------------------------------------------------------------------
    # Getting and setting access control hardware information.
    # ------------------------------------------------------------------------------------

    def loadcell_tare(self):
        self.exec("access_control.loadcell.tare()")

    def loadcell_calibrate(self, weight):
        self.exec("access_control.loadcell.calibrate({})".format(weight))

    def loadcell_weigh(self):
        return float(self.eval("access_control.loadcell.weigh()").decode())

    def rfid_read_tag(self):
        return eval(self.eval("access_control.rfid.read_tag()").decode())
