# from https://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
import sys
import os
from typing import Tuple
import pandas as pd


from paths import paths


def load_data_csv():

    fp = os.path.join(paths["task_dir"], "tasks.csv")
    task_df = pd.read_csv(fp)
    # task_df.file_location = fp

    fp = os.path.join(paths["experiment_dir"], "experiments.csv")
    exp_df = pd.read_csv(fp)
    # exp_df.file_location = fp

    fp = os.path.join(paths["setup_dir"], "setups.csv")
    setup_df = pd.read_csv(fp)
    # setup_df.file_location = fp

    fp = os.path.join(paths["mice_dir"], "mice.csv")
    mouse_df = pd.read_csv(fp)
    # mouse_df.file_location = fp

    for col in mouse_df.columns:
        if "Unnamed" in col:
            mouse_df.drop(col, inplace=True, axis=1)

    return task_df, exp_df, setup_df, mouse_df


# this is a pointer to the module object instance itself.
this = sys.modules[__name__]

# we can explicitly make assignments on it
this.controllers = {}
this.connected_access_controls = {}
this.connected_pycontrol_boards = {}
this.updated = False
this.update_table_queue = []
this.message_queue = []

# These are print consumers that ensure that things are printer to the correct place
this.print_consumers = {}

print("Running load_data_csv()")
this.task_df, this.exp_df, this.setup_df, this.mouse_df = load_data_csv()
