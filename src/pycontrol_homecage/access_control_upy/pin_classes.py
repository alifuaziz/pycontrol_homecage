'''
Classes that wrap around the pyb.Pin class to provide additional functionality with nice syntax
- Signal pins 
- Magnet pins
'''


import pyb




class signal_pin:
    """ Pseudo-subclass of pin that replicates its method but within the context of the
        surrounding hardware used for door sensing.
    """
    def __init__(self,sense_pin,enable_pin_1,enable_pin_2,sense_delay=3000,threshold=1400,check_every=10):
        self.pin = sense_pin
        self.enable_pin_1 = enable_pin_1
        self.enable_pin_2 = enable_pin_2
        self.sense_delay = sense_delay
        self.threshold = threshold
        self._last_pin_check = pyb.millis() # used to keep track of time passing.
        self.state = 0
        self.check_every = check_every
        self.measured_value = 0
    
    def value(self,print_it=False):
        """ Returns true if the door is open. This convention is used for consistency with
            the previous access control code
        """
        #value =
        if pyb.elapsed_millis(self._last_pin_check)>self.check_every:
            self.enable_pin_1.value(0)
            self.enable_pin_2.value(0)
            pyb.udelay(self.sense_delay)
            self.measured_value = self.pin.read()
            #self.value = value
            self.enable_pin_1.value(1)
            self.enable_pin_2.value(1)
            if print_it:
                print(self.measured_value)
            self.state = (self.measured_value > self.threshold)
            self._last_pin_check = pyb.millis()

        return self.state

    #def get_measured_value(self):
    #    return

    



class magnet_pin:
    """ Psuedo-subclass of an output pin that enables switching magnets on and off but
        allowing for demagnetisation
    """
    def __init__(self,highside,lowside,demag_delay=10):
        self.highside = highside
        self.lowside=lowside
        self.demag_delay = demag_delay
        self.has_demagged = False

    def value(self,set_value):
        # sets the value of the magnet pin taking into account the need to demagnetise
        if set_value==1:
            self.highside.value(1)
            self.lowside.value(0)
            self.has_demagged = False
        elif set_value==0:
            if not self.has_demagged:
                self.highside.value(0)
                self.lowside.value(1)
                pyb.delay(self.demag_delay)
                self.lowside.value(0)
                self.has_demagged = True
            else:
                self.highside.value(0)
                self.lowside.value(0)      

    
