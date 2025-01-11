# Intergration testing plan

- Write a script for the micropython boards that is able to emit the data that the machine must be able to handle. 
- Should be able to see the logs that do exist and that they reflect the test. 



## States
- `allow_entry`
  - `door0_open:  + pin read value`
- `wait_close`
- `check_mouse`
  - `temp_w:`
  - weight:
  - `weight`
- `entry_training_chamber`
- `check_mouse_in_training`
- `mouse_training`
  - Is handled by: checking if the self.data_file is None. If so: 
    - (in `self._handle_mouse_training`), 
      - From the mouse
- `check_mouse_in_ac`
  - YW: "When the mouse starts to leave"
- `allow_exit`
  - `temp_w_out`
- `entry_state`
- `check_exit`
- `error_state`
  - Is handled by stopping the pycontrol framework. 
- sent states - for the load cell
- `calW` (weigh)
- `CalC` (calibrate)
- `CalT` (tare)
## Messages

*That aren't states that are sent (so i should probably be able to simulate them*


## Goals 

### Software
Get signals to come out of the access control board.  (done)
Write those signals to a log file (done)
Write those signals to the correct part of the tables in the software. (inprogress)

### Hardware
Check the logic for the hardware is working i.e. The correct signals come out of the access control at the right times. 
- Getting the correct weight readings
- Order new load cell. 
- Order new screw hinge
- Getting the correct RFID readings 
- Get the RFID coil ordered. 
- checking the magents magnetise and demagnitise correctly
  



## No module named hardware definition. 
This means that the required modules haven't been uploade to the board. To do this, you need to make sure that when you upload your framework, you are also uploading the pycontrol hardware definition dependancy files to the machine as well. 
For some reason the hardware definition is not imported with to the pyboard with the statemachine file as well... therefore for testing i am going to upload it with the state signal generator

You need a pycontrol task for the access control pycontrol board to start working. (this is an extra requirement that might not be required? idk.)

