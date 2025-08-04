# pyControl Homecage Software

Important differences:

- Upgraded pyControl v2.0.2
- Access Control Board interface uses `Pycboard` instead of `Pyboard` and resuses appropriate functions
- Access Control drivers include drift corrector as extra class.
- Upgrade to PyQt6
- Setup is slightly different.
- RFID driver software for the RWD_QT is also present (funtional with appropriate RFID tags)
- Installation process simplified. Data folder is not created automatically. It requires the user to run `source/pycontrol_homecage/utils/setup_utils.py` to create data files
- Refactor of the code base to be more similar to pyControl directory structure.

## Setup

Installation different to orginial:

1. You need to create the data folder by running the `source/pycontrol_homecage/utils/setup_utils.py` script. This will create the data folder structure that allows the GUI to start up.
   - The GUI requires that there is a properly initialised data folder where it can store the information about the setups and mice.
2. You need to install the dependancies for the of the GUI
   - Using `pip install -r requirements.txt`
3. Run `pyControlHomecage.pyw` to startup
