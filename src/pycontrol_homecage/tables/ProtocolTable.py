from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
import pandas as pd
from functools import partial

# from ..gui_tabs import ProtocolAssemblyTab


class ProtocolTable(QTableWidget):
    def __init__(self, tab, nRows: int = None, parent=None):
        super(QTableWidget, self).__init__(1, 6, parent=parent)
        self.set_headers()
        self.tab = tab
        if nRows:
            self.setRowCount(nRows)
            self.nRows = nRows
        else:
            self.nRows = 1

        self.delete_row_idx = self.header_names.index("Delete")

    def set_headers(self):
        self.header_names = [
            "Stage",
            "Task",
            "Tracked",
            "Threshold(s)",
            "Default(s)",
            "Delete",
        ]
        self.setHorizontalHeaderLabels(self.header_names)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.set_resizemode_for_headers()

    def set_resizemode_for_headers(self):
        for h_ix in range(len(self.header_names) - 1):
            self.horizontalHeader().setSectionResizeMode(h_ix, QHeaderView.Stretch)

    def fill_table(self, protocol_df: pd.DataFrame):
        """Here pass prot_dict"""

        self.nRows = len(protocol_df.index)

        self.clear()
        self.setHorizontalHeaderLabels(self.header_names)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        for i in range(1, len(self.header_names) - 1):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

        if self.nRows:
            self.setRowCount(self.nRows)

        for idx, row in protocol_df.iterrows():
            self.fill_row(row.to_dict(), row=idx)

    def fill_row(self, stage_data: pd.Series, row: int = None):
        """From the pandas dataframe, display the information correctlty
        If row not defined in function call, the row = 0"""

        if not row:
            row = 0
            self.reset_()

        for key, value in stage_data.items():
            print("Fill row function")
            print(key, value)
            # 'Preprocess' the threshold and default values into strings for putting in the table
            # if ("thresh" in key) or ("default" in key):
            #     variableTemp = QTableWidgetItem(self._translate(value))
            # else:
            variableTemp = QTableWidgetItem(str(value))

            # Put the items in the table
            if key == "threshV":
                self.setItem(row, self.header_names.index("Threshold(s)"), variableTemp)
            elif key == "defaultV":
                self.setItem(row, self.header_names.index("Default(s)"), variableTemp)
            elif key == "trackV":
                self.setItem(row, self.header_names.index("Tracked"), variableTemp)
            # elif key == "stage_nr":
            #     self.setItem(row, self.header_names.index("Stage"), variableTemp)
            elif key == "task":
                self.setItem(row, self.header_names.index("Task"), variableTemp)

        # Build delete button
        self.setCellWidget(
            row,
            self.header_names.index("Delete"),
            self._build_delete_button(row_number=row),
        )

        self.resizeRowToContents(row)

    def _build_delete_button(self, row_number: pd.Series):
        """Build button to delete this row of the GUI."""
        button = QPushButton("Delete Stage")
        button.clicked.connect(partial(self.tab.remove_stage_from_protocol, row_number))
        return button

    def _translate(self, x):
        ret = ""
        if len(x):
            for x_ in x:
                ret = ret + str(x_[0]) + ": " + str(x_[1]) + "\n"
        return ret

    def reset_(self):
        self.clear()
        self.setHorizontalHeaderLabels(self.header_names)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

        for i in range(1, len(self.header_names) - 1):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

        if self.nRows:
            self.setRowCount(self.nRows)
