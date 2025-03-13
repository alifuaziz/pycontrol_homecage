import os
import json

config_path = os.path.join(os.path.split(os.path.dirname(__file__))[0], "config.json")
print(os.path.isfile(config_path))
print(config_path)
config = json.load(open(config_path, 'r'))

ROOT = os.path.abspath(config["ROOT"])
if not os.path.isdir(ROOT):
    os.mkdir(ROOT)

data_dir = os.path.join(ROOT, 'data')
task_dir = os.path.join(ROOT, 'tasks')
setup_dir = os.path.join(ROOT, 'setups')
AC_logger_dir = os.path.join(ROOT, 'loggers')
experiment_dir = os.path.join(ROOT, 'experiments')
mice_dir = os.path.join(ROOT, 'mice')
protocol_dir = os.path.join(ROOT, 'prot')


user_path = os.path.join(ROOT, "users.txt")
print(user_path)
if not os.path.isfile(user_path):
    with open(user_path, 'w') as f:
        f.write('system_email: "{}"'.format(config["System_email"]))
        f.write('password: "{}"'.format(config["System_password"]))

main_path = os.path.dirname(os.path.abspath(__file__))


all_paths = [ROOT, task_dir, experiment_dir, setup_dir, mice_dir, data_dir, AC_logger_dir, protocol_dir]


