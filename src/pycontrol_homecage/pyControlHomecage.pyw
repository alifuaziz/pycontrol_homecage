import sys
import os
from functools import partial

from pyqtgraph.Qt import QtGui

from pycontrol_homecage.gui_tabs.main_gui import GUIApp
from pycontrol_homecage.utils import get_path
from pycontrol_homecage.utils import custom_excepthook


def initialise_excepthook() -> None:
    """Initialise a custom excepthook that prints errors to a log
       in addition to shutting down the program
    """
    setup_dir= get_path("setups")
    sys._excepthook = sys.excepthook

    exception_path = os.path.join(setup_dir, 'exception_store.txt')
    except_hook = partial(custom_excepthook, filepath=exception_path)
    sys.excepthook = except_hook


def main() -> None:
    app = QtGui.QApplication(sys.argv)
    gui = GUIApp()
    gui.app = app   # To allow app functions to be called from GUI.
    return app


if __name__ == "__main__":

    initialise_excepthook()

    app = main()
    sys.exit(app.exec_())
