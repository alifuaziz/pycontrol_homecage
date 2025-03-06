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
    QMainWindow,
)
from PyQt5.QtGui import QFont, QTextCursor

from pycontrol_homecage.tables import SetupTable, ExperimentOverviewTable
from pycontrol_homecage.plotting import Experiment_plot
from pycontrol_homecage.dialogs import NewExperimentDialog, InformationDialog
import pycontrol_homecage.db as database


class SystemOverviewTab(QWidget):
    def __init__(self, parent: QMainWindow = None):
        super(QWidget, self).__init__(parent)

        self.GUI = self.parent()
        self.plot_isactive = False

        # Initialise User Groupbox
        self.user_groupbox = QGroupBox("Users")

        self.user_label = QLabel()
        self.user_label.setText("Users")

        self.login_button = QPushButton("Login")
        self.login_button.setToolTip("Login to a user to get started")
        self.add_user_button = QPushButton("Add User")
        self.add_user_button.setToolTip("Add a new account. This requires email verification.")
        self.logout_button = QPushButton("Logout")
        self.logout_button.setEnabled(False)

        self.Hlayout_users = QHBoxLayout()
        self.Hlayout_users.addWidget(self.login_button)
        self.Hlayout_users.addWidget(self.add_user_button)
        self.Hlayout_users.addWidget(self.logout_button)
        self.user_groupbox.setLayout(self.Hlayout_users)

        # Initialise Experiment Groupbox
        self.experiment_groupbox = QGroupBox("Active Experiments")
        self.scrollable_experiments = QScrollArea()
        self.scrollable_experiments.setWidgetResizable(True)
        self.experiement_overview_table: ExperimentOverviewTable = ExperimentOverviewTable(only_active=True)
        self.scrollable_experiments.setWidget(self.experiement_overview_table)

        # Initialise the New Experiment Buttons
        self.start_experiment_button = QPushButton("Start New Experiment")
        self.start_experiment_button.clicked.connect(self.start_new_experiment)

        self.end_experiment_button = QPushButton("End Experiment")
        self.end_experiment_button.clicked.connect(self.end_experiment)

        # Set the layout of these buttons
        self.Hlayout_exp_buttons = QHBoxLayout()
        self.Hlayout_exp_buttons.addWidget(self.start_experiment_button)
        self.Hlayout_exp_buttons.addWidget(self.end_experiment_button)
        self.Vlayout_exp = QVBoxLayout(self)
        self.Vlayout_exp.addLayout(self.Hlayout_exp_buttons)
        self.Vlayout_exp.addWidget(self.scrollable_experiments)
        self.experiment_groupbox.setLayout(self.Vlayout_exp)

        # Initialise the setups groupbox
        self.setup_groupbox = QGroupBox("Setups")
        self.scrollable_setups = QScrollArea()
        self.scrollable_setups.setWidgetResizable(True)
        self.setup_table_widget = SetupTable(self.GUI)
        self.scrollable_setups.setWidget(self.setup_table_widget)

        # Buttons to control stuff
        self.calibrate_setup_button = QPushButton("Calibrate Selected Setup")
        self.calibrate_setup_button.clicked.connect(self.open_calibration_dialog)

        self.show_setup_plot = QPushButton("Show Plot")
        self.show_setup_plot.clicked.connect(self.activate_plot)
        self.filter_setup_combo = QComboBox()
        self.filter_setup_combo.addItems(["Filter by"])

        self.setup_label = QLabel()
        self.setup_label.setText("Setups")

        # Set the layout of the setup groupbox
        self.Hlayout_setup_buttons = QHBoxLayout()
        self.Hlayout_setup_buttons.addWidget(self.show_setup_plot)
        self.Hlayout_setup_buttons.addWidget(self.filter_setup_combo)

        self.Vlayout_setup = QVBoxLayout()
        self.Vlayout_setup.addLayout(self.Hlayout_setup_buttons)
        self.Vlayout_setup.addWidget(QLabel("Table of Setups"))
        self.Vlayout_setup.addWidget(self.scrollable_setups)
        self.setup_groupbox.setLayout(self.Vlayout_setup)

        # Initliase the log groupbox
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
        # Set the Log groupbox layout
        self.log_hlayout = QHBoxLayout()
        self.log_hlayout.addWidget(self.log_active)
        self.log_hlayout.addWidget(self.filter_exp)
        self.log_hlayout.addWidget(self.filter_setup)

        self.log_layout = QVBoxLayout()
        self.log_layout.addLayout(self.log_hlayout)
        self.log_layout.addWidget(self.log_textbox)
        self.log_groupbox.setLayout(self.log_layout)

        # Set the Global Layout for the page
        self.Vlayout = QVBoxLayout(self)
        self.Vlayout.addWidget(self.user_groupbox)
        self.Vlayout.addWidget(self.experiment_groupbox)
        self.Vlayout.addWidget(self.setup_groupbox)
        self.Vlayout.addWidget(self.log_groupbox)

    # Button Function calls ---------------------------------------------------------------------

    def open_calibration_dialog(self) -> None:
        """
        Function to open calibratino dialog
        """
        # get checked setups
        isChecked = self.experiement_overview_table.get_checked_experiments()
        if not isChecked:
            info = InformationDialog(info_text="No setups have been selected. Please select a setup to calibrate.")
            info.exec_()
            return
        if len(isChecked) != 1:
            info = InformationDialog(info_text="Please select exactly one setup to calibrate.")
            info.exec_()
            return

        info = InformationDialog(info_text="Function Not Implemented")
        info.exec_()
        # Open a dialog
        # Add your dialog opening code here

    def activate_plot(self):
        """Start plotting incoming data from an experiment"""

        if len(database.exp_df) > 0:  # check first if an experiment is running
            self.experiment_plot = Experiment_plot()

            experiment = {"subjects": {}, "sm_infos": {}, "handlers": {}}
            # check which mice are training right now
            for _, row in database.setup_df.iterrows():
                if row["Mouse_training"] != "none":
                    # k = str(len(experiment['subjects']))
                    experiment["subjects"][row["Setup_ID"]] = row["Mouse_training"]
                    handler_ = [setup for k, setup in database.controllers.items() if k == row["Setup_ID"]][0]
                    experiment["sm_infos"][row["Setup_ID"]] = handler_.PYC.sm_info
                    experiment["handlers"][row["Setup_ID"]] = handler_

            self.experiment_plot.setup_experiment(experiment)

            self.experiment_plot.set_state_machines(experiment)

            for ix_, hKey in enumerate(sorted(experiment["handlers"].keys())):
                experiment["handlers"][hKey].data_consumers = [self.experiment_plot.subject_plots[ix_]]

            self.experiment_plot.show()
            self.experiment_plot.start_experiment()
            self.plot_isactive = True
        else:
            # Add error... idk what is means though.
            info = InformationDialog(info_text="len(databse.exp_df) == 0")
            info.exec_()

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
        self.new_experiment_config = NewExperimentDialog(self.GUI)
        self.new_experiment_config.exec_()

    def end_experiment(self):
        selected_experiments = self.experiement_overview_table.get_checked_experiments()

        if selected_experiments:
            self.experiement_overview_table.end_experiments(selected_experiments)
        else:
            # the `selected_experiment` variable is has no values assocaited with it
            info = InformationDialog(
                info_text="No experiments have been selected. Please select an experiment to stop it."
            )
            info.exec_()
        self.experiement_overview_table.fill_table()

        self.GUI.experiment_tab.list_of_experiments.fill_table()
        self.GUI.setup_tab.setup_table_widget.fill_table()

    # Functions for writing to GUI ----------------------------------------------------------------------------------------

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
