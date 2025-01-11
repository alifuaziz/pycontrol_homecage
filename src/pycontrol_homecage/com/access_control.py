import os
import re
from datetime import datetime

from numpy import source

from serial import SerialException
from .pyboard import Pyboard, PyboardError

import pycontrol_homecage.db as database
from pycontrol_homecage.com.messages import MessageRecipient, MessageSource, emit_print_message
# from pycontrol_homecage.com.system_handler import system_controller

class Access_control(Pyboard):
    # Class that runs on the main computer to provide an API for inferfacting with
    # the access control module

    def __init__(self, serial_port, print_func=print, data_logger=None):

        self.serial_port = serial_port
        self.print = print_func        # Function used for print statements.
        self.data_logger = data_logger # This is set to the system_controller. Ideally this would be done on initalisation, however this could lead to a circular depenadncy
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
        '''
        This function opens the file which the data from the pyboard is written to. The self.process_data() function then
        writes the data that is returned the host computer to 
        '''
        try: 
            name_ = database.setup_df.loc[database.setup_df['COM_AC'] == self.serial_port, 'Setup_ID'].values[0]
        except IndexError:
            available_controls = database.setup_df['COM_AC'].tolist()
            raise IndexError(f"No entry found in setups_df for COM_AC = {self.serial_port}. Available access controls: {available_controls}")
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

    def load_test_framework(self) -> None:
        ''' 
        Script for generating artificial signals
        
        This function mirrors the normal `load_framework` function.
        '''
        
        self.print('\nTransfering `state_signal_generator` to the python board.')
        
        # Load signal generator
        self.transfer_file(os.path.join(database.paths["access_control_dir"], 'state_signal_generator.py'), 'state_signal_generator.py')
        
        try: 
            self.exec_raw_no_follow("import state_signal_generator")
        except PyboardError as e:
            raise e
        
        self.print('OK')
            
    def load_framework(self) -> None:
        '''
        Copy the pyControl framework folder to the board. Then run the main script that runs the firmware on the board. 
        
        
        The commands run on the board are: 
        from access_control_upy.access_control_1_0 import Access_control_upy
        access_control = Access_control_upy()
                
        '''

        self.print('\nTransfering access control framework to pyboard.', end='')

        self.transfer_folder(database.paths["access_control_dir"], file_type='py', show_progress=True)    # upload access control framework
        self.transfer_file(os.path.join(database.paths["access_control_dir"], 'main_script_for_pyboard.py'), 'main.py')

        # Access Control Hardware
        
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
        
        
        # Handler Class 
        
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

    def print_data(self):
        '''Another testing function by Alif. 
        This will read the output of the serial port of the access control to the host computer.
        '''
        # print(self.serial.inWaiting())
        if self.serial.inWaiting() > 0 : 
            read = str(self.serial.read(self.serial.inWaiting()))

            messages = re.findall('start_(.*?)_end', read)
            for msg in messages:
                with open('access_control_testing_log.txt', 'a') as f:
                    f.write(msg + '_' + datetime.now().strftime('-%Y-%m-%d-%H%M%S')+'\n')


    def process_data(self):
        """ Here process data from buffer to update dataframes 
        This is not where the data updates anything about the states of the 
        """
        # Just send each message as being 16 characters long. That way
        # can just check padding. Should be fine


        if self.serial.inWaiting() > 0:

            read = str(self.serial.read(self.serial.inWaiting()))

            messages = re.findall('start_(.*?)_end', read)
            print(f'messages:{messages}')
            for msg in messages:
                print(f'msg:{msg}')
                with open(self.logger_path, 'a') as f:
                    f.write(msg + '_' + datetime.now().strftime('-%Y-%m-%d-%H%M%S')+'\n')

            for msg in messages:
                # This is a horrible information flow. The point is simply to print
                # into the calibrate dialog
                if 'cal' in msg:
                    '''
                    datbase.print_consumers is a list of callable functions. They are specifically being used to print to 
                    different parts of the GUI depending on what the recipient of the message should be.
                    The reason for the if statement below is that these print functions are only used if they are defined during the initalisation.
                    If they are not then the `emit_print_message` function can not work. 
                    '''

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
                    
                    
                # The message is passed to another function to be 'processed'
                self.data_logger.process_data_AC(messages)

    def loadcell_tare(self):
        self.exec('access_control.loadcell.tare()')

    def loadcell_calibrate(self, weight):
        self.exec('access_control.loadcell.calibrate({})'.format(weight))

    def loadcell_weigh(self):
        return float(self.eval('access_control.loadcell.weigh()').decode())

    def rfid_read_tag(self):
        return eval(self.eval('access_control.rfid.read_tag()').decode())
