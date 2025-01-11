import numpy as np
from pyqtgraph import Qt
from pyqtgraph.Qt import QtCore, QtGui


class MouseListTable(QtGui.QTableWidget):
    """This table contains information about all mice currently running in the
    system"""

    def __init__(self, tab, parent=None):
        super(QtGui.QTableWidget, self).__init__(1, 17, parent=parent)
        self.header_names = [
            "",
            "Mouse_ID",
            "RFID",
            "Sex",
            "Age",
            "Experiment",
            "Protocol",
            "Stage",
            "Task",
            "User",
            "Start_date",
            "Current_weight",
            "Start_weight",
            "is_training",
            "is_assigned",
            "training_log",
            "Setup_ID",
        ]

        self.tab = tab
        self.setHorizontalHeaderLabels(self.header_names)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)
        self.fill_table()

    def fill_table(self):
        self.clear()
        self.setHorizontalHeaderLabels(self.header_names)
        df = self.tab.df_mouse_tmp.loc[
            self.tab.df_mouse_tmp["Setup_ID"].isin(self.tab.CLT.selected_setups)
        ]
        df.index = np.arange(len(df))

        df.reset_index(drop=True)
        self.setRowCount(len(df))

        for row_index, row in df.iterrows():
            for col_index in range(self.columnCount() - 1):
                self.setItem(
                    row_index,
                    col_index + 1,
                    Qt.QtWidgets.QTableWidgetItem(str(row[col_index])),
                )

            chkBoxItem = QtGui.QTableWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)
            self.setItem(row_index, 0, chkBoxItem)
