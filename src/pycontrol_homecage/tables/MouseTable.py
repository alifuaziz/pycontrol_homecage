from functools import partial

from PyQt5 import QtCore, QtWidgets

from pycontrol_homecage.utils import get_tasks
import pycontrol_homecage.db as database


class MouseTable(QtWidgets.QTableWidget):
    """This table contains information about all mice currently running in the
    system"""

    def __init__(self, GUI, parent=None):
        super(QtWidgets.QTableWidget, self).__init__(1, 15, parent=parent)
        self.header_names = [
            "",
            "Mouse_ID",
            "RFID",
            "Sex",
            "Age",
            "Experiment",
            "Task",
            "Protocol",
            "User",
            "Start_date",
            "Current_weight",
            "Start_weight",
            "is_training",
            "is_assigned",
            "training_log",
            "Setup_ID",
        ]

        self.GUI = GUI
        self.setHorizontalHeaderLabels(self.header_names)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.loaded = False

        self.fill_table()
        self.loaded = True

    def fill_table(self):
        """
        Fill the table with information from the `database.mouse_df`
        
        There is special behaviour for column: `Task` where there is a combox box that needs its behaviour defined.
        For the other columns they are filled in as strings. 
        """
        
        self.setRowCount(len(database.mouse_df))
        df_cols = database.mouse_df.columns

        for row_index, row in database.mouse_df.iterrows():
            for col_index in range(self.columnCount() - 1):
                col_name = df_cols[col_index]
                if col_name in self.header_names:
                    table_col_ix = self.header_names.index(df_cols[col_index])
                    if col_name == "Task":
                        task_combo = QtWidgets.QComboBox()
                        task_combo.activated.connect(
                            partial(self.update_task_combo, task_combo)
                        )
                        task_combo.installEventFilter(self)
                        task_combo.RFID = row["RFID"]
                        print(database.mouse_df["RFID"])
                        cTask = database.mouse_df.loc[
                            database.mouse_df["RFID"] == row["RFID"], "Task"
                        ].values[0]

                        task_combo.addItems([cTask] + get_tasks())

                        self.setCellWidget(row_index, table_col_ix, task_combo)

                        task_combo.currentTextChanged.connect(
                            partial(self.change_mouse_task, task_combo)
                        )

                    else:
                        self.setItem(
                            row_index,
                            table_col_ix,
                            QtWidgets.QTableWidgetItem(str(row[col_index])),
                        )
            chkBoxItem = QtWidgets.QTableWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)
            self.setItem(row_index, 0, chkBoxItem)

    def update_task_combo(self, combo: QtWidgets.QComboBox) -> None:
        cTask = combo.currentText()
        combo.clear()
        combo.addItems([cTask] + get_tasks())

    def change_mouse_task(self, combo: QtWidgets.QComboBox) -> None:
        """Change what task mouse is doing within the mouse_df"""

        database.mouse_df.loc[database.mouse_df["RFID"] == combo.RFID, "Task"] = (
            combo.currentText()
        ) 
        
        # Save the updated dataframe to disk
        database.mouse_df.to_csv(database.mouse_df.file_location)
        # fill the table again since the data has been updated
        self.fill_table()
