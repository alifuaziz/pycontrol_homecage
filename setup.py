import atexit
import os
from setuptools import setup
import sys
import subprocess


def setup_folders() -> None:
    path = os.path.join(os.path.split(__file__)[0], r"src\pycontrol_homecage\utils")
    print(path)
    sys.path.append(path)

    from setup_utils import get_paths, create_paths_and_empty_csvs, create_user_file, get_root_path

    if not os.path.isdir(get_root_path()):
        os.mkdir(get_root_path())
    all_paths = get_paths()
    print(all_paths)
    create_paths_and_empty_csvs(all_paths)
    create_user_file()


if __name__ == "__main__":
    # setup()
    setup_folders()
