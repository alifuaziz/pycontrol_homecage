from PyQt5.QtWidgets import (
    QWidget,
    QGroupBox,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QScrollArea,
    QComboBox,
    QCheckBox,
    QPlainTextEdit,
    QMessageBox,
    QMainWindow
)
from PyQt5.QtGui import QFont, QTextCursor

from pycontrol_homecage.new_experiment_menu import new_experiment_dialog
from pycontrol_homecage.tables import SetupTable, ExperimentOverviewTable
from pycontrol_homecage.plotting import Experiment_plot
import pycontrol_homecage.db as database


class SystemOverviewTab(QWidget):
    def __init__(self, parent:QMainWindow=None):
        super(QWidget, self).__init__(parent)

        self.GUI = self.parent()
        self.plot_isactive = False

        self._init_user_groupbox()

        self._init_experiment_groupbox()

        self._init_setup_groupbox()

        self._init_log_groupbox()
        # ------------------------------------ #
        # -------- Vertical stacking  -------- #
        # ------------------------------------ #

        self._set_global_layout()

    def _init_user_groupbox(self):
        self.user_groupbox = QGroupBox("Users")

        self.user_label = QLabel()
        self.user_label.setText("Users")

        self.login_button = QPushButton("Login")
        self.login_button.setToolTip("Login to a user to get started")
        self.add_user_button = QPushButton("Add User")
        self.add_user_button.setToolTip(
            "Add a new account. This requires email verification."
        )
        self.logout_button = QPushButton("Logout")
        self._set_user_layout()

    def _set_user_layout(self) -> None:
        self.Hlayout_users = QHBoxLayout()
        self.Hlayout_users.addWidget(self.login_button)
        self.Hlayout_users.addWidget(self.add_user_button)
        self.Hlayout_users.addWidget(self.logout_button)
        self.user_groupbox.setLayout(self.Hlayout_users)

    def _init_experiment_groupbox(self):
        self.experiment_groupbox = QGroupBox("Experiments")
        self.scrollable_experiments = QScrollArea()
        self.scrollable_experiments.setWidgetResizable(True)
        self.experiement_overview_table: ExperimentOverviewTable = (
            ExperimentOverviewTable(only_active=True)
        )
        self.scrollable_experiments.setWidget(self.experiement_overview_table)

        self._init_experiment_buttons()

        self._set_experiment_layout()

    def _init_experiment_buttons(self):
        self.start_experiment_button = QPushButton("Start New Experiment")
        self.start_experiment_button.clicked.connect(self.start_new_experiment)

        self.end_experiment_button = QPushButton("End Experiment")
        self.end_experiment_button.clicked.connect(self.end_experiment)

    def _set_experiment_layout(self):
        self.Hlayout_exp_buttons = QHBoxLayout()
        self.Hlayout_exp_buttons.addWidget(self.start_experiment_button)
        self.Hlayout_exp_buttons.addWidget(self.end_experiment_button)

        self.Vlayout_exp = QVBoxLayout(self)
        self.Vlayout_exp.addLayout(self.Hlayout_exp_buttons)
        self.Vlayout_exp.addWidget(self.scrollable_experiments)

        self.experiment_groupbox.setLayout(self.Vlayout_exp)

    def _init_setup_groupbox(self) -> None:
        self.setup_groupbox = QGroupBox("Setups")
        self.scrollable_setups = QScrollArea()
        self.scrollable_setups.setWidgetResizable(True)
        self.setup_table_widget: SetupTable = SetupTable(self.GUI)
        self.scrollable_setups.setWidget(self.setup_table_widget)

        # Buttons to control stuff
        self.show_setup_plot = QPushButton("Show Plot")
        self.show_setup_plot.clicked.connect(self.activate_plot)
        self.filter_setup_combo = QComboBox()
        self.filter_setup_combo.addItems(["Filter by"])

        self.setup_label = QLabel()
        self.setup_label.setText("Setups")

        self._set_setup_layout()

    def _set_setup_layout(self) -> None:
        self.Hlayout_setup_buttons = QHBoxLayout()
        self.Hlayout_setup_buttons.addWidget(self.show_setup_plot)
        self.Hlayout_setup_buttons.addWidget(self.filter_setup_combo)

        self.Vlayout_setup = QVBoxLayout()
        self.Vlayout_setup.addLayout(self.Hlayout_setup_buttons)
        self.Vlayout_setup.addWidget(QLabel("Table of Setups"))
        self.Vlayout_setup.addWidget(self.scrollable_setups)
        self.setup_groupbox.setLayout(self.Vlayout_setup)

    def _init_log_groupbox(self) -> None:
        self.log_groupbox = QGroupBox("Log")

        self.log_active = QCheckBox("Print to log")
        self.log_active.setChecked(True)

        self.filter_exp = QCheckBox("Filter by experiment")
        self.filter_exp.setChecked(False)
        self.filter_setup = QCheckBox("Filter by setup")
        self.filter_setup.setChecked(False)

        self.log_textbox = QPlainTextEdit()
        self.log_textbox.setMaximumBlockCount(500)
        self.log_textbox.setFont(QFont("Courier", 12))
        self.log_textbox.setReadOnly(True)
        self._set_log_layout()

    def _set_log_layout(self) -> None:
        self.log_hlayout = QHBoxLayout()
        self.log_hlayout.addWidget(self.log_active)
        self.log_hlayout.addWidget(self.filter_exp)
        self.log_hlayout.addWidget(self.filter_setup)

        self.log_layout = QVBoxLayout()
        self.log_layout.addLayout(self.log_hlayout)
        self.log_layout.addWidget(self.log_textbox)
        self.log_groupbox.setLayout(self.log_layout)

    def _set_global_layout(self) -> None:
        self.Vlayout = QVBoxLayout(self)

        self.Vlayout.addWidget(self.user_groupbox)
        self.Vlayout.addWidget(self.experiment_groupbox)
        self.Vlayout.addWidget(self.setup_groupbox)
        self.Vlayout.addWidget(self.log_groupbox)

    def activate_plot(self):
        """Start plotting incoming data from an experiment"""

        if len(database.exp_df) > 0:  # check first if an experiment is running
            self.experiment_plot: Experiment_plot = Experiment_plot()

            experiment = {"subjects": {}, "sm_infos": {}, "handlers": {}}
            # check which mice are training right now
            for _, row in database.setup_df.iterrows():
                if row["Mouse_training"] != "none":
                    # k = str(len(experiment['subjects']))
                    experiment["subjects"][row["Setup_ID"]] = row["Mouse_training"]
                    handler_ = [
                        setup
                        for k, setup in database.controllers.items()
                        if k == row["Setup_ID"]
                    ][0]
                    experiment["sm_infos"][row["Setup_ID"]] = handler_.PYC.sm_info
                    experiment["handlers"][row["Setup_ID"]] = handler_

            self.experiment_plot.setup_experiment(experiment)

            self.experiment_plot.set_state_machines(experiment)

            for ix_, hKey in enumerate(sorted(experiment["handlers"].keys())):
                experiment["handlers"][hKey].data_consumers = [
                    self.experiment_plot.subject_plots[ix_]
                ]

            self.experiment_plot.show()
            self.experiment_plot.start_experiment()
            self.plot_isactive = True

    def start_new_experiment(self) -> None:
        """
        This creates a new experiment which refers to a cohort of mice
        performing a set of tasks.
        """

        # Add check to see if there are any setups that are connected to the computer
        CONNECTED_STEP = any(database.setup_df["connected"])
        if not CONNECTED_STEP:
            reply = QMessageBox.question(
                self,
                "No Connected Setups",
                "There are no setups connected to the software. Do you want to go back to the main GUI (Yes) or continue (No)?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                return
            else:
                # Continue
                pass

        # Create a dialog
        self.new_experiment_config: new_experiment_dialog = new_experiment_dialog(
            self.GUI
        )
        self.new_experiment_config.exec_()

    def end_experiment(self):
        selected_experiments = self.experiement_overview_table.get_checked_experiments()
        if selected_experiments:
            self.experiement_overview_table.end_experiments(selected_experiments)

        self.experiement_overview_table.fill_table()

        self.GUI.experiment_tab.list_of_experiments.fill_table()
        self.GUI.setup_tab.setup_table_widget.fill_table()

    def write_to_log(self, msg, from_sys=None):
        if self.log_active.isChecked():
            if type(msg) is str:
                if "Wbase" not in msg:
                    self.log_textbox.moveCursor(QTextCursor.End)
                    self.log_textbox.insertPlainText(msg + "\n")
                    self.log_textbox.moveCursor(QTextCursor.End)
            elif type(msg) is list:
                for msg_ in msg:
                    if "Wbase" not in msg:
                        self.log_textbox.moveCursor(QTextCursor.End)
                        self.log_textbox.insertPlainText(str(msg_) + "\n")
                        self.log_textbox.moveCursor(QTextCursor.End)
        else:
            pass

    def _refresh(self):
        pass
