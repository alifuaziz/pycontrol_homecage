import os
import re
import time
import inspect
from datetime import datetime

from serial import SerialException
from .pyboard import Pyboard, PyboardError
from .pycboard import Pycboard

import db as database
from source.gui.settings import user_folder
from source.communication.messages import (
    MessageRecipient,
    MessageSource,
    emit_print_message,
)

# ----------------------------------------------------------------------------------------
#  Helper functions.
# ----------------------------------------------------------------------------------------


# djb2 hashing algorithm used to check integrity of transfered files.
def _djb2_file(file_path):
    with open(file_path, "rb") as f:
        h = 5381
        while True:
            c = f.read(4)
            if not c:
                break
            h = ((h << 5) + h + int.from_bytes(c, "little")) & 0xFFFFFFFF
    return h


# Used on pyboard for file transfer.
def _receive_file(file_path, file_size):
    usb = pyb.USB_VCP()
    usb.setinterrupt(-1)
    buf_size = 512
    buf = bytearray(buf_size)
    buf_mv = memoryview(buf)
    bytes_remaining = file_size
    try:
        with open(file_path, "wb") as f:
            while bytes_remaining > 0:
                bytes_read = usb.recv(buf, timeout=5)
                usb.write(b"OK")
                if bytes_read:
                    bytes_remaining -= bytes_read
                    f.write(buf_mv[:bytes_read])
    except:
        fs_stat = os.statvfs("/flash")
        fs_free_space = fs_stat[0] * fs_stat[3]
        if fs_free_space < bytes_remaining:
            usb.write(b"NS")  # Out of space.
        else:
            usb.write(b"ER")


# ----------------------------------------------------------------------------------------
#  Access_control class.
# ----------------------------------------------------------------------------------------


class Access_control(Pyboard):
    # Class that runs on the main computer to provide an API for inferfacting with
    # the access control module

    def __init__(self, serial_port, print_func=print):
        self.serial_port = serial_port
        self.print = print_func  # Function used for print statements.
        self.data_logger = None  # This is set to the system_controller. Ideally this would be done on initalisation, however this could lead to a circular depenadncy

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
        pass

    def gc_collect(self):
        """Run a garbage collection on pyboard to free up memory."""
        self.exec("gc.collect()")
        time.sleep(0.01)

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
    # Pyboard filesystem operations.
    # ------------------------------------------------------------------------------------

    def write_file(self, target_path, data):
        """Write data to file at specified path on pyboard, any data already
        in the file will be deleted."""
        try:
            self.exec("with open('{}','w') as f: f.write({})".format(target_path, repr(data)))
        except PyboardError as e:
            raise PyboardError(e)

    def get_file_hash(self, target_path):
        """Get the djb2 hash of a file on the pyboard."""
        try:
            file_hash = int(self.eval("_djb2_file('{}')".format(target_path)).decode())
        except PyboardError:  # File does not exist.
            return -1
        return file_hash

    def transfer_file(self, file_path, target_path=None):
        """Copy file at file_path to location target_path on pyboard."""
        if not target_path:
            target_path = os.path.split(file_path)[-1]
        file_size = os.path.getsize(file_path)
        file_hash = _djb2_file(file_path)
        error_message = (
            "\n\nError: Unable to transfer file. See the troubleshooting docs:\n"
            "https://pycontrol.readthedocs.io/en/latest/user-guide/troubleshooting/"
        )
        # Try to load file, return once file hash on board matches that on computer.
        for i in range(10):
            if file_hash == self.get_file_hash(target_path):
                return
            self.exec_raw_no_follow("_receive_file('{}',{})".format(target_path, file_size))
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(512)
                    if not chunk:
                        break
                    self.serial.write(chunk)
                    response_bytes = self.serial.read(2)
                    if response_bytes != b"OK":
                        if response_bytes == b"NS":
                            self.print("\n\nInsufficient space on pyboard filesystem to transfer file.")
                        else:
                            self.print(error_message)
                        time.sleep(0.01)
                        self.serial.reset_input_buffer()
                        raise PyboardError
                self.follow(3)
        # Unable to transfer file.
        self.print(error_message)
        raise PyboardError

    def transfer_folder(
        self, folder_path, target_folder=None, file_type="all", files="all", remove_files=True, show_progress=False
    ):
        """Copy a folder into the root directory of the pyboard.  Folders that
        contain subfolders will not be copied successfully.  To copy only files of
        a specific type, change the file_type argument to the file suffix (e.g. 'py').
        To copy only specified files pass a list of file names as files argument."""
        if not target_folder:
            target_folder = os.path.split(folder_path)[-1]
        if files == "all":
            files = os.listdir(folder_path)
            if file_type != "all":
                files = [f for f in files if f.split(".")[-1] == file_type]
        try:
            self.exec("os.mkdir({})".format(repr(target_folder)))
        except PyboardError:
            # Folder already exists.
            if remove_files:  # Remove any files not in sending folder.
                target_files = self.get_folder_contents(target_folder)
                remove_files = list(set(target_files) - set(files))
                for f in remove_files:
                    target_path = target_folder + "/" + f
                    self.remove_file(target_path)
        for f in files:
            file_path = os.path.join(folder_path, f)
            target_path = target_folder + "/" + f
            self.transfer_file(file_path, target_path)
            if show_progress:
                self.print(".", end="")

    def remove_file(self, file_path):
        """Remove a file from the pyboard."""
        try:
            self.exec("os.remove({})".format(repr(file_path)))
        except PyboardError:
            pass  # File does not exist.

    def get_folder_contents(self, folder_path, get_hash=False):
        """Get a list of the files in a folder on the pyboard, if
        get_hash=True a dict {file_name:file_hash} is returned instead"""
        file_list = eval(self.eval("os.listdir({})".format(repr(folder_path))).decode())
        if get_hash:
            return {file_name: self.get_file_hash(folder_path + "/" + file_name) for file_name in file_list}
        else:
            return file_list

    # ------------------------------------------------------------------------------------
    # Access Control operations.
    # ------------------------------------------------------------------------------------

    def load_framework(self) -> None:
        """
        Copy the pyControl framework folder to the board. Then run the main script that runs the firmware on the board.
        The commands run on the board are:
        from access_control_upy.access_control_1_0 import Access_control_upy
        access_control = Access_control_upy()
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
