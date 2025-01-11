import re
import os
from typing import List
from serial.tools import list_ports
from pycontrol_homecage.utils import get_path

def get_tasks() -> List[str]:
    """Function to read available tasks from the tasks folder 
    Returns a list of the .py files that are in the `/data/tasks` folder"""

    tasks = [t.split('.')[0] for t in os.listdir(get_path("tasks")) if t[-3:] == '.py']
    return tasks


def get_variables_from_taskfile(pth: str) -> List[str]:
    "Helper function to scan python script and return variables in that script"
    with open(pth, 'r') as f:
        txt = f.read()

    variables = re.findall(r'(v\.[^\s ]*) {0,2}=', txt)
    variables = list(set(variables))
    return variables


def get_variables_and_values_from_taskfile(pth: str) -> dict[str, str]:
    "Helper function to scan python script and return variables in that script"
    with open(pth, 'r') as f:
        txt = f.readlines()

    var_dict = {}
    for line in txt:
        if ('v.' in line) and ('=' in line):
            var_ = re.findall(r'(v\.[^\s]*)', line)[0].strip()
            val_ = re.findall(r'v\..*=(.*)[#|\n]', line)[0]
            var_dict[var_] = val_
        if 'run_start' in line:
            break

    return var_dict


def find_setups():
    """Looks for pyboards in the list of comports on the computer"""
    ports = list(set([c[0] for c in list_ports.comports() if ('Pyboard' in c[1]) or ('USB Serial Device' in c[1])]))
    return ports
