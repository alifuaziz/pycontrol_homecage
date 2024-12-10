from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import pycontrol_homecage.db as database



""" This modules provides classes to pass messages from data processors to
    the recipient log windows which then print them
"""


class MessageRecipient(Enum):
    system_overview = 1
    calibrate_dialog = 2
    configure_box_dialog = 3
    direct_pyboard_dialog = 4


class MessageSource(Enum):
    ACBoard = 1
    PYCBoard = 2
    GUI = 3


@dataclass
class PrintMessage:

    text: str
    time: datetime
    time_str: str = field(init=False)
    recipient: MessageRecipient
    source : MessageSource

    def __post_init__(self):
        '''Funtion that runns immediately after the init of the PrintMessage constructer. In this case it fills in the
        appropriate attribute. '''
        self.time_str = str(self.time)


def emit_print_message(print_text: str, target: MessageRecipient, data_source: MessageSource) -> None:

    msg = PrintMessage(text=print_text,
                        time=datetime.now(),
                        recipient=target,
                        source=data_source
                        )
    database.message_queue.append(msg)