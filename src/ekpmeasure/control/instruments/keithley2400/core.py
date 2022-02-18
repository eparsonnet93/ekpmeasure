__all__ = ('config_measure_voltage', 'config_measure_resistance', 'enable_source', 
	'disable_source', 'read', 'config_voltage_pulse', 'set_resistance_mode_manual',
	'set_voltage_compliance', 'set_source_current_amplitude',
	)


def set_resistance_mode_manual(k2400):
    """Set the mode to manual resistance OHMs
    
    args:
        k2400 (pyvisa.instrument): Keithley 2400
    """
    k2400.write(":SENS:RES:MODe MAN")
    return

def set_source_current_amplitude(k2400, amplitude:float=0.0001):
    """Set the current source amplitude.
    
    args:
        k2400 (pyvisa.instrument): Keithley 2400
        amplitude (float): Current amplitude in Amps
    """
    k2400.write(':SOUR:CURR:LEV:IMM:AMPL {}'.format(amplitude))
    return

def set_voltage_compliance(k2400, compliance:float=2.1):
    """Set the Voltage compliance.
    
    args:
        k2400 (pyvisa.instrument): Keithley 2400
        compliance (float): Voltage compliance in Volts
    """
    k2400.write(':SENS:VOLT:DC:PROT:LEV {}'.format(compliance))
    return

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

def config_measure_resistance(k2400, nplc=1, voltage=21.0, auto_range=True):
	""" Configures the measurement of resistance. (Courtesy of pymeasure, see link below)
	args:
		k2400 (pyvisa.instrument): Keithley 2400
		nplc (float or int): Number of power line cycles (NPLC) from 0.01 to 10
		voltage (float): Upper limit of voltage in Volts, from -210 V to 210 V
		auto_range (bool): Enables auto_range if True, else uses the set voltage
	
	https://github.com/pymeasure/pymeasure/blob/4249c3a06457d5e4c8a2ba595aea867e99f9e5b6/pymeasure/instruments/keithley/keithley2400.py
	"""
	k2400.write(":SENS:FUNC 'RES';"
			   ":SENS:RES:NPLC %f;:FORM:ELEM RES;" % nplc)
	if auto_range:
		k2400.write(":SENS:RES:RANG:AUTO 1;")
	else:
		k2400.write(":SENS:RES:RANG %g" % voltage)
		
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
	"""Do and Read measurement.

	args:
		k2400 (pyvisa.instrument): K2400

	returns:
		reading (str)

	"""
	return k2400.query(":READ?").replace('\n', '')

def config_voltage_pulse(k2400, nplc:float=.01, amplitude:float=5):
	"""Configure for Voltage pulse. nplc=.01 gives ~1.5ms pulse nplc=.1 is ~7ms pulse

	args:
		k2400 (pyvisa.instrument): K2400
		nplc (float): (.01, 10) power line cycles to specify speed
		amplitude (float): Voltage amplitude in volts

	examples:

		.. code-block:: python

			k24 = pyvisa.ResourceManager().open_resource(<GBIP>)
			config_voltage_pulse(k24, amplitude=10) # configure 10V pulse
			enable_source(k24) # start the source
			read(k24) # apply the pulse
	"""
	k2400.write("""*RST
	:SENS:FUNC:CONC OFF
	:SOUR:FUNC VOLT
	:SOUR:VOLT:MODE SWE
	:SOURce:SWEep:POINts 2
	:SOURce:VOLTage:STARt {}
	:SOURce:VOLTage:STOP 0
	:SENS:VOLT:NPLCycles {}
	:TRIG:COUN 2
	:TRIG:DELay 0
	:SOUR:DEL 0
	""".format(amplitude, nplc))
	return