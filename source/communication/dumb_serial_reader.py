import serial
import time

ser = serial.Serial("/dev/cu.usbmodem14142")
while True:
    try:
        if ser.inWaiting():
            print(
                ser.read(ser.inWaiting()),
            )

        time.sleep(0.05)
    except OSError:
        ser = serial.Serial("/dev/cu.usbmodem14142")
