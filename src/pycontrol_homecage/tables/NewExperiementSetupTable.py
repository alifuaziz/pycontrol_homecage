import os
from PyQt5 import QtCore, QtWidgets

from pycontrol_homecage.com.pyboard import _djb2_file
from pycontrol_homecage.utils import get_tasks
# import pycontrol_homecage.db as database


class NewExperimentSetupTable(QtWidgets.QTableWidget):
    """Table Widget that is used in the `Start New Experiement` dialog. It is used for displaying the setups
    There are three tables in this dialog. The other two are defined in the `new_experiment_dialog` class."""

    def __init__(self, GUI, tab, parent=None):
        super(QtWidgets.QTableWidget, self).__init__(1, 12, parent=parent)
        self.header_names = ['Show mice', 'Shared Protocol', 'Protocol',
                             'COM', 'COM_AC', 'Setup_ID',
                             'in_use', 'connected', 'User', 'Experiment',
                             'Protocol', 'Mouse_training', 'Door', 'n_mice']

        self.GUI = GUI
        self.tab = tab

        self.share_task_in_setup = []

        self.setHorizontalHeaderLabels(self.header_names)
        self.verticalHeader().setVisible(False)

        self.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.cellChanged.connect(self.show_mice_in_setup)

        self.selected_setups = []

    def run_task(self) -> None:
        ""
        setup, task = self.sender().name

        board_ix = [i for i, brd in enumerate(self.GUI.connected_boards) if brd.serial_port == setup]

        self.task_hash = _djb2_file(os.path.join(self.GUI.GUI_filepath, 'tasks', task + '.py'))
        self.GUI.connected_boards[int(board_ix[0])].setup_state_machine(task, uploaded=False)
        self.GUI.connected_boards[int(board_ix[0])].start_framework()

    def fill_table(self) -> None:

        self.clear()
        self.setHorizontalHeaderLabels(self.header_names)
        self.setRowCount(len(self.tab.df_setup_tmp))

        for row_index, row in self.tab.df_setup_tmp.iterrows():
            self.share_task_in_setup.append(False)

            for col_index in range(self.columnCount()-3):

                self.setItem(row_index, col_index+3, QtWidgets.QTableWidgetItem(str(row[col_index])))

            # These should be set just as one for each column
            chkBoxItem = QtWidgets.QTableWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)
            self.setItem(row_index, 0, chkBoxItem)

            chkBoxItem = QtWidgets.QTableWidgetItem()
            if self.tab.global_task:

                chkBoxItem.setFlags(QtCore.Qt.ItemIsEnabled)
            else:
                chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                chkBoxItem.setCheckState(QtCore.Qt.Unchecked)

            self.setItem(row_index, 1, chkBoxItem)

            protocols = QtWidgets.QComboBox()

            self.available_tasks = get_tasks()
            protocols.addItems(['Select Task'] + self.available_tasks)
            protocols.setEnabled(False)
            # QtWidgets.QTableWidgetItem()
            if self.tab.global_task:
                protocols.setEnabled(False)
                protocols.clear()
                protocols.addItems([self.tab.protocol_combo.currentText()])

                self.tab.mouse_prot.clear()
                self.tab.mouse_prot.addItems([self.tab.protocol_combo.currentText()])

            self.setCellWidget(row_index, 2, protocols)

        self.selected_setups = []

    def show_mice_in_setup(self, row, col):

        item = self.item(row, col)

        if col == 1:
            if item.checkState() == 2:
                if self.cellWidget(row, 2) is not None:
                    self.cellWidget(row, 2).setEnabled(True)
                    self.share_task_in_setup[row] = True
                    self.tab.mouse_prot.setEnabled(False)
                    self.tab.mouse_prot.clear()
                    self.tab.mouse_prot.addItems([self.cellWidget(row, 2).currentText()])
            elif item.checkState() == 0:
                if self.cellWidget(row, 2) is not None:
                    self.cellWidget(row, 2).setEnabled(False)
                    self.share_task_in_setup[row] = False
                    self.tab.mouse_prot.clear()
                    self.tab.mouse_prot.addItems(['Select Task'] + self.tab.available_tasks)
                    self.tab.mouse_prot.setEnabled(True)
        else:

            if col == 0:
                if item.checkState() == 2:
                    self.selected_setups.append(self.item(row, 5).text())
                    if self.share_task_in_setup[row]:
                        self.tab.mouse_prot.setEnabled(False)
                        self.tab.mouse_prot.clear()
                        self.tab.mouse_prot.addItems([self.cellWidget(row, 2).currentText()])

                if item.checkState() == 0:
                    self.selected_setups = [i for i in self.selected_setups if i != self.item(row, 5).text()]

            if len(self.selected_setups) > 0:
                self.tab.MICE.setEnabled(True)
                self.tab.add_mouse_button.setEnabled(True)

            else:
                self.tab.MICE.setEnabled(False)

            if len(self.selected_setups) > 1:

                self.tab.add_mouse_button.setEnabled(False)

        self.tab.mouse_list_table.fill_table()
