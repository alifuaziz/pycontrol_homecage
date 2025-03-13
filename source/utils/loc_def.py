import os
import json

config_path = os.path.join(os.path.split(os.path.dirname(__file__))[0], "config.json")
print(os.path.isfile(config_path))
print(config_path)
config = json.load(open(config_path, 'r'))

DATA_DIR = os.path.abspath(config["DATA_DIR"])
if not os.path.isdir(DATA_DIR):
    os.mkdir(DATA_DIR)

data_dir = os.path.join(DATA_DIR, 'data')
task_dir = os.path.join(DATA_DIR, 'tasks')
setup_dir = os.path.join(DATA_DIR, 'setups')
AC_logger_dir = os.path.join(DATA_DIR, 'loggers')
experiment_dir = os.path.join(DATA_DIR, 'experiments')
mice_dir = os.path.join(DATA_DIR, 'mice')
protocol_dir = os.path.join(DATA_DIR, 'prot')


user_path = os.path.join(DATA_DIR, "users.txt")
print(user_path)
if not os.path.isfile(user_path):
    with open(user_path, 'w') as f:
        f.write('system_email: "{}"'.format(config["System_email"]))
        f.write('password: "{}"'.format(config["System_password"]))

main_path = os.path.dirname(os.path.abspath(__file__))


all_paths = [DATA_DIR, task_dir, experiment_dir, setup_dir, mice_dir, data_dir, AC_logger_dir, protocol_dir]


