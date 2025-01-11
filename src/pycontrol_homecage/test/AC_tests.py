'''
Alif tries unit testing a piece of code 

Note: in these tests the firmware for both the boards have are loaded properly. You should check if that is working for you. 


'''
import unittest
from unittest.mock import patch
from datetime import datetime
from functools import partial

from pycontrol_homecage.com.system_handler import system_controller as SystemController
from pycontrol_homecage.com.pycboard import Pycboard
from pycontrol_homecage.com.access_control import Access_control


class TestSystemController(unittest.TestCase):
    
    @classmethod
    def setUp(cls):
        '''Function that will setup the COM ports'''
        
        # CONSTANTS
        COM_AC = 'COM4'
        COM_PYC = 'COM3'
        SETUP_ID = 'setup1'

        try: 
            # Re-defines the print function where the kwarg `flush` is always true. 
            print_func = partial(print, flush=True)
            # Datalogger class (This is the object that writes things to disk
            cls.system_controller = SystemController(print_func=print_func, setup_id=SETUP_ID)
            # Instantiate Pycontrol board
            cls.pycontrol_board = Pycboard(serial_port=COM_PYC, 
                                    print_func=print_func, data_logger=cls.system_controller)
            # Load the pycontrol_framework
            cls.access_control = Access_control(serial_port=COM_AC, 
                                            print_func=print_func,
                                            data_logger=cls.system_controller)
            
            # System controller gets access to the pycontrol board (That runs the operant box task)
            cls.system_controller.add_PYC(cls.pycontrol_board)
            # Add it also getes access to the access control board (That run the access control module)
            cls.system_controller.add_AC(cls.access_control)
            
            
            
        except Exception as e: 
            raise e
    
    @classmethod
    def tearDown(cls):
        '''Close the ports correctly'''

        try: 
            # Close the pycontrol_board
            cls.pycontrol_board.close()
        
        except Exception as e: 
            raise e    

    # def test_process_ac_state_error_state(cls):
    #     '''
    #     Test the functionality of the 'error_state' 
    #     '''
    #     cls.system_controller.process_ac_state(
    #         state='error_state'
    #     )
    #     cls.assertEqual(cls.system_controller.PYC.framework_running, False)

    
    def test_process_ac_state_allow_entry(cls):
        '''
        Test the functionality of the 'allow_entry' 
        '''
        
        cls.system_controller._handle_allow_entry()
        
        expected_output = cls.system_controller.mouse_data
        cls.system_controller.process_ac_state(
            state='allow_entry',
            now=datetime.now().strftime('%Y-%m-%d-%H%M%S')
        )
        cls.assertEqual(expected_output, cls.system_controller.mouse_data)

    # def test_process_ac_state_allow_entry_mouse_training
    
    
    
    
if __name__ == '__main__':
    unittest.main()

    # This code will run the test in order: 'test_c','test_a','test_b'
    # suite = unittest.main()
    # suite.addTest(TestExample('test_c'))
    # suite.addTest(TestExample('test_a'))
    # suite.addTest(TestExample('test_b'))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)
    
    