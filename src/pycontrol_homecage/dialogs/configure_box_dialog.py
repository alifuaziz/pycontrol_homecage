import os
from pyqtgraph.Qt import QtGui

import pycontrol_homecage.db as database
from pycontrol_homecage.com.messages import MessageRecipient

class ConfigureBoxDialog(QtGui.QDialog):
    """Dialog window that allows you to upload harware definitions etc """ 

    def __init__(self, setup_id, parent=None):
        super(ConfigureBoxDialog, self).__init__(parent)
        self.setGeometry(10, 30, 500, 200) # Left, top, width, height.
        self.setup_id = setup_id
        layoutH = QtGui.QHBoxLayout(self)


        self.load_framework_button = QtGui.QPushButton('Load Pycontrol \nframework', self)
        self.load_framework_button.clicked.connect(self.load_framework)


        self.load_ac_framework_button = QtGui.QPushButton('Load Access control \nframework', self)
        self.load_ac_framework_button.clicked.connect(self.load_ac_framework)

        self.load_hardware_definition_button = QtGui.QPushButton('Load hardware definition',self)
        self.load_hardware_definition_button.clicked.connect(self.load_hardware_definition)

        self.disable_flashdrive_button = QtGui.QPushButton('Disable flashdrive')
        self.disable_flashdrive_button.clicked.connect(self.disable_flashdrive)
        layout2 = QtGui.QVBoxLayout(self)
        layout2.addWidget(self.load_framework_button)
        layout2.addWidget(self.load_hardware_definition_button)
        layout2.addWidget(self.disable_flashdrive_button)
        layout2.addWidget(self.load_ac_framework_button)


        self.ac = database.controllers[self.setup_id].AC
        self.reject = self._done


        #self.setGeometry(10, 30, 400, 200) # Left, top, width, height.

        self.buttonDone = QtGui.QPushButton('Done')
        self.buttonDone.clicked.connect(self._done)

        self.buttonTare = QtGui.QPushButton('Tare', self)
        self.buttonTare.clicked.connect(self.tare)

        self.buttonWeigh = QtGui.QPushButton('Weigh', self)
        self.buttonWeigh.clicked.connect(self.weigh)

        self.calibration_weight = QtGui.QLineEdit("")
        self.buttonCal = QtGui.QPushButton('callibrate', self)
        self.buttonCal.clicked.connect(self.callibrate)

        self.log_textbox = QtGui.QTextEdit()
        self.log_textbox.setFont(QtGui.QFont('Courier', 9))
        self.log_textbox.setReadOnly(True)

        layout = QtGui.QVBoxLayout()

        layout.addWidget(self.buttonWeigh)
        layout.addWidget(self.buttonTare)
        layout.addWidget(self.calibration_weight)
        layout.addWidget(self.buttonCal)
        layout.addWidget(self.buttonDone)

        layoutH.addLayout(layout2)
        layoutH.addLayout(layout)
        layoutH.addWidget(self.log_textbox)
        database.print_consumers[MessageRecipient.configure_box_dialog] = self.print_msg

    def _set_layout(self) -> None:
        layout = QtGui.QVBoxLayout()

        layout.addWidget(self.buttonWeigh)
        layout.addWidget(self.buttonTare)
        layout.addWidget(self.calibration_weight)
        layout.addWidget(self.buttonCal)
        layout.addWidget(self.buttonDone)

        layoutH.addLayout(layout2)
        layoutH.addLayout(layout)
        layoutH.addWidget(self.log_textbox)

    def load_ac_framework(self):

        self.log_textbox.insertPlainText('Loading access control framework...')
        database.controllers[self.setup_id].AC.reset()
        database.controllers[self.setup_id].AC.load_framework()
        self.log_textbox.insertPlainText('done!')

    def load_framework(self):
        self.log_textbox.insertPlainText('Loading framework...')
        database.controllers[self.setup_id].PYC.load_framework()
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.log_textbox.insertPlainText('done!')
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)

    def disable_flashdrive(self):
        database.controllers[self.setup_id].PYC.disable_flashdrive()

    def load_hardware_definition(self):
        hwd_path = QtGui.QFileDialog.getOpenFileName(self, 'Select hardware definition:',
                os.path.join(database.paths["config_dir"], 'hardware_definition.py'), filter='*.py')[0]


        self.log_textbox.insertPlainText('uploading hardware definition...')
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)

        database.controllers[self.setup_id].PYC.load_hardware_definition(hwd_path)
        self.log_textbox.insertPlainText('done!')
        #setup.load_hardware_definition(hwd_path)


    def tare(self):
        self.ac.serial.write(b'tare')

    def callibrate(self):
        cw = self.calibration_weight.text()
        str_ = 'calibrate:'+cw
        self.ac.serial.write(str_.encode())

        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.log_textbox.insertPlainText('Target calibration weight: ' + str(cw) +'g\n')
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)

    def weigh(self):
        self.ac.serial.write(b'weigh')

    def _done(self):
        del database.print_consumers[MessageRecipient.configure_box_dialog]
        self.accept()

    def print_msg(self, msg: str):
        "print weighing messages"
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)

        if 'calT' in msg:
            self.log_textbox.insertPlainText('Weight after Tare: ' + msg.replace('calT:','')+'g\n')
        elif 'calW' in msg:
            self.log_textbox.insertPlainText('Weight: ' + msg.replace('calW:','')+'g\n')
        if 'calC' in msg:
            self.log_textbox.insertPlainText('Measured post-calibration weight: ' + msg.replace('calC:','')+'g\n')
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)