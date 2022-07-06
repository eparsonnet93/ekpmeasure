import numpy as np
from .. import misc
from ....utils import get_number_and_suffix

__all__ = ('restore', 'is_on', 'measure')

def get_voltage(nano_voltmeter):
    """Measures the nanovoltmeter once by first resetting it to idle state
    then setting the function to volts (instead of temp) and selecting chnnl 1
    and reading it with the auto range function
    
    args:
        nanovoltmeter (pyvisa.resources.gpib.GPIBInstrument): Keithley 2182A 

    """
    nano_voltmeter.write("*rst")
    nano_voltmeter.write(":sens:func 'volt'")
    nano_voltmeter.write(":sens:chan 1")
    nano_voltmeter.write("sens:volt:chan1:rang:auto on")
    return nano_voltmeter.query(":read?").replace('\n', '')


def restore(nano_voltmeter):
    """Restore settings on nanovoltmeter.

    args:
        nanovoltmeter (pyvisa.resources.gpib.GPIBInstrument): Keithley 2182A

    
    """
    nano_voltmeter.write("*rst")
    return


def is_on(nano_voltmeter):
    """Query the nanovoltmeter as on or off.

    args:
        nanovoltmeter (pyvisa.resources.gpib.GPIBInstrument): Keithley 2182A

    returns:
        (bool): True (on) or False (off)
    """
    result = nano_voltmeter.query('output?')
    if float(result.replace('\n', '')) == 1:
        return True
    else:
        return False
