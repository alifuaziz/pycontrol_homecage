import json
import os
import time
from datetime import datetime

import pandas as pd

from pycontrol_homecage.utils import get_path
import pycontrol_homecage.db as database
from paths import paths
from pycontrol_homecage.com.messages import (
    MessageRecipient,
    MessageSource,
    emit_print_message,
)
from pycontrol_homecage.com.data_logger import Data_logger


class system_controller(Data_logger):
    """
    This is a class that sits on top of access control and pycboard classes
    and controls data storage for the system as well as setting tasks when
    mice enter/exit the training apparatus. There is one system controller
    for each homecage system.
    """

    def __init__(self, AC, PYC, print_func=print, setup_ID=None) -> None:
        self.on = True
        self.setup_ID = setup_ID
        self.AC = AC
        self.AC.data_logger = self
        self.PYC = PYC
        self.PYC.data_logger = self
        self.analog_files = {}
        self.sm_info = {}
        self.print_func = print_func
        self.active = False
        self.mouse_in_AC = None
        self.data_dir = get_path("data")
        self.data_file = None

    def disconnect(self):
        """This needs to be done for when we have multiple setups"""
        self.PYC.close()  # This closes the connection to the behaviour board
        self.AC.close()  # This closes the connection to AC board by pyboard class

    def check_for_data(self):
        """check whether either AC or the PYC board have data to deliver"""
        self.AC.process_data()
        self.PYC.process_data()

    def process_data(self, new_data):
        """If data _file is open new data is written to file."""
        if self.data_file:
            self.write_to_file(new_data)

        # self.GUI.print_msg(new_data, ac_pyc='pyc')
        emit_print_message(new_data, MessageRecipient.system_overview, MessageSource.PYCBoard)

        if MessageRecipient.direct_pyboard_dialog in database.print_consumers:
            emit_print_message(new_data, MessageRecipient.direct_pyboard_dialog, MessageSource.PYCBoard)

    def process_data_AC(self, new_data):
        """Here process the data from the access control system to
            actually do stuff: open/close files, update csv files with
            weights etc

        based on the contents of the messages, a range of things can be done by the access controller:
        - 'state'
            - 'error_state'
            - 'allow_entry'
            - 'mouse_training'
            - 'allow_exit'
        - 'RFID'
        - 'weight'


        """
        # the time at which the data was received
        now = datetime.now().strftime("%Y-%m-%d-%H%M%S")

        exp_running_now = database.setup_df.loc[database.setup_df["COM"] == self.PYC.serial_port]["Experiment"].values

        # if exp_running_now != 'none':  # YW 11/02/21 NOT SURE WHY THIS CHECK IS HERE
        for msg in new_data:
            # Message to print the message to the system overview.
            emit_print_message(msg, MessageRecipient.system_overview, MessageSource.ACBoard)

            if "cal" in msg:
                # THis was handled in the function call above.
                pass
            else:
                if "state" in msg:
                    self.process_ac_state(msg[6:])
                if "RFID" in msg:
                    self.mouse_data["RFID"] = int(msg.strip("RFID:"))
                if "weight" in msg:
                    self.mouse_data["weight"] = float(msg.strip("weight:"))

        # else:

        #     for msg in new_data:
        #         emit_print_message(msg,
        #                         MessageRecipient.system_overview,
        #                         MessageSource.ACBoard
        #                         )
        #         # if MessageRecipient.direct_pyboard_dialog in database.print_consumers:
        #         #     emit_print_message(new_data,
        #         #                         MessageRecipient.direct_pyboard_dialog,
        #         #                         MessageSource.PYCBoard
        #         #                         )

    """
    Functions for processing the data collected from the access control. I.e writing them to the correct files in the database.
    """

    def process_ac_state(self, state: str) -> None:
        """
        This is the that receives the states from the access control system and calls the relevent functions in the main script
        to handle these states.
        """
        # update access control state in the database
        database.setup_df.loc[database.setup_df["COM"] == self.PYC.serial_port, "AC_state"] = state

        if state == "error_state":
            # Handle error state from Access control board
            self.PYC.stop_framework()  # stops the task
            time.sleep(0.05)
            self.PYC.process_data()
            self.close_files()

        if state == "allow_entry":
            # Reset the mouse information on entry
            self.mouse_data = {
                "weight": None,
                "RFID": None,
                "entry_time": None,
                "exit_time": None,
                "task": None,
            }

        # first entry in this state is when the mouse first enters the apparatus
        elif state == "mouse_training":
            if self.data_file is None: # The mouse has NOT re-entered the Training room from being it it. It has come in from the 'home' side
                self._handle_mouse_training()

        elif state == "allow_exit":
            self.mouse_data["exit_time"] = datetime.now().strftime("%Y-%m-%d-%H%M%S")

            if self.data_file:
                self.PYC.stop_framework()
                time.sleep(0.05)
                self.PYC.process_data()
                self.close_files()

    def _handle_mouse_training(self) -> None:
        """This function is called to start the Pycontrol framework for this animal.
        This is run on mouse training beginning.

        Steps of this function:
        - Gets the correct mouse row from the the `mouse_df` table
        - Gets the `Mouse_ID` from the mouse row
        - Gets the `Protocol` from the mouse row. This protocal is either a task or a protocol.

        If the mouse is assigned (? a task)
        Then the task is run, else: the mouse protocol is run.

        The entry time and the task are assigned to the `self.mouse_data`
        """
        # Get the mouse row from the RFID number
        mouse_row = database.mouse_df.loc[database.mouse_df["RFID"] == self.mouse_data["RFID"]]
        # Raise an exception if mouse_row is empty
        if mouse_row.empty:
            raise Exception(f"Error: No mouse found with the given RFID ({self.mouse_data['RFID']}) in the database.")
        # Get the mouse ID and protocol frpom the mouse row.
        mouse_ID, protocol = mouse_row[["Mouse_ID", "Protocol"]].values[0]

        # if a task has been assigned to this mouse
        if mouse_row["is_assigned"].values[0]:
            # if the current protocol is a task do so.
            if "task" in protocol:  # All tasks have "task" as a substring of their name
                task = self.start_running_mouse_task(mouse_info_row=mouse_row)
            else:  # Otherwise they must be protocals.
                task = self.run_mouse_protocol(mouse_info_row=mouse_row)

            self.mouse_data["entry_time"] = datetime.now()
            self.mouse_data["task"] = task

            mouse_ID = mouse_row["Mouse_ID"].values[0]
            experiment_name = mouse_row["Experiment"].values[0]
            protocol = mouse_row["Protocol"].values[0]
            task = mouse_row["Task"].values[0]

            file_name = "_".join([mouse_ID, experiment_name, task, datetime.now()]) + ".txt"
            fullpath_to_datafile = os.path.join(self.data_dir, experiment_name, mouse_ID, protocol, file_name)
            # Save a copy of the taskfile that was run
            with open(os.path.join(get_path("tasks"), task + ".py"), "r") as f_:
                # read the task file uploaded to pyboard
                dat_ = f_.readlines()
                # save it to a new file
                with open(paths["mice_dir"] + "_taskFile.txt", "w") as f_backup:
                    f_backup.writelines(dat_)

            # Open the data file (using the datalogger class)
            self.open_data_file(
                data_dir=fullpath_to_datafile,
                experiment_name=experiment_name,
                setup_ID=self.setup_ID,
                subject_ID=mouse_ID,
                datetime_now=datetime.now(),
            )

            self.PYC.start_framework()

            # Update database on entry
            database.mouse_df.loc[database.mouse_df["RFID"] == self.mouse_data["RFID"], "Current_weight"] = (
                self.mouse_data["weight"]
            )
            database.mouse_df.loc[database.mouse_df["RFID"] == self.mouse_data["RFID"], "is_training"] = True
            database.setup_df.loc[database.setup_df["COM"] == self.PYC.serial_port, "Mouse_training"] = mouse_ID
            # Update the tables from queue
            database.update_table_queue.append("setup_tab.list_of_setups")
            database.update_table_queue.append("system_tab.list_of_setups")

    def start_running_mouse_task(self, mouse_info_row: pd.Series) -> None:
        """
        Runs Mouse task from the information in the `mouse_info_row`

        Args:
            mouse_info (pd.Series): Row of the database.mouse_df that corresponds the mouse that entered the experiment room
        """
        # Get the name of the task
        task = mouse_info_row["Task"].values[0]
        # self.GUI.print_msg("Uploading: " + str(task), ac_pyc='pyc')
        emit_print_message(
            "Uploading: " + str(task),
            MessageRecipient.system_overview,
            MessageSource.GUI,
        )
        #################################### Not working!
        # Set the state machine for the task
        self.PYC.setup_state_machine(sm_name=task)
        # Set the `set_variables` for the task
        if not pd.isnull(mouse_info_row["set_variables"].values):
            # Dictionary of set variables are used to set Pycontrol board
            set_variables = eval(mouse_info_row["set_variables"].values[0])
            if set_variables:
                for k, v in set_variables.items():
                    self.PYC.set_variable(k[2:], eval(v))
        # Set the `persistent_variables` for the task
        if not pd.isnull(mouse_info_row["persistent_variables"].values):
            persistent_variables = eval(mouse_info_row["persistent_variables"].values[0])
            if persistent_variables:
                for k, v in persistent_variables.items():
                    if v != "auto":
                        self.PYC.set_variable(k[2:], eval(v))

    def run_mouse_protocol(self, mouse_info_row: pd.Series) -> str:
        """
        - Get the protocol, mouse id, current stage of the protocol from the mouse_info_row
        - Load in the protocol dataframe / mouse log dataframe

        - Check wether the stage of the protocol should be changed.
            - The stage is the row index of the .prot file.
        -
        """

        # If running a real protocol, handle (potential) update of protocol.
        newStage = False
        try:
            stage = int(mouse_info_row["Stage"].values[0])
        except ValueError:
            # info
            print("ERROR:Stage not valid!!")
        prot = mouse_info_row["Protocol"].values[0]
        mouse_ID = mouse_info_row["Mouse_ID"].values[0]

        protocol_path = os.path.join(get_path("prot"), prot)
        mouse_prot = pd.read_csv(protocol_path, index_col=0)

        # read last stage of training
        logPth = os.path.join(get_path("mice"), mouse_ID + ".csv")
        mouse_df_log = pd.read_csv(logPth)

        # Protocol Stage row
        current_protocol_stage = mouse_prot.iloc[stage]

        ####################### LOGIC FOR CHECKING IF STAGE SHOULD BE INCREASED #################
        ######### This logic is not tested as I do not know how to get things into the log for the mouse
        # If the number of columns is more that 0:
        if len(mouse_df_log) > 0:
            # Get the final row of the dataframe (since this is the most up to date one.)
            mouse_df_log = mouse_df_log.iloc[-1]
            # Turn the string of a dict that is saved in the log into a variables dictionary
            pycontrol_variables_dict = eval(mouse_df_log["Variables"])

            if not pd.isnull(current_protocol_stage["threshV"]):
                # Load in the String of list of lists
                for k, thresh in eval(mouse_prot.loc[str(stage), "threshV"]):
                    print(
                        float(pycontrol_variables_dict[k]),
                        float(thresh),
                        float(pycontrol_variables_dict[k]) >= float(thresh),
                    )
                    if float(pycontrol_variables_dict[k]) >= float(thresh):
                        newStage = True
                        stage += 1

        ########################################################################################

        updated_stage_row = mouse_prot.iloc[stage]

        task = updated_stage_row["task"]

        # Updates the mouse_df to reflect any changes in the task stage or the mouse is in.
        database.mouse_df.loc[database.mouse_df["RFID"] == self.mouse_data["RFID"], "Task"] = task
        database.mouse_df.loc[database.mouse_df["RFID"] == self.mouse_data["RFID"], "Stage"] = stage

        self.PYC.setup_state_machine(sm_name=task)

        # handle setting varibles

        for k, defV in eval(updated_stage_row["defaultV"]):
            # Persistant veriables. They are set the same for every instance of the pycontrol statemachine
            self.PYC.set_variable(k, float(defV))

        if len(mouse_df_log) > 0:
            if not newStage:  # newStage is False
                for k in updated_stage_row["trackV"]:
                    # Updated variables. They are changed based on the behaviour of the animal.
                    self.PYC.set_variable(k, float(pycontrol_variables_dict[k]))
        return task

    def close_files(self):
        """
        This function closes the files assocaited with the mouse table (This is the information about the mice currently running in the system)
        A part of this process requires the saving of the data collected from the access control to the appropriate datatables.

        This table contains headings such as ['','Mouse_ID', 'RFID', 'Sex', 'Age', 'Experiment', 'Task','Protocol', 'User',
                            'Start_date', 'Current_weight', 'Start_weight', 'is_training',
                            'is_assigned', 'training_log', 'Setup_ID']


        BUG: ##NEED TO UPDATE THIS FUNCTION SO THAT ON ERROR IT CLOSES THE DATA FILES AND
        # UPDATES THE variables file appropriately. Also should make a note that an error
        #ocurred if it does.

        """

        if self.data_file:
            RUN_ERROR = False
            try:
                v_ = self.PYC.get_variables()
                self.data_file.writelines("Variables")
                self.data_file.writelines(repr(v_))
                if (
                    not database.mouse_df.loc[
                        database.mouse_df["RFID"] == self.mouse_data["RFID"],
                        "persistent_variables",
                    ]
                    .isnull()
                    .values.any()
                ):
                    persistent_variables = eval(
                        database.mouse_df.loc[
                            database.mouse_df["RFID"] == self.mouse_data["RFID"],
                            "persistent_variables",
                        ].values[0]
                    )
                else:
                    persistent_variables = {}
                for k, v__ in v_.items():
                    k = "v." + k
                    if k in persistent_variables.keys():
                        persistent_variables[k] = v__
                database.mouse_df.loc[
                    database.mouse_df["RFID"] == self.mouse_data["RFID"],
                    "persistent_variables",
                ] = json.dumps(
                    persistent_variables
                )  # ignore this line
                # JSON.dumps is a string representation of a dictionary. that is put into a column of a dataframe. This is probably not the most elegant solution...
            except Exception as e:
                print(e)
                if (
                    not (
                        database.mouse_df.loc[
                            database.mouse_df["RFID"] == self.mouse_data["RFID"],
                            "persistent_variables",
                        ]
                    )
                    .isnull()
                    .values.any()
                ):
                    v_ = eval(
                        database.mouse_df.loc[
                            database.mouse_df["RFID"] == self.mouse_data["RFID"],
                            "persistent_variables",
                        ].values[0]
                    )
                self.PYC.reset()
                RUN_ERROR = True

            self.data_file.close()
            self.update_mouse_log(v_, RUN_ERROR)

            self.data_file = None
            self.file_path = None
            if "RUN_ERROR" not in database.mouse_df.columns:
                database.mouse_df.insert(len(database.mouse_df.columns), "RUN_ERROR", pd.Series(), True)

            # Selects the `RUN_ERROR` column for the appropriate row of the mouse_df and sets its value to the `RUN_ERROR` value
            database.mouse_df.loc[database.mouse_df["RFID"] == self.mouse_data["RFID"], "RUN_ERROR"] = RUN_ERROR
            database.mouse_df.loc[database.mouse_df["RFID"] == self.mouse_data["RFID"], "is_training"] = False
            # Removes columns from the mouse_df that are unnamed ???
            database.mouse_df = database.mouse_df.loc[:, ~database.mouse_df.columns.str.contains("^Unnamed")]
            database.mouse_df.to_csv(paths["mice_dataframe_filepath"])
            
            database.setup_df.loc[database.setup_df["COM"] == self.PYC.serial_port, "Mouse_training"] = ""
            database.setup_df = database.setup_df.loc[:, ~database.setup_df.columns.str.contains("^Unnamed")]
            database.setup_df.to_csv(paths["setup_dir_dataframe_filepath"])

        for analog_file in self.analog_files.values():
            if analog_file:
                analog_file.close()
                analog_file = None

    def update_mouse_log(self, v_, RUN_ERROR):
        """Update the log of mouse behavior. v_ are the variables
        If there is an error retrieving variables from the
        pyboard, then copies over variables from the previous
        session
        """

        mouse_row = database.mouse_df.loc[database.mouse_df["RFID"] == self.mouse_data["RFID"]]
        mouse_ID = mouse_row["Mouse_ID"].values[0]

        logPth = os.path.join(get_path("mice"), mouse_ID + ".csv")
        df_mouseLog = pd.read_csv(logPth)

        entry_nr = len(df_mouseLog)
        df_mouseLog._append(pd.Series(), ignore_index=True)
        if "RUN_ERROR" not in df_mouseLog.columns:
            df_mouseLog.insert(len(df_mouseLog.columns), "RUN_ERROR", pd.Series(), True)

        for k in self.mouse_data.keys():
            if k in df_mouseLog.columns:
                df_mouseLog.loc[entry_nr, k] = self.mouse_data[k]

        df_mouseLog.loc[entry_nr, "Variables"] = repr(v_)
        df_mouseLog.loc[entry_nr, "RUN_ERROR"] = RUN_ERROR

        df_mouseLog = df_mouseLog.loc[:, ~df_mouseLog.columns.str.contains("^Unnamed")]
        df_mouseLog.to_csv(logPth)
