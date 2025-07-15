# Task where the animal simply pokes for water

from pyControl.utility import *
from devices import *

# -------- Hardware --------
poke_1 = Digital_input("X1", rising_event="poke_1")
valve_1 = Digital_output("X2")

# -------- Variables --------
valve_open_time = 50 * ms

# -------- States --------
states = ["wait_for_poke", "deliver_water"]

# -------- Events --------
events = ["poke_1"]

# -------- Initial state --------
initial_state = "wait_for_poke"


# -------- State behavior --------
def wait_for_poke(event):
    if event == "poke_1":
        goto_state("deliver_water")


def deliver_water(event):
    if event == "entry":
        valve_1.on()
        timed_goto_state("wait_for_poke", valve_open_time)
    elif event == "exit":
        valve_1.off()
