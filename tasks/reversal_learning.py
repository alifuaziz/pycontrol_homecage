from pyControl.utility import *
import hardware_definition as hw

# States and events.

states = ['inter_stimulus_interval',
          'inter_stimulus_interval_baseline',
          'stimulus_A',
          'stimulus_B',
          'reward',
          'no_reward',
          'end_session']

events = ['poke_7',
          'poke_7_out',
          'poke_8',
          'poke_8_out',
          'poke_9',
          'poke_9_out']

initial_state = 'inter_stimulus_interval'

# Parameters

v.isi = [3, 15] # Inter stimulus interval (seconds). Use range of 45 -> 135 sec for actual experiment
v.stimulus_duration = 2*second # duration of CS presentations
v.reward_duration = 100 # (ms)  #duration solenoid will deliver water
v.stimulus_sampler = sample_without_replacement(['A','A','B','B']) #used to deliver CS+ and CS- in pseudorandom manner
v.max_trials = 3  #total number of CS deliveries

# Variables.
v.n_trials = 0  # trial counter, updated to reflect current trial number
v.n_rewards = 0 # reward counter, updated to reflect number of rewards delivered thus far
v.n_stim_A = 0 #... etc....
v.n_stim_B = 0
v.n_pokesA_isi = 0    #number of pokes in poke A during 10sec isi baseline
v.n_pokesB_isi = 0    #number of pokes in poke B during 10sec isi baseline
v.n_pokesA_stimA = 0  #number of pokes in poke A during stim A 
v.n_pokesA_stimB = 0  #number of pokes in poke A during stim B
v.n_pokesB_stimA = 0  #number of pokes in poke B during stim A
v.n_pokesB_stimB = 0  #number of pokes in poke B during stim B
v.n_rewardpokes_isi = 0  #number of pokes in reward poke during 10sec isi baseline
v.n_rewardpokes_stimA = 0   #number of pokes in reward poke during stim A
v.n_rewardpokes_stimB = 0   #number of pokes in reward poke during stim B

# Run start behaviour.

def run_start():
    hw.houselight.on()

def run_end():
    hw.off()

# Define behaviour. 

def inter_stimulus_interval(event):
    if event == 'entry':
        print('#Trials: {}, Rewards: {}, Stim A:{}, Stim B: {}, PokeA_ISI: {}, PokeA_StimA:{}, PokeA_StimB: {}, PokeB_ISI: {}, PokeB_StimA: {}, PokeB_StimB: {}, RewardPoke_ISI: {}, RewardPoke_StimA: {}, RewardPoke_StimB:{}'.format(v.n_trials, v.n_rewards, v.n_stim_A, v.n_stim_B, v.n_pokesA_isi, v.n_pokesA_stimA, v.n_pokesA_stimB, v.n_pokesB_isi, v.n_pokesB_stimA, v.n_pokesB_stimB, v.n_rewardpokes_isi, v.n_rewardpokes_stimA, v.n_rewardpokes_stimB))
        if v.n_trials < v.max_trials:  # for all but the last trial
            timed_goto_state('inter_stimulus_interval_baseline', (randint(v.isi[0], (v.isi[1])*second) - v.stimulus_duration))  #go to ISI baseline period after the ISI duration-stim duration
        elif v.n_trials == v.max_trials:
            timed_goto_state('end_session', 2*second)
        

# ISI baseline period is the period just before CS onset which lasts the same duration as CS-on, used to determine baseline poking behavior 
def inter_stimulus_interval_baseline(event):
    if event == 'entry':
        if v.stimulus_sampler.next() == 'A':  # go to next stimulus listed in variable v.stimulus_sampler, this is where stimulus randomisation comes from
            timed_goto_state('stimulus_A', v.stimulus_duration)
        else: 
            timed_goto_state('stimulus_B', v.stimulus_duration)
    #count pokes in all ports during ISI baseline period to use as baseline
    elif event == 'poke_7':
        v.n_pokesA_isi += 1
    elif event == 'poke_8':
        v.n_pokesB_isi += 1
    elif event == 'poke_9':
        v.n_rewardpokes_isi +=1

def stimulus_A(event):
    if event == 'entry':
        v.n_trials += 1 #update trial counter
        v.n_stim_A += 1 #update appropriate stimulus counter
        timed_goto_state('reward', v.stimulus_duration)
        hw.poke_7.LED.on()
    elif event == 'exit':
        hw.poke_7.LED.off()
    #count pokes in all ports during stimulus A on period
    elif event == 'poke_7':
        v.n_pokesA_stimA += 1
    elif event == 'poke_8':
        v.n_pokesB_stimA += 1
    elif event == 'poke_9':
        v.n_rewardpokes_stimA += 1


def stimulus_B(event):
    if event == 'entry':
        v.n_trials += 1  #update trial counter
        v.n_stim_B += 1  #update appropriate stimulus counter
        timed_goto_state('no_reward', v.stimulus_duration)
        hw.poke_8.LED.on()
    elif event == 'exit':
        hw.poke_8.LED.off()
    #count pokes in all ports during stimulus B on period
    elif event == 'poke_7':
        v.n_pokesA_stimB += 1
    elif event == 'poke_8':
        v.n_pokesB_stimB += 1
    elif event == 'poke_9':
        v.n_rewardpokes_stimB += 1

def reward(event):
    if event == 'entry':
        v.n_rewards += 1  #update reward counter
        timed_goto_state('inter_stimulus_interval', v.reward_duration)  #after reward delivery return to ISI state
        hw.poke_9.SOL.on()  #reward delivery, solenoid on for as long as v.reward duration specifies
    elif event == 'exit':
        hw.poke_9.SOL.off()    

def no_reward(event):
    if event == 'entry':
        timed_goto_state('inter_stimulus_interval', v.reward_duration)  #no reward delivery, but wait the same amount of time as if it were delivered before entering ISI state

def end_session(event):
    if event == 'entry':
        stop_framework()
