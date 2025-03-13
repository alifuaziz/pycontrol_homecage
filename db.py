# from https://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
import sys
import pandas as pd
from source.gui.settings import get_setting
from paths import paths


def load_data_csv():

    task_df = pd.read_csv(paths["task_dir_dataframe_filepath"])
    exp_df = pd.read_csv(paths["experiment_dataframe_filepath"])
    setup_df = pd.read_csv(paths["setup_dir_dataframe_filepath"])
    mouse_df = pd.read_csv(paths["mice_dataframe_filepath"])

    for col in mouse_df.columns:
        if "Unnamed" in col:
            mouse_df.drop(col, inplace=True, axis=1)

    return task_df, exp_df, setup_df, mouse_df


# this is a pointer to the module object instance itself.
this = sys.modules[__name__]

# we can explicitly make assignments on it
this.controllers = {}
this.update_table_queue = []
this.message_queue = []

# These are print consumers that ensure that things are printer to the correct place
this.print_consumers = {}

this.task_df, this.exp_df, this.setup_df, this.mouse_df = load_data_csv()
