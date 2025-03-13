import os, json

# Get DATA_DIR  from the config file
config_path = os.path.join(os.path.dirname(__file__), "configs", "config.json")
config = json.load(open(config_path, "r"))
DATA_DIR = os.path.abspath(config["DATA_DIR"])
print("DATA_DIR:", DATA_DIR)
# pycontrol_homecage path
package_path = os.path.split(__file__)[0]

paths = {
    "DATA_DIR": DATA_DIR,
    # Data paths
    "user_path": os.path.join(DATA_DIR, "users.txt"),
    "task_dir": os.path.join(DATA_DIR, "tasks"),  # Task Directory
    "task_dir_dataframe_filepath": os.path.join(DATA_DIR, "tasks", "tasks.csv"),  # Tasks df filepath
    "experiment_dir": os.path.join(DATA_DIR, "experiments"),  # Experiment direcotry
    "experiment_dataframe_filepath": os.path.join(DATA_DIR, "experiments", "experiments.csv"),  # Experiment df filepath
    "setup_dir": os.path.join(DATA_DIR, "setups"),  # Setups directory
    "setup_dir_dataframe_filepath": os.path.join(DATA_DIR, "setups", "setups.csv"),  # Setups df filepath
    "mice_dir": os.path.join(DATA_DIR, "mice"),  # Mice directory
    "mice_dataframe_filepath": os.path.join(DATA_DIR, "mice", "mice.csv"),  # Mice df filepath
    "data_dir": os.path.join(DATA_DIR, "data"),
    "AC_logger_dir": os.path.join(DATA_DIR, "loggers"),
    "protocol_dir": os.path.join(DATA_DIR, "prot"),
    # Package paths
    "framework_dir": os.path.join(package_path, "pyControl"),
    "devices_dir": os.path.join(package_path, "devices"),
    "config_dir": os.path.join(package_path, "pyControl_config"),
    "access_control_dir": os.path.join(package_path, "access_control_framework"),
}
