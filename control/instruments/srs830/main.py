from .. import misc

__all__ = (
	'get_lockin_r_theta','set_harmonic', 'set_time_constant', 'get_time_constant', 'auto_gain',
	'get_sensitivity', 'set_sensitivity', 'get_reference_source', 'set_reference_source',
	'set_internal_frequency', 'set_internal_amplitude'
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

def get_lockin_r_theta(lockin):
	r, theta = lockin.query('SNAP? 3,4').split('\n')[0].split(',')
	r, theta = float(r), float(theta)
	return r, theta

def set_harmonic(lockin, harmonic_number = 1):
	lockin.write("harm{}".format(harmonic_number))
	return

def auto_gain(lockin):
	"""autogain the srs830"""
	lockin.write("agan")
	return

def set_time_constant(lockin, time_constant):
	"""set time constant on srs830
	----
	allowed time_constant:
	['10us', '30us', '100us', '300us', '1ms', '3ms', '10ms', '30ms', '100ms', '300ms', '1s', '3s', '10s', '30s', '100s', '300s', '1ks', '3ks', '10ks', '30ks']
	"""
	if time_constant not in set(time_constant_to_index_mapper.keys()):
		raise KeyError("time_constant {} not allowed. allowed constants are {}".format(time_constant, time_constant_to_index_mapper.keys()))
	lockin.write("oflt{}".format(time_constant_to_index_mapper[time_constant]))
	
	#check to ensure it worked
	if get_time_constant(lockin) != time_constant:
		raise ValueError("set_time_constant failed")
	return

def get_time_constant(lockin):
	"""get the current time constant"""
	return index_to_time_constant_mapper[int(lockin.query("oflt?").split('\n')[0])]

def get_reference_source(lockin):
	"""return either internal (1) or external (0)"""
	return int(lockin.query("fmod?").split('\n')[0])

def set_reference_source(lockin, source):
	"""set the reference source to interal or external
	----
	source: (int or str) 1, 'internal' or 0, 'external'

	example: set_reference_source(lockin, 1), set_reference_source(lockin, 'internal')
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
	"""set the frequency output of the lockin
	----
	frequency: (str or float) allowed suffix are khz or hz if using str. limits on srs830 are .001<f<10200
	"""

	if type(frequency) == str:
		number, suffix = misc._get_number_and_suffix(frequency.lower())
		frequency = float('{}{}'.format(number, misc.freq_mapper[suffix]))
	else:
		frequency = float(frequency)

	lockin.write("freq {}".format(frequency))
	return

def set_internal_amplitude(lockin, amplitude):
	"""set the amplitude output of the lockin
	----
	amplitude: (str or float) allowed suffix are mv or v if using str. limits on srs830 are .004<v<5
	"""

	if type(amplitude) == str:
		number, suffix = misc._get_number_and_suffix(amplitude.lower())
		amplitude = float('{}{}'.format(number, misc.voltage_amp_mapper[suffix]))
	else:
		amplitude = float(amplitude)

	lockin.write("slvl {}".format(amplitude))
	return

def set_sensitivity(lockin, sensitivity):
	"""set sensitivity of lockin. 
	----
	sensitivity: (str) allowed are '2nv/fa','5nv/fa','10nv/fa','20nv/fa','50nv/fa','100nv/fa':,'200nv/fa','500nv/fa','1uv/pa','2uv/pa','5uv/pa','10uv/pa':,'20uv/pa','50uv/pa','100uv/pa','200uv/pa','500uv/pa','1mv/na','2mv/na','5mv/na','10mv/na','20mv/na','50mv/na','100mv/na','200mv/na','500mv/na','1v/ua'
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
	"""get the current time constant"""
	return index_to_sensitivity_mapper[int(lockin.query("sens?").split('\n')[0])]
