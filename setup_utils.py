from typing import List
import os
import json
import pandas as pd


def get_config() -> dict:
    config_path = os.path.join(os.path.split(__file__)[0], "configs", "config.json")
    config = json.load(open(config_path, "r"))
    return config


DATA_DIR = get_config()["DATA_DIR"]


def get_path(path_type) -> str:

    path_list = ["data", "tasks", "setups", "loggers", "experiments", "mice", "prot", "users.txt"]
    assert path_type in path_list, "PATH must be one of {}".format(path_list)
    return os.path.join(DATA_DIR, path_type)


def get_paths() -> List[str]:

    path_list = ["data", "tasks", "setups", "loggers", "experiments", "mice", "prot"]
    return list(map(get_path, path_list))


def create_user_file() -> None:
    """Create the root file with system email information"""

    user_path = os.path.join(DATA_DIR, "users.txt")
    if not os.path.isfile(user_path):
        config = get_config()
        with open(user_path, "w") as f:
            f.write('system_email: "{}"'.format(config["System_email"]))
            f.write('password: "{}"'.format(config["System_password"]))


def create_paths_and_empty_csvs(all_paths) -> None:

    # This is thee data directory, doesn't have an empty csv in it
    if not os.path.isdir(all_paths[0]):
        os.mkdir(all_paths[0])

    for pth in all_paths[1:]:
        if not os.path.isdir(pth):
            os.mkdir(pth)
        create_empty_csv(pth)


# Experiment defines the overall experiment that is being run with these mice
# Protocol defines the current protocol, within a given experiment that is beign use
# User defines what user is currently using this setup
def create_empty_csv(pth: str) -> None:
    """Should probably use an enum here"""

    fp = None
    # set variables for tasks, what to store about them
    if "task" in pth:
        df = pd.DataFrame(columns=["Name", "User_added"])
        fp = os.path.join(pth, "tasks.csv")

    # set variables for experiments what to store about them
    elif "experiment" in pth:
        df = pd.DataFrame(
            columns=["Name", "Setups", "Subjects", "n_subjects", "User", "Protocol", "Active", "Persistent_variables"]
        )
        fp = os.path.join(pth, "experiments.csv")

    # set variables for setups what to store about them
    elif "setup" in pth:
        df = pd.DataFrame(
            columns=[
                "Setup_ID",
                "COM",
                "COM_AC",
                "in_use",
                "connected",
                "User",
                "Experiment",
                "Protocol",
                "Mouse_training",
                "AC_state",
                "Door_Mag",
                "Door_Sensor",
                "n_mice",
                "mice_in_setup",
                "logger_path",
            ]
        )
        fp = os.path.join(pth, "setups.csv")

    # set variables for mice what to store about them
    elif "mice" in pth:
        df = pd.DataFrame(
            columns=[
                "Mouse_ID",
                "RFID",
                "Sex",
                "Age",
                "Experiment",
                "Protocol",
                "Stage",
                "Task",
                "User",
                "Start_date",
                "Current_weight",
                "Start_weight",
                "is_training",
                "is_assigned",
                "training_log",
                "Setup_ID",
                "in_system",
                "summary_variables",
                "persistent_variables",
                "set_variables",
            ]
        )
        fp = os.path.join(pth, "mice.csv")

    if (fp is not None) and (not os.path.isfile(fp)):
        df.to_csv(fp, index=False)


if __name__ == "__main__":

    if not os.path.isdir(DATA_DIR):
        os.mkdir(DATA_DIR)
    create_paths_and_empty_csvs(get_paths())
    create_user_file()
