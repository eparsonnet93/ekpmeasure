__all__ = ('get_lockin_r_theta','set_harmonic', 'set_time_constant', 'get_time_constant', 'auto_gain')

def get_lockin_r_theta(lockin):
	r, theta = lockin.query('SNAP? 3,4').split('\n')[0].split(',')
	r, theta = float(r), float(theta)
	return r, theta


time_constant_to_index_mapper = {
	'10us':0,'30us':1,'100us':2,'300us':3,'1ms':4,'3ms':5,'10ms':6,
	'30ms':7,'100ms':8,'300ms':9,'1s':10,'3s':12,'10s':12,'30s':13,
	'100s':14,'300s':15,'1ks':16,'3ks':17,'10ks':18,'30ks':19,
}

index_to_time_constant_mapper = {time_constant_to_index_mapper[key]:key for key in time_constant_to_index_mapper}

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