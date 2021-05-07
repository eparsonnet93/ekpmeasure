from .. import misc
import time

__all__ = (
	'get_lockin_r_theta','set_harmonic', 'set_time_constant', 'get_time_constant', 'auto_gain',
	'get_sensitivity', 'set_sensitivity', 'get_reference_source', 'set_reference_source',
	'set_internal_frequency', 'set_internal_amplitude', 'get_time_constant_from_frequency',
	'get_time_constant_float', 'set_lockin_sensitivity', 'initialize_lockin', 'set_phase'
)


time_constant_to_index_mapper = {
	'10us':0,'30us':1,'100us':2,'300us':3,'1ms':4,'3ms':5,'10ms':6,
	'30ms':7,'100ms':8,'300ms':9,'1s':10,'3s':11,'10s':12,'30s':13,
	'100s':14,'300s':15,'1ks':16,'3ks':17,'10ks':18,'30ks':19,
}

index_to_time_constant_mapper = {time_constant_to_index_mapper[key]:key for key in time_constant_to_index_mapper}

sensitivity_to_index_mapper = {
	'2nv/fa':0, '5nv/fa':1, '10nv/fa':2, '20nv/fa':3, '50nv/fa':4, '100nv/fa':5,
	'200nv/fa':6, '500nv/fa':7, '1uv/pa':8, '2uv/pa':9, '5uv/pa':10, '10uv/pa':11,
	'20uv/pa':12, '50uv/pa':13, '100uv/pa':14, '200uv/pa':15, '500uv/pa':16, 
	'1mv/na':17, '2mv/na':18, '5mv/na':19, '10mv/na':20, '20mv/na':21, '50mv/na':22, 
	'100mv/na':23, '200mv/na':24, '500mv/na':25, '1v/ua':26
}

index_to_sensitivity_mapper = {sensitivity_to_index_mapper[key]:key for key in sensitivity_to_index_mapper}

def set_phase(lockin, phase=None):
	"""Set the phase of the lockin.

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS830
		phase (str): Phase.




	"""
	if type(phase) == type(None):
		return
	else:
		lockin.write("phas {}".format(phase))
	return

def initialize_lockin(lockin, trigger, harmonic, time_constant, frequency = None, amplitude = None,):
	"""Initialize lockin.

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS830
		trigger (str): Trigger source. 'internal' or 'external'.
		harmonic (int): Harmonic
		time_constant (str): Time constant.
		frequency (str): If internal triggering, must supply frequency and amplitude.
		amplitude (str): Units of Volts. If internal triggering, must supply frequency and amplitude.  



	"""
	trigger = trigger.lower()
	assert trigger == 'internal' or trigger == 'external', 'Trigger: {} not allowed. Must me "internal" or "external"'.format(trigger)

	if trigger == 'internal' and (type(frequency) == type(None) or type(amplitude) == type(None)):
		raise ValueError('must supply a frequency if internal triggering. currently supplied None')
	
	#initialize
	set_reference_source(lockin, trigger)
	set_time_constant(lockin, time_constant)

	set_harmonic(lockin, harmonic)
	return 

def set_lockin_sensitivity(lockin, sensitivity='default', sleep_time = 10):
	"""Set the sensitivity on the lockin. 'default' will auto-gain the lockin.

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS830
		sensitivity (str): Sensitivity.
		sleep_time (int or float): Amount of time to sleep before amd after setting the sensitivity. 




	"""
	time.sleep(sleep_time)

	if sensitivity == 'default':
		#autogain the lockin
		auto_gain(lockin)

		#wait for the autogain to progress
		time.sleep(10)
	else:
		set_sensitivity(lockin, sensitivity)
		time.sleep(sleep_time)
	return

def get_time_constant_float(time_constant):
	"""Get float of time constant.

	args:
		time_constant (str): Time constant.

	returns:
		(float): Time constant float. 

	


	"""
	try:
		out = time_constant.replace('s','')
		out.replace('u', 'e-6')
		out.replace('m', 'e-3')
		out.replace('k', 'e3')
		return float(out)
	except:
		raise TypeError('unable to convert {} to float. allowed suffixes are us, ms, s, ks'.time_constant)

def get_time_constant_from_frequency(frequency, multiplier = 3):
	"""Estimate a good time constant from the frequency. (multiplier/frequency).

	args:
		frequency (str): Frequency
		multipler (int or float): Multiplier for time constant.




	"""
	number, suffix = misc._get_number_and_suffix(frequency)
	freq = float(str(number) + misc.freq_mapper[suffix])
	time = multiplier*1/freq
	sci_time = misc._scientific_notation(time)
	
	exponent = sci_time.split('e')[-1]
	counter = 0
	while float(exponent) not in set({-6, -3, 0, 3}):
		exponent = str(int(exponent) + 1)
		counter += 1
		
	number = sci_time[0]
	if number == '2':
		number = '3'
	elif number != '1' and number != '3':
		number = '10'
		
	for i in range(counter):
		number = str(float(number))
		spl = number.split('.')
		number = spl[0][:-1] + '.' + spl[0][-1:] + spl[1]
	
	tmp_out = '{}e{}'.format(number, exponent)
	#final check
	if tmp_out[0] == '0' or tmp_out[0] == '.':
		new_exponent = int(tmp_out.split('e')[-1])-3
		new_number = float(tmp_out.split('e')[0])*10**3
		tmp_out = '{}e{}'.format(new_number, new_exponent)
		
	try:
		tmp_out = tmp_out.split('.')[0] + tmp_out.split('.')[1][1:]
	except:
		pass
	tmp_out.replace('.','')
	
	tmp_out = tmp_out.split('e')[0] + misc.sci_to_time_mapper['e' + tmp_out.split('e')[-1]]
	
	return tmp_out

