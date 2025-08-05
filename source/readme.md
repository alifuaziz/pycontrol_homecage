## Structure of source

Micropython boards
- pyControl
  - This is simply the micropython framework that runs on the pyControl boards for the normal running of the pyControl program. This is without adaptation
- pyAccessControl
  - This is the framework that runs the logic for the access control for doors / load cell / rfid reading. It also includes the required device drivers that run these processes

Used for interfacing between the micropython boards and the program
- Communication
  - This contains the logic for interfaceing between the main program and the micropython frameworks. 
  - For example there are `Pycboard` and `access_control` classes that esstially wrap the core functions of the micropython boards in code that allow them to be interfaced with via the main GUI. 
  - Additionally, the `system_handler.py` wraps both the `Pycboard` & the `access_control` board together as they are an important unit of the software

Main Program GUI and control for the processes

The following are the logic and code for the interface for using the software. Since there are places where the same table is located in multiple places, the `tables` are in a different folder
- GUI
  - This contains the main tabs which compose the program
- tables
- utils
