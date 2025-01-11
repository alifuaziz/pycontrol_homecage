#

[Main Notes](/ailfs_notes.md)

- Ardunio editor for using the pyboard. however this software is a bit bug-y
- However the 'move files' button doesn't seem to transfer files very well. the pyControl method for tranferring files works better (...sometimes. It will work if you reset the board and then upload the files I think.)

- I have finally been able to run Yves firmware on the pyboard.

- Need now to think about how the codebase recieves information from the pyboard and writes them to database files etc.

- Messages are handled from  `Access_control.process_data()`  function. 
- They are written a log file foundin the AC_logger_dir (remember that this is defined in the `db.py` file.)

- For getting the system working, it is probably worth trying to implement a bunch of intergration testing for the different states that the host computer should be able to handle and write to log files. (e.g. see `system_handler.process_ac_state()` has 4 states that it should be able to handle)
- see [Intergration testing plan](/Intergration_testing.md)

- A lot of the code involves looking at and updating dataframes to reflect the information being emitted from the pyboard (which is the data producer of the whole system. )

## TODO

-[x] Get the pyboard emitting signals
-[x] Recieve the state signals into the access control module 

- [x]Do this with the system controller as well. 
the states do not seem to be writing to file? idk why though/ 
- get the system handler able to write the signals to file appropriately. 


- https://stackoverflow.com/questions/15331726/how-does-functools-partial-do-what-it-does