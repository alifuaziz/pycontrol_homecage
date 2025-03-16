from dataclasses import dataclass
from typing import List
from PyQt5 import QtGui, QtCore, QtWidgets
from .animals_tab import AnimalSettingsConfig


@dataclass
class Homecage:
    setup_name: str
    animals: List[AnimalSettingsConfig]


class Homecage_montior(QtWidgets.QWidget):
    def __init__(self):
        self.setup = None
        self.animals = None


# Subjects that 