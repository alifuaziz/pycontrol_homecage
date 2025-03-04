# from https://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
import sys
import os
import json
from typing import Tuple

import pandas as pd



def load_data_csv() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    
    fp = os.path.join(this.paths["task_dir"], 'tasks.csv')
    task_df = pd.read_csv(fp)
    task_df.file_location = fp

    fp = os.path.join(this.paths["experiment_dir"], 'experiments.csv')
    exp_df = pd.read_csv(fp)
    exp_df.file_location = fp

    fp = os.path.join(this.paths["setup_dir"], 'setups.csv')
    setup_df = pd.read_csv(fp)
    setup_df.file_location = fp

    fp = os.path.join(this.paths["mice_dir"], 'mice.csv')
    mouse_df = pd.read_csv(fp)
    mouse_df.file_location = fp

    for col in mouse_df.columns:
        if 'Unnamed' in col:
            mouse_df.drop(col, inplace=True, axis=1)

    return task_df, exp_df, setup_df, mouse_df



# this is a pointer to the module object instance itself.
this = sys.modules[__name__]


config_path = os.path.join(os.path.dirname(__file__), "config.json")
print(os.path.isfile(config_path))
print(config_path)
config = json.load(open(config_path, 'r'))

ROOT = os.path.abspath(config["ROOT"])


# we can explicitly make assignments on it
this.controllers = {}
this.connected_access_controls = {}
this.connected_pycontrol_boards = {}
this.updated = False
this.update_table_queue = []
this.message_queue = []

# These are print consumers that ensure that things are printer to the correct place
this.print_consumers = {}



package_path = os.path.split(__file__)[0]
this.paths = {'ROOT': ROOT,
              'user_path': os.path.join(ROOT,"users.txt"),
              'task_dir': os.path.join(ROOT, 'tasks'),
              'experiment_dir': os.path.join(ROOT, 'experiments'),
              'setup_dir': os.path.join(ROOT, 'setups'),
              'mice_dir': os.path.join(ROOT, 'mice'),
              'data_dir': os.path.join(ROOT, 'data'),
              'AC_logger_dir': os.path.join(ROOT, 'loggers'),
              'protocol_dir': os.path.join(ROOT, 'prot'),

              'framework_dir': os.path.join(package_path, "pyControl"),
              "devices_dir": os.path.join(package_path, "devices"),
              "config_dir": os.path.join(package_path, "pyControl_config"),
              "access_control_dir": os.path.join(package_path, 'access_control_upy')
              }


this.task_df, this.exp_df, this.setup_df, this.mouse_df = load_data_csv()


# This is clearly not implemented yet
# class pycontrol_homecage_database:

#     def __init__(self) -> None:
#         self.has_been_updated = True

#     def update_table_row(self, table_name: str, column_name: str, new_value: object, row_identifier: object, row_id_value: object) -> None:
#         pass

#     def add_table_row(self, table: str, row) -> None:
#         pass

#     def add_table_rows(self) -> None:
#         pass

#     def write_tables_to_file(self) -> None:
#         pass

#     def add_controller(self) -> None:
#         pass

#     def add_access_control_board(self) -> None:
#         pass

#     def add_pycontrol_board(self) -> None:
#         pass

