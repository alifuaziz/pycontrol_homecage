from pyControl.utility import *
import hardware_definition as hw

# States and events.

states = ['reward_available',
          'reward',
          'no_reward',
          'ITI']

events = ['poke_9', 
          'poke_9_out',
          'rsync',
          'session_timer']

initial_state = 'reward_available'


# Variables.

v.n_rewards = 0
v.reward_duration = 150*ms
v.mean_inter_reward_interval = 10*second
v.session_duration = 10 * minute
v.reward_probability=0.9

# State behaviour.

def run_start():
    # hw.houselight.on()
    set_timer('session_timer', v.session_duration)

def ITI(event):
    if event == 'entry':
        timed_goto_state('reward_available', exp_rand(v.mean_inter_reward_interval))

def reward_available(event):
    # if event == 'entry':
    #     hw.poke_9.LED.on()
    if ((event == 'poke_9') and withprob(v.reward_probability)):
        goto_state('reward')
    else:
        goto_state('no_reward')

def reward(event):
    if event == 'entry':
        v.n_rewards += 1
        print('Reward: {}'.format(v.n_rewards))
        hw.poke_9.SOL.on()
        # hw.poke_9.LED.off()
        hw.BNC_1.on()
        timed_goto_state('ITI', v.reward_duration)
    elif event == 'exit':
        hw.poke_9.SOL.off()
        hw.BNC_1.off()

def no_reward(event)
    if event == 'entry':
        # hw.poke_9.LED.off()
        timed_goto_state('ITI', v.reward_duration)
    elif event == 'exit':


def all_states(event):
    if event == 'session_timer':
        stop_framework()