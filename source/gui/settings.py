import os
import json

VERSION = "0.0.0"

# Get DATA_DIR  from the config file
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "configs", "config.json")
config = json.load(open(config_path, "r"))
DATA_DIR = os.path.abspath(config["DATA_DIR"])
print("DATA_DIR:", DATA_DIR)
# pycontrol_homecage path
package_path = os.path.split(__file__)[0]


def get_setting(setting_type, setting_name, want_default=False):
    """
    gets a user setting from settings.json or, if that doesn't exist,
    the default_user_settings dictionary
    """

    default_user_settings = {
        "folders": {
            "api_classes": os.path.join(os.getcwd(), "api_classes"),
            "controls_dialogs": os.path.join(os.getcwd(), "controls_dialogs"),
            "devices": os.path.join(os.getcwd(), "devices"),
            "hardware_definitions": os.path.join(os.getcwd(), "hardware_definitions"),
            "data": os.path.join(os.getcwd(), "data"),
            "experiments": os.path.join(os.getcwd(), "experiments"),
            "tasks": os.path.join(os.getcwd(), "tasks"),
            "config":os.path.join(os.getcwd(), "configs"),
            ########################## PYCONTROL HOMECAGE FOLDERS ##########################
            "user_path": os.path.join(DATA_DIR, "users.txt"),
            "task_dir": os.path.join(DATA_DIR, "tasks"),  # Task Directory
            "task_dir_dataframe_filepath": os.path.join(DATA_DIR, "tasks", "tasks.csv"),  # Tasks df filepath
            "experiment_dir": os.path.join(DATA_DIR, "experiments"),  # Experiment direcotry
            "experiment_dataframe_filepath": os.path.join(
                DATA_DIR, "experiments", "experiments.csv"
            ),  # Experiment df filepath
            "setup_dir": os.path.join(DATA_DIR, "setups"),  # Setups directory
            "setup_dir_dataframe_filepath": os.path.join(DATA_DIR, "setups", "setups.csv"),  # Setups df filepath
            "mice_dir": os.path.join(DATA_DIR, "mice"),  # Mice directory
            "mice_dataframe_filepath": os.path.join(DATA_DIR, "mice", "mice.csv"),  # Mice df filepath
            "data_dir": os.path.join(DATA_DIR, "data"),
            "AC_logger_dir": os.path.join(DATA_DIR, "loggers"),
            "protocol_dir": os.path.join(DATA_DIR, "prot"),
            # Package paths
            # "framework_dir": os.path.join(package_path, "pyControl"),
            # "devices_dir": os.path.join(package_path, "devices"),
            "config_dir": os.path.join(package_path, "pyControl_config"),
            "access_control_dir": os.path.join(os.getcwd(), "source", "pyAccessControl"),
        },
        "plotting": {
            "update_interval": 10,
            "event_history_len": 200,
            "state_history_len": 100,
            "analog_history_dur": 12,
        },
        "GUI": {
            "ui_font_size": 11,
            "log_font_size": 9,
        },
    }

    json_path = os.path.join("config", "settings.json")
    if os.path.exists(json_path) and not want_default:  # user has a settings.json
        with open(json_path, "r", encoding="utf-8") as f:
            custom_settings = json.loads(f.read())
        if setting_name in custom_settings[setting_type]:
            return custom_settings[setting_type][setting_name]
        else:
            return default_user_settings[setting_type][setting_name]
    else:  # use defaults
        return default_user_settings[setting_type][setting_name]


def user_folder(folder_name):
    return get_setting("folders", folder_name)
