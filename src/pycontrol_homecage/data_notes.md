# File for describing the role of each datafolder in the `/data` folder for the access control 
## `/mice`
- Contains a csv which is the list of mice in the setup (mice.csv) 
- For each mouse in the setup a history of their life in the box 
Thus, there are N + 1 files in this folder
## `/loggers`
- Contains `.txt` files for each setup (atm) This is the history of all the signals that are coming out of each setup. 
- Each new line it the output of the serial command that is coming from the  pyboard (for the access control board. )
## `/tasks` 
- Contains the folder of tasks that are available for each mouse. The Each mouse can be allocated a different task to do themselves (i wonder what the behaviour for this would look like)
## `/setups`
- Table summarsing the state of each setup currently in existance. 
## `/experiments`
- I am unsure why it exists. This is the most high level summary of the computer the access control hardware is running on 
## `/prot`
- ???
## `/data`
- A directory containing .txt files that tell you what the output of a pycontrol. May be the experimental results. 
- The details of this work are in the link: https://pycontrol.readthedocs.io/en/latest/user-guide/pycontrol-data/#old-data-format