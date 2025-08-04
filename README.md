# pyControl Homecage Software

Important differences:

- RFID driver software for the RWD_QT id is present
- Upgraded pyControl v2.0.2
  - Access Control Board interface uses `Pycboard`
- Upgrade to PyQt6
- Setup is slightly different.

## Setup Notes

Since i have change the repo a decent amount and simplified the code, the installation process is slighlty different to the original repo.

1. You need to create the data folder by running the `src/pycontrol_homecage/utils/setup_utils.py` script. This will create the structure that allows the GUI to start up.
   - The GUI requires that there is a properly initialised data folder where it can store the information about the setups and mice
2. You need to install the dependancies for the of the GUI
   - Using `pip install -r requirements.txt` (At the moment an editable version of the lib is installed in the env you are )
