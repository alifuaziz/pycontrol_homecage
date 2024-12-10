#!/usr/bin/env python

"""
pyboard interface
This module provides the Pyboard class, used to communicate with and
control the pyboard over a serial USB connection.
Example usage:
    import pyboard
    pyb = pyboard.Pyboard('/dev/c')
    pyb.enter_raw_repl()
    pyb.exec('pyb.LED(1).on()')
    pyb.exit_raw_repl()
To run a script from the local machine on the board and print out the results:
    import pyboard
    pyboard.execfile('test.py', device='/dev/ttyACM0')
This script can also be run directly.  To execute a local script, use:
    ./pyboard.py test.py
Or:
    python pyboard.py test.py
"""
import os
import sys
import time
import serial
import inspect
from serial import SerialException
from array import array

# ----------------------------------------------------------------------------------------
#  Helper functions.
# ----------------------------------------------------------------------------------------

# djb2 hashing algorithm used to check integrity of transfered files.
def _djb2_file(file_path):
    with open(file_path, 'rb') as f:
        h = 5381
        while True:
            c = f.read(4)
            if not c:
                break
            h = ((h << 5) + h + int.from_bytes(c,'little')) & 0xFFFFFFFF           
    return h

# Used on pyboard to remove directories or files.
def _rm_dir_or_file(i):
    try:
        os.remove(i)
    except OSError:
        os.chdir(i)
        for j in os.listdir():
            _rm_dir_or_file(j)
        os.chdir('..')
        os.rmdir(i)

# Used on pyboard to clear filesystem.
def _reset_pyb_filesystem():
    os.chdir('/flash')
    for i in os.listdir():
        if i not in ['System Volume Information', 'boot.py']:
            _rm_dir_or_file(i)

# Used on pyboard for file transfer.
def _receive_file(file_path, file_size):
    gc.collect()
    usb = pyb.USB_VCP()
    usb.setinterrupt(-1)
    buf_size = 512
    buf = bytearray(buf_size)
    buf_mv = memoryview(buf)
    bytes_remaining = file_size
    with open(file_path, 'wb') as f:
        while bytes_remaining > 0:
            bytes_read = usb.recv(buf, timeout=5)
            usb.write(b'0')
            if bytes_read:
                bytes_remaining -= bytes_read
                f.write(buf_mv[:bytes_read])
    gc.collect()

def stdout_write_bytes(b):
    sys.stdout.buffer.write(b)
    sys.stdout.buffer.flush()

class PyboardError(BaseException):
    pass


# ----------------------------------------------------------------------------------------
#  Main Pyboard class shared betweeen pyboard.py and access_control.py
# ----------------------------------------------------------------------------------------

