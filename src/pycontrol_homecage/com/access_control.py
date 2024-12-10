import os
import re
from datetime import datetime

from numpy import source

from serial import SerialException
from .pyboard import Pyboard, PyboardError

import pycontrol_homecage.db as database
from pycontrol_homecage.com.messages import MessageRecipient, MessageSource, emit_print_message


class Access_control(Pyboard):
    # Class that runs on the main computer to provide an API for inferfacting with
    # the access control module

    def __init__(self, serial_port, print_func=print, data_logger=None):

        self.serial_port = serial_port
        self.print = print_func        # Function used for print statements.
        self.data_logger = data_logger
        self._init_variables()

        self._init_logger()
        self.init_serial_connection()

    def _init_variables(self) -> None:

        self.prev_read = None
        self.rfid = None
        self.weight = None
        self.status = {'serial': None,
                       'framework': None,
                       'usb_mode': None
                       }

    def _init_logger(self) -> None:

        name_ = database.setup_df.loc[database.setup_df['COM_AC'] == self.serial_port, 'Setup_ID'].values[0]
        now = datetime.now().strftime('-%Y-%m-%d-%H%M%S')
        self.logger_dir = database.paths['AC_logger_dir']
        self.logger_path = os.path.join(self.logger_dir, name_ + '_' + now + '.txt')

        database.setup_df.loc[database.setup_df['COM_AC'] == self.serial_port, 'logger_path'] = self.logger_path
        database.setup_df.to_csv(database.setup_df.file_location)

        with open(self.logger_path, 'w') as f:
            f.write("Start"+'\n')
            f.write(now+'\n')

    def init_serial_connection(self) -> None:
        try:
            super().__init__(self.serial_port, baudrate=115200)
            self.status['serial'] = True
            self.reset()  # Soft resets pyboard.
            self.unique_ID = eval(self.eval('pyb.unique_id()').decode())
            v_tuple = eval(
                            self.eval("sys.implementation.version if hasattr(sys, 'implementation') else (0,0,0)"
                                      ).decode()
                            )
            self.micropython_version = float('{}.{}{}'.format(*v_tuple))

        except SerialException as e:
            print('Could not connect to pyboard')
            self.status['serial'] = False
            raise(e)

    def load_framework(self) -> None:
        '''Copy the pyControl framework folder to the board.'''

        self.print('\nTransfering access control framework to pyboard.', end='')

        self.transfer_folder(database.paths["access_control_dir"], file_type='py', show_progress=True)    # upload access control framework
        self.transfer_file(os.path.join(database.paths["access_control_dir"], 'main_script_for_pyboard.py'), 'main.py')

        try:
            self.exec('from access_control_upy.access_control_1_0 import Access_control_upy')
        except PyboardError as e:
            print('Could not import access control upy modules.')
            raise(e)
        try:
            self.exec('access_control = Access_control_upy()')
        except PyboardError as e:
            print('Could not instantiate Access_control.')
            raise(e)
        try:
            # This the main script that is run on the pyboard. It controls the pin i/o  for magment and RFID
            self.exec('from main import handler')
            self.exec_raw_no_follow('handler().run()')
            # print(self.eval('print(run)'))
            pass
        except PyboardError as e:

            raise(e)
        # self.exec('run()')
        print("OK")

    def process_data(self):
        """ Here process data from buffer to update dataframes """
        # Just send each message as being 16 characters long. That way
        # can just check padding. Should be fine


        if self.serial.inWaiting() > 0:

            read = str(self.serial.read(self.serial.inWaiting()))

            messages = re.findall('start_(.*?)_end', read)
            for msg in messages:
                with open(self.logger_path, 'a') as f:
                    f.write(msg + '_' + datetime.now().strftime('-%Y-%m-%d-%H%M%S')+'\n')

            for msg in messages:
                # This is a horrible information flow. The point is simply to print
                # into the calibrate dialog
                if 'cal' in msg:

                    # if self.GUI.setup_tab.callibrate_dialog:
                    #     self.GUI.setup_tab.callibrate_dialog.print_msg(msg)
                    # if self.GUI.setup_tab.configure_box_dialog:
                    #     self.GUI.setup_tab.configure_box_dialog.print_msg(msg)
                    if MessageRecipient.calibrate_dialog in database.print_consumers:
                        emit_print_message(print_text=msg,
                                           target=MessageRecipient.calibrate_dialog,
                                           data_source=MessageSource.ACBoard
                                           )
                    if MessageRecipient.configure_box_dialog in database.print_consumers:
                        emit_print_message(print_text=msg,
                                           target=MessageRecipient.configure_box_dialog,
                                           data_source=MessageSource.ACBoard
                                           )

                self.data_logger.process_data_AC(messages)

    def loadcell_tare(self):
        self.exec('access_control.loadcell.tare()')

    def loadcell_calibrate(self, weight):
        self.exec('access_control.loadcell.calibrate({})'.format(weight))

    def loadcell_weigh(self):
        return float(self.eval('access_control.loadcell.weigh()').decode())

    def rfid_read_tag(self):
        return eval(self.eval('access_control.rfid.read_tag()').decode())
