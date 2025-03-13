import os, json

# Get ROOT  from the config file
config_path = os.path.join(os.path.dirname(__file__), "configs", "config.json")
config = json.load(open(config_path, "r"))
ROOT = os.path.abspath(config["ROOT"])
print("ROOT:", ROOT)
# pycontrol_homecage path
package_path = os.path.split(__file__)[0]

paths = {
    "ROOT": ROOT,
    # Data paths
    "user_path": os.path.join(ROOT, "users.txt"),
    "task_dir": os.path.join(ROOT, "tasks"),  # Task Directory
    "task_dir_dataframe_filepath": os.path.join(ROOT, "tasks", "tasks.csv"),  # Tasks df filepath
    "experiment_dir": os.path.join(ROOT, "experiments"),  # Experiment direcotry
    "experiment_dataframe_filepath": os.path.join(ROOT, "experiments", "experiments.csv"),  # Experiment df filepath
    "setup_dir": os.path.join(ROOT, "setups"),  # Setups directory
    "setup_dir_dataframe_filepath": os.path.join(ROOT, "setups", "setups.csv"),  # Setups df filepath
    "mice_dir": os.path.join(ROOT, "mice"),  # Mice directory
    "mice_dataframe_filepath": os.path.join(ROOT, "mice", "mice.csv"),  # Mice df filepath
    "data_dir": os.path.join(ROOT, "data"),
    "AC_logger_dir": os.path.join(ROOT, "loggers"),
    "protocol_dir": os.path.join(ROOT, "prot"),
    # Package paths
    "framework_dir": os.path.join(package_path, "pyControl"),
    "devices_dir": os.path.join(package_path, "devices"),
    "config_dir": os.path.join(package_path, "pyControl_config"),
    "access_control_dir": os.path.join(package_path, "access_control_upy"),
}