class Pyboard:
    def __init__(self, serial_device, baudrate=115200):
        self.serial = serial.Serial(serial_device, baudrate=baudrate, interCharTimeout=1)

    def close(self):
        self.serial.close()

    def read_until(self, min_num_bytes, ending, timeout=10, data_consumer=None):
        data = self.serial.read(min_num_bytes)
        if data_consumer:
            data_consumer(data)
        timeout_count = 0
        while True:
            if data.endswith(ending):
                break
            elif self.serial.inWaiting() > 0:
                new_data = self.serial.read(1)
                data = data + new_data
                if data_consumer:
                    data_consumer(new_data)
                timeout_count = 0
            else:
                timeout_count += 1
                if timeout is not None and timeout_count >= 10 * timeout:
                    break
                time.sleep(0.1)
        return data

    def enter_raw_repl(self):
        self.serial.write(b'\r\x03\x03') # ctrl-C twice: interrupt any running program
        # flush input (without relying on serial.flushInput())
        n = self.serial.inWaiting()
        while n > 0:
            self.serial.read(n)
            n = self.serial.inWaiting()
        self.serial.write(b'\r\x01') # ctrl-A: enter raw REPL
        data = self.read_until(1, b'to exit\r\n>')
        if not data.endswith(b'raw REPL; CTRL-B to exit\r\n>'):
            print(data)
            raise PyboardError('could not enter raw repl')
        self.serial.write(b'\x04') # ctrl-D: soft reset
        data = self.read_until(1, b'to exit\r\n>')
        if not data.endswith(b'raw REPL; CTRL-B to exit\r\n>'):
            print(data)
            raise PyboardError('could not enter raw repl')

    def exit_raw_repl(self):
        self.serial.write(b'\r\x02') # ctrl-B: enter friendly REPL

    def follow(self, timeout, data_consumer=None):
        # wait for normal output
        data = self.read_until(1, b'\x04', timeout=timeout, data_consumer=data_consumer)
        if not data.endswith(b'\x04'):
            raise PyboardError('timeout waiting for first EOF reception')
        data = data[:-1]

        # wait for error output
        data_err = self.read_until(2, b'\x04>', timeout=timeout)
        if not data_err.endswith(b'\x04>'):
            raise PyboardError('timeout waiting for second EOF reception')
        data_err = data_err[:-2]

        # return normal and error output
        return data, data_err

    def exec_raw_no_follow(self, command):
        if isinstance(command, bytes):
            command_bytes = command
        else:
            command_bytes = bytes(command, encoding='utf8')

        # write command
        for i in range(0, len(command_bytes), 256):
            self.serial.write(command_bytes[i:min(i + 256, len(command_bytes))])
            time.sleep(0.01)
        self.serial.write(b'\x04')

        # check if we could exec command
        data = self.serial.read(2)
        if data != b'OK':
            raise PyboardError('could not exec command')

    def exec_raw(self, command, timeout=10, data_consumer=None):
        self.exec_raw_no_follow(command);
        return self.follow(timeout, data_consumer)

    def eval(self, expression):
        ret = self.exec('print({})'.format(expression))
        ret = ret.strip()
        return ret

    def exec(self, command):
        ret, ret_err = self.exec_raw(command)
        if ret_err:
            raise PyboardError('exception', ret, ret_err)
        return ret

    def execfile(self, filename):
        with open(filename, 'rb') as f:
            pyfile = f.read()
        return self.exec(pyfile)

    def get_time(self):
        t = str(self.eval('pyb.RTC().datetime()'), encoding='utf8')[1:-1].split(', ')
        return int(t[4]) * 3600 + int(t[5]) * 60 + int(t[6])



    # ------------------------------------------------------------------------------------
    # Other set of functions ported from previous pycboard class.
    # ------------------------------------------------------------------------------------


    def reset(self):
        '''Enter raw repl (soft reboots pyboard), import modules.'''
        self.enter_raw_repl() # Soft resets pyboard.
        self.exec(inspect.getsource(_djb2_file))  # define djb2 hashing function.
        self.exec(inspect.getsource(_receive_file))  # define recieve file function.
        self.exec('import os; import gc; import sys; import pyb')
        self.framework_running = False
        error_message = None
        self.status['usb_mode'] = self.eval('pyb.usb_mode()').decode()
        try:
            self.exec('from pyControl import *; import devices')
            self.status['framework'] = True # Framework imported OK.
        except PyboardError as e:
            error_message = e.args[2].decode()
            if (("ImportError: no module named 'pyControl'" in error_message) or
                ("ImportError: no module named 'devices'"   in error_message)):
                self.status['framework'] = None # Framework not installed.
            else:
                self.status['framework'] = False # Framework import error.
        return error_message

    def hard_reset(self, reconnect=True):
        self.print('\nResetting pyboard.')
        try:
            self.exec_raw_no_follow('pyb.hard_reset()')
        except PyboardError:
            pass
        self.close()    # Close serial connection.
        if reconnect:
            time.sleep(5.)  # Wait 5 seconds before trying to reopen serial connection.
            try: 
                super().__init__(self.serial_port, baudrate=115200) # Reopen serial conection.
                self.reset()
            except SerialException:
                self.print('Unable to reopen serial connection.')
        else:
            self.print('\nSerial connection closed.')

    def gc_collect(self): 
        '''Run a garbage collection on pyboard to free up memory.'''
        self.exec('gc.collect()')
        time.sleep(0.01)

    def DFU_mode(self):
        '''Put the pyboard into device firmware update mode.'''
        self.exec('import pyb')
        try:
            self.exec_raw_no_follow('pyb.bootloader()')
        except PyboardError as e:
            pass # Error occurs on older versions of micropython but DFU is entered OK.
        self.print('\nEntered DFU mode, closing serial connection.\n')
        self.close()

    def disable_mass_storage(self):
        '''Modify the boot.py file to make the pyboards mass storage invisible to the
        host computer.'''
        self.print('\nDisabling USB flash drive')
        self.write_file('boot.py', "import machine\nimport pyb\npyb.usb_mode('VCP')")
        self.hard_reset(reconnect=False)

    def enable_mass_storage(self):
        '''Modify the boot.py file to make the pyboards mass storage visible to the
        host computer.'''
        self.print('\nEnabling USB flash drive')
        self.write_file('boot.py', "import machine\nimport pyb\npyb.usb_mode('VCP+MSC')")
        self.hard_reset(reconnect=False)



    # ------------------------------------------------------------------------------------
    # Pyboard filesystem operations.
    # ------------------------------------------------------------------------------------

    def write_file(self, target_path, data):
        '''Write data to file at specified path on pyboard, any data already
        in the file will be deleted.'''
        try:
            self.exec("with open('{}','w') as f: f.write({})".format(target_path, repr(data)))
        except PyboardError as e:
            raise PyboardError(e)

    def get_file_hash(self, target_path):
        '''Get the djb2 hash of a file on the pyboard.'''
        try:
            file_hash = int(self.eval("_djb2_file('{}')".format(target_path)).decode())
        except PyboardError as e: # File does not exist.
            return -1  
        return file_hash

    def transfer_file(self, file_path, target_path=None):
        '''Copy file at file_path to location target_path on pyboard.'''
        if not target_path:
            target_path = os.path.split(file_path)[-1]
        file_size = os.path.getsize(file_path)
        file_hash = _djb2_file(file_path)
        try:
            for i in range(10):
                    if file_hash == self.get_file_hash(target_path):
                        return
                    try:
                        self.remove_file(file_path)
                    except PyboardError:
                        pass
                    self.exec_raw_no_follow("_receive_file('{}',{})"
                                            .format(target_path, file_size))
                    with open(file_path, 'rb') as f:
                        while True:
                            chunk = f.read(512)
                            if not chunk:
                                break
                            self.serial.write(chunk)
                            self.serial.read(1)
                    self.follow(5)
        except PyboardError as e:
            self.print('\n\nError: Unable to transfer file.')
            raise PyboardError

    def transfer_folder(self, folder_path, target_folder=None, file_type='all',
                        show_progress=False):
        '''Copy a folder into the root directory of the pyboard.  Folders that
        contain subfolders will not be copied successfully.  To copy only files of
        a specific type, change the file_type argument to the file suffix (e.g. 'py').'''
        if not target_folder:
            target_folder = os.path.split(folder_path)[-1]
        files = os.listdir(folder_path)
        if file_type != 'all':
            files = [f for f in files if f.split('.')[-1] == file_type]
        try:
            self.exec('os.mkdir({})'.format(repr(target_folder)))
        except PyboardError:
            pass # Folder already exists.
        for f in files:
            file_path = os.path.join(folder_path, f)
            target_path = target_folder + '/' + f
            print(f'\nfile_path:{file_path}', f'target_path:{target_path}')
            self.transfer_file(file_path, target_path)
            if show_progress:
                self.print('.', end='')
                sys.stdout.flush()

    def remove_file(self, file_path):
        '''Remove a file from the pyboard.'''
        self.exec('os.remove({})'.format(repr(file_path)))

    def reset_filesystem(self):
        '''Delete all files in the flash drive apart from boot.py'''
        self.print('Resetting filesystem.')
        self.reset()
        self.exec(inspect.getsource(_rm_dir_or_file))
        self.exec(inspect.getsource(_reset_pyb_filesystem)) 
        self.exec_raw('_reset_pyb_filesystem()', timeout=60)
        self.hard_reset() 

def execfile(filename, device='/dev/ttyACM0'):
    pyb = Pyboard(device)
    pyb.enter_raw_repl()
    output = pyb.execfile(filename)
    stdout_write_bytes(output)
    pyb.exit_raw_repl()
    pyb.close()