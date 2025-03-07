import os, json

# Get ROOT  from the config file
config_path = os.path.join(os.path.dirname(__file__), "config.json")
config = json.load(open(config_path, "r"))
ROOT = os.path.abspath(config["ROOT"])

# pycontrol_homecage path 
package_path = os.path.split(__file__)[0]

paths = {
    "ROOT": ROOT,
    # Data paths
    "user_path": os.path.join(ROOT, "users.txt"),
    "task_dir": os.path.join(ROOT, "tasks"),
    "experiment_dir": os.path.join(ROOT, "experiments"),
    "setup_dir": os.path.join(ROOT, "setups"),
    "mice_dir": os.path.join(ROOT, "mice"),
    "data_dir": os.path.join(ROOT, "data"),
    "AC_logger_dir": os.path.join(ROOT, "loggers"),
    "protocol_dir": os.path.join(ROOT, "prot"),
    # Package paths
    "framework_dir": os.path.join(package_path, "pyControl"),
    "devices_dir": os.path.join(package_path, "devices"),
    "config_dir": os.path.join(package_path, "pyControl_config"),
    "access_control_dir": os.path.join(package_path, "access_control_upy"),
}