def get_lockin_r_theta(lockin):
	"""Get R and Theta. (Measure).

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS830

	returns:
		(tuple): R, Theta

	


	"""
	r, theta = lockin.query('SNAP? 3,4').split('\n')[0].split(',')
	r, theta = float(r), float(theta)
	return r, theta

def set_harmonic(lockin, harmonic_number = 1):
	"""Set detection harmonic.

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS830
		harmonic_number (int): Specify harmonic. 


	"""
	lockin.write("harm{}".format(harmonic_number))
	return

def auto_gain(lockin):
	"""Autogain.

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS830


	"""
	lockin.write("agan")
	return

def set_time_constant(lockin, time_constant):
	"""Set time constant.

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS830
		time_constant (str): Time constant. allowed time_constant: ['10us', '30us', '100us', '300us', '1ms', '3ms', '10ms', '30ms', '100ms', '300ms', '1s', '3s', '10s', '30s', '100s', '300s', '1ks', '3ks', '10ks', '30ks']



	
	"""
	if time_constant not in set(time_constant_to_index_mapper.keys()):
		raise KeyError("time_constant {} not allowed. allowed constants are {}".format(time_constant, time_constant_to_index_mapper.keys()))
	lockin.write("oflt{}".format(time_constant_to_index_mapper[time_constant]))
	
	#check to ensure it worked
	if get_time_constant(lockin) != time_constant:
		raise ValueError("set_time_constant failed")
	return

def get_time_constant(lockin):
	"""Get the current time constant.

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS830

	returns:
		(str): Time constant.


	"""
	return index_to_time_constant_mapper[int(lockin.query("oflt?").split('\n')[0])]

def get_reference_source(lockin):
	"""Get the reference source. Return either internal (1) or external (0).

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS830

	returns:
		(int): 1 for internal, 0 for external.


	"""
	return int(lockin.query("fmod?").split('\n')[0])

def set_reference_source(lockin, source):
	"""Set the reference source to interal or external.

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS830
		source (int or str): 1, 'internal' or 0, 'external'

	examples:
		```
		>>> set_reference_source(lockin, 1), set_reference_source(lockin, 'internal')
		```



	"""
	if type(source) == str:
		source = source.lower()
		assert source == 'internal' or source == 'external', "soure is not 'internal' or 'external'. provided: {}".format(source)
		if source == 'internal':
			lockin.write("fmod 1")
		if source == 'external':
			lockin.write("fmod 0")
	elif type(source) == int:
		assert source == 1 or source == 0, "if providing an int, must be 1 (internal) or 0 (external)"
		lockin.write("fmod {}".format(source))
	else:
		raise ValueError('cannot set reference source. source {} not understood'.format(source))
	return

def set_internal_frequency(lockin, frequency):
	"""Set the internal frequency output of the lockin.

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS830
		frequency (str or float): Frequency. allowed suffix are khz or hz if using str. limits on srs830 are .001<f<10200


	"""

	if type(frequency) == str:
		number, suffix = misc._get_number_and_suffix(frequency.lower())
		frequency = float('{}{}'.format(number, misc.freq_mapper[suffix]))
	else:
		frequency = float(frequency)

	lockin.write("freq {}".format(frequency))
	return

def set_internal_amplitude(lockin, amplitude):
	"""Set the internal amplitude output of the lockin.

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS 830
		amplitude (str or float): Amplitude. Allowed suffix are 'mv' or 'v' if using str. Limits on srs830 are .004<v<5



	"""

	if type(amplitude) == str:
		number, suffix = misc._get_number_and_suffix(amplitude.lower())
		amplitude = float('{}{}'.format(number, misc.voltage_amp_mapper[suffix]))
	else:
		amplitude = float(amplitude)

	lockin.write("slvl {}".format(amplitude))
	return

def set_sensitivity(lockin, sensitivity):
	"""Set sensitivity of lockin. 

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS 830
		sensitivity ('str'): Sensitivity. Allowed are '2nv/fa','5nv/fa','10nv/fa','20nv/fa','50nv/fa','100nv/fa':,'200nv/fa','500nv/fa','1uv/pa','2uv/pa','5uv/pa','10uv/pa':,'20uv/pa','50uv/pa','100uv/pa','200uv/pa','500uv/pa','1mv/na','2mv/na','5mv/na','10mv/na','20mv/na','50mv/na','100mv/na','200mv/na','500mv/na','1v/ua'


	"""
	sensitivity = sensitivity.lower()
	if sensitivity not in set(sensitivity_to_index_mapper.keys()):
		raise KeyError("sensitivity {} not allowed".format(sensitivity))

	lockin.write("sens {}".format(sensitivity_to_index_mapper[sensitivity]))

	#check to ensure it worked
	if get_sensitivity(lockin) != sensitivity:
		raise ValueError("set_sensitivity failed.")
	return

def get_sensitivity(lockin):
	"""Get sensitivity.

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS 830

	returns:
		(str): Sensitivity.


	"""
	return index_to_sensitivity_mapper[int(lockin.query("sens?").split('\n')[0])]
