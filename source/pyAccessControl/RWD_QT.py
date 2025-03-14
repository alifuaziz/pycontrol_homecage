from time import sleep_ms
from pyb import UART, Pin


class RWD_QT:
    def __init__(self, bus=4, cts="X8"):
        self.uart = UART(bus, baudrate=9600)
        self.cts = Pin(cts, Pin.IN)
        ack1 = self.write_read(b"P\x00\x00", 100)  # Set polling delay to 0
        ack2 = self.write_read(b"v\x03", 100)  # Set tag type to EM400X
        if ack1 == ack2 == b"\xc0":
            print("RWD_QT setup OK.")
        else:
            print("RWD_QT setup error")
            print(ack1)
            print(ack2)

    def write_read(self, buf, delay):
        # Write buf to UART when cts pin is low, wait specified
        # delay before reading reply, return reply.
        self.uart.read()  # Clear any data in the uart buffer.
        while self.cts.value() == 1:
            sleep_ms(1)
        self.uart.write(buf)
        sleep_ms(delay)
        return self.uart.read()

    def read_tag(self):
        # Read a tag, return integer tag ID if present otherwise -1.
        x = self.write_read(b"R\x00", 150)
        if x == None or len(x) == 1:  # No tag present.
            return None
        else:  # Tag read OK.
            return int.from_bytes(x[1:], "little")

    def get_status(self):
        # return status message string.
        return self.write_read(b"z", 150)  # Status message


def getbits(char):
    # Convert a 1 byte character into list of bits, useful
    # for reading error flags in acknowledge bytes.
    "Return string of bits encoding char, lsb last."
    return [(char >> i) & 1 for i in range(7, -1, -1)]
