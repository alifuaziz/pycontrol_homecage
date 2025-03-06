# Base python imports
import sys
import logging
import os
from functools import partial
import ctypes

# Check dependencies
import importlib.util

if os.name == "nt":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("pyControlHomecage")


# Set up logging
logging.basicConfig(
    level=logging.ERROR,
    handlers=[
        logging.FileHandler("ErrorLog.txt", delay=True),
    ],
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# Dependency Mangement
def check_module(module_name):
    if importlib.util.find_spec(module_name) is None:
        logging.error(f"Unable to import dependency: {module_name}")
        sys.exit()


# Depedencies for application
check_module("PyQt5")
check_module("pyqtgraph")
check_module("serial")
check_module("pandas")

from PyQt5.QtWidgets import QApplication
from pycontrol_homecage.gui_tabs.MainGUI import MainGUI
from pycontrol_homecage.utils import get_path
from pycontrol_homecage.utils import custom_excepthook


def initialise_excepthook() -> None:
    """Initialise a custom excepthook that prints errors to a log
    in addition to shutting down the program"""
    setup_dir = get_path("setups")
    sys._excepthook = sys.excepthook

    exception_path = os.path.join(setup_dir, "exception_store.txt")
    except_hook = partial(custom_excepthook, filepath=exception_path)
    sys.excepthook = except_hook


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    gui = MainGUI()
    gui.app = app  # To allow app functions to be called from GUI.
    return app


if __name__ == "__main__":
    initialise_excepthook()

    app = main()
    sys.exit(app.exec_())
