from pyb import UART
from time import sleep


class uRFID:
    # Class for using the Priority 1 Design Micro RFID module to read FDX-B tags.
    # http://www.priority1design.com.au/rfid_reader_modules.html
    # Ref: https://www.priority1design.com.au/rfidrw-e-ttl.pdf

    def __init__(self, bus):
        self.uart = UART(bus)
        self.uart.init(baudrate=9600, bits=8, parity=None, stop=1, timeout=1)
        self.uart.write(b"ST2\r")  # Put reader in FDX-B tag mode.
        sleep(0.01)
        self.uart.read()  # Clear input buffer.

    def read_tag(self):
        # Return the ID of the most recent tag read, if not tag has been read return None.
        self.uart.write(b"RAT\r")  # Call Read Animal Tag function.
        read_bytes = self.uart.read()
        if read_bytes is None:
            return None  # No messages in UART
        else:
            msgs = read_bytes.split(b"\r")  # Split message by <crn>
        for msg in msgs:
            if msg is b"?1":
                return None  # Error: No read
            else:
                parts = msg.split(b"_")  # Split valid message into component parts
                return parts[1].decode()  # Return the second part of the message as a string
