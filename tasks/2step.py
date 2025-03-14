from pyControl.utility import *
import hardware_definition as hw


# States and events.

states = [
    "init_trial",
    "state1",
    "state2",
    "state3",
    "left_reward",
    "right_reward",
    "inter_trial_interval",
]

events = [
    "left_poke",
    "right_poke",
    "center_poke",
    "session_timer",
]

initial_state = "init_trial"

v.session_duration = 1 * hour
v.ITI_duration = 1 * second  # Inter trial interval duration.
v.reward_duration = 100
v.transition_prob = 0.7
# Moving averages for outcomes
v.tau_state2 = 8  # Time constsant for moving average
v.state2_good_prob_ave = Exp_mov_ave(tau=v.tau_state2, init_value=0.5)  # Moving average of correct/incorrect choices
v.state2_good_prob = v.state2_good_prob_ave.value
v.tau_state3 = 8  # Time constsant for moving average
v.state3_good_prob_ave = Exp_mov_ave(tau=v.tau_state3, init_value=0.5)  # Moving average of correct/incorrect choices
v.state3_good_prob = v.state3_good_prob_ave.value

# Run start and stop behaviour.


def run_start():
    # Set session timer and turn on houslight.
    set_timer("session_timer", v.session_duration)
    hw.houselight.on()


def run_end():
    # Turn off all hardware outputs.
    hw.off()


# State behaviour functions.


def init_trial(event):
    if event == "entry":
        hw.center_poke.LED.on()
    elif event == "exit":
        hw.center_poke.LED.off()
    elif event == "center_poke":
        goto_state("state1")


def state1(event):
    if event == "entry":
        hw.left_poke.LED.on()
        hw.right_poke.LED.on()
    elif event == "exit":
        hw.left_poke.LED.off()
        hw.right_poke.LED.off()
    elif event == "left_poke":  # left
        if withprob(v.transition_prob):
            goto_state("state2")
        else:
            goto_state("state3")
    elif event == "right_poke":  # right
        if withprob(v.transition_prob):
            goto_state("state3")
        else:
            goto_state("state2")


def state2(event):
    if event == "entry":
        hw.left_poke.LED.on()
        hw.right_poke.LED.on()
    elif event == "exit":
        hw.left_poke.LED.off()
        hw.right_poke.LED.off()
    elif event == "left_poke":  # left
        if withprob(v.state2_good_prob):
            goto_state("left_reward")
        else:
            goto_state("inter_trial_interval")
    elif event == "right_poke":  # right
        if withprob(v.state2_good_prob):
            goto_state("right_reward")
        else:
            goto_state("inter_trial_interval")


def state3(event):
    if event == "entry":
        hw.left_poke.LED.on()
        hw.right_poke.LED.on()
    elif event == "exit":
        hw.left_poke.LED.off()
        hw.right_poke.LED.off()
    elif event == "left_poke":  # left
        if withprob(v.state3_good_prob):
            goto_state("left_reward")
        else:
            goto_state("inter_trial_interval")
    elif event == "right_poke":  # right
        if withprob(v.state3_good_prob):
            goto_state("right_reward")
        else:
            goto_state("inter_trial_interval")


def left_reward(event):
    # Deliver reward to left poke.
    if event == "entry":
        timed_goto_state("inter_trial_interval", v.reward_duration)
        hw.left_poke.SOL.on()
    elif event == "exit":
        hw.left_poke.SOL.off()


def right_reward(event):
    # Deliver reward to right poke.
    if event == "entry":
        timed_goto_state("inter_trial_interval", v.reward_duration)
        hw.right_poke.SOL.on()
    elif event == "exit":
        hw.right_poke.SOL.off()


def inter_trial_interval(event):
    # Go to init trial after specified delay.
    if event == "entry":
        timed_goto_state("init_trial", v.ITI_duration)

    # update the exp moving averages
    v.state2_good_prob_ave.update(1)
    v.state2_good_prob = v.state2_good_prob_ave.value
    v.state3_good_prob_ave.update(1)
    v.state3_good_prob = v.state3_good_prob_ave.value


# State independent behaviour.


def all_states(event):
    # When 'session_timer' event occurs stop framework to end session.
    if event == "session_timer":
        stop_framework()
