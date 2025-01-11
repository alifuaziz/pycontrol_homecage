'''
File for Creating the state signals
'''
import pyb
import time


# Instantiate serial comport
com = pyb.USB_VCP()
# Visual indications of the Commands being sent indicated by the pins
red    = pyb.LED(1)
green  = pyb.LED(2)
yellow = pyb.LED(3)
blue   = pyb.LED(4)


# Define the build_message function
def build_msg(x):
    return 'start_' + x + '_end'
# Commands that could be sent by the micropython board
state_commands= [
    'state:allow_entry', 
    'RFID:1234',
    'weight:100',
    'state:mouse_training', 
    'state:allow_exit'
    ]

while True:
    # emit the commands in an other 
    yellow.off()
    blue.on()
    com.write(build_msg(state_commands[0]))
    time.sleep(1)
    blue.off()
    red.on()
    com.write(build_msg(state_commands[1]))
    time.sleep(1)
    red.off()
    green.on()
    com.write(build_msg(state_commands[2]))
    time.sleep(1)
    green.off()
    yellow.on()
    com.write(build_msg(state_commands[3]))
    time.sleep(1)
    com.write(build_msg(state_commands[4]))
    time.sleep(1)
    