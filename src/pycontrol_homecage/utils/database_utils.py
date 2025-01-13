import os
from typing import List
from pycontrol_homecage.utils import get_path
# import pycontrol_homcage.db as database


def get_tasks() -> List[str]:
    """Function to read available tasks from the tasks folder
    Returns a list of the .py files that are in the `/data/tasks` folder"""

    tasks = [t.split(".")[0] for t in os.listdir(get_path("tasks")) if t[-3:] == ".py"]
    return tasks


def get_available_experiments() -> list[str]:
    """Function get the list of experiements that exist in the database"""
    return []


def get_available_setups() -> list[str]:
    """Return a list of the setups from the databse."""
    return []
