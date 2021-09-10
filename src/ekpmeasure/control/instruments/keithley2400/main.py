__all__ = ('config_measure_voltage', 'enable_source', 'disable_source', 'read')

def config_measure_voltage(k2400, nplc=1, voltage=21.0, auto_range=True):
        """ Configures the measurement of voltage. (Courtesy of pymeasure, see link below)
        args:
            k2400 (pyvisa.instrument): Keithley 2400
            nplc (float or int): Number of power line cycles (NPLC) from 0.01 to 10
            voltage (float): Upper limit of voltage in Volts, from -210 V to 210 V
            auto_range (bool): Enables auto_range if True, else uses the set voltage
        
        https://github.com/pymeasure/pymeasure/blob/4249c3a06457d5e4c8a2ba595aea867e99f9e5b6/pymeasure/instruments/keithley/keithley2400.py
        """
        k2400.write(":SENS:FUNC 'VOLT';"
                   ":SENS:VOLT:NPLC %f;:FORM:ELEM VOLT;" % nplc)
        if auto_range:
            k2400.write(":SENS:VOLT:RANG:AUTO 1;")
        else:
            k2400.write(":SENS:VOLT:RANG %g" % voltage)
            
        return
            
def enable_source(k2400):
    """Turn on source (either current or voltage)

    args:
        k2400 (pyvisa.instrument): K2400

    """
    k2400.write('OUTPUT ON')
    
def disable_source(k2400):
    """Turn off source (either current or voltage)

    args:
        k2400 (pyvisa.instrument): K2400


    """
    k2400.write('OUTPUT OFF')
    
def read(k2400):
    """Read measurement.

    args:
        k2400 (pyvisa.instrument): K2400

    returns:
        reading (str)

    """
    return k2400.query(":READ?").replace('\n', '')