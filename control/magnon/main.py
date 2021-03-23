import pyvisa
import pandas as pd
import numpy as np
import warnings
import time

from ..instruments import srs830 as srs
from ..instruments import keithley6221 as k6221
from ..instruments import misc
from .. import core

__all__ = ('determine_time_constant_from_frequency', 'Magnon', 'magnon_run_function')


def get_time_constant_float(time_constant):
	"""return a float of time_constant"""
	try:
		out = time_constant.replace('s','')
		out.replace('u', 'e-6')
		out.replace('m', 'e-3')
		out.replace('k', 'e3')
		return float(out)
	except:
		raise TypeError('unable to convert {} to float. allowed suffixes are us, ms, s, ks'.time_constant)

def determine_time_constant_from_frequency(frequency, multiplier = 3):
	"""gets the time constant from the frequency
	----
	frequency: (str) e.g. 47hz
	multiplier: (int) what to multiply 1/frequency by to get the time_constant
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


def initialize_lockin(lockin, trigger, harmonic, time_constant, frequency = None, amplitude = None,):
	"""initialize lockin (srs 830) 
	----
	lockin: (pyvisa.resources.gpib.GPIBInstrument) SRS830
	trigger: (str) 'internal' or 'external'
	harmonic: (int) which harmonic
	time_constant: (str) srs time constant
	frequency: (str) if internal triggering, must supply frequency and amplitude
	amplitude: (str) in voltage; if internal triggering, must supply frequency and amplitude
	"""
	trigger = trigger.lower()
	assert trigger == 'internal' or trigger == 'external', 'Trigger: {} not allowed. Must me "internal" or "external"'.format(trigger)

	if trigger == 'internal' and (type(frequency) == type(None) or type(amplitude) == type(None)):
		raise ValueError('must supply a frequency if internal triggering. currently supplied None')
	
	#initialize
	srs.set_reference_source(lockin, trigger)
	srs.set_time_constant(lockin, time_constant)

	srs.set_harmonic(lockin, harmonic)
	return 

def source_on(frequency, amplitude, lockin=None, current_source=None):
	"""turn on the source. if lockin is supplied, will turn on lockin output. if current_source is supplied, will turn on current source"""
	if type(lockin) != type(None) and type(current_source) != type(None):
		raise ValueError('must supply either a lockin or current_source, not both')

	if lockin == None and current_source == None:
		raise ValueError('must supply either a lock or current_source')

	if lockin != None:
		#turn on the lockin
		if amplitude.replace('v', '') == amplitude:
			raise ValueError('supply a voltage for amplitude if using lockin. cannot interpret {}'.format(amplitude))
		srs.set_internal_amplitude(lockin, amplitude)
		srs.set_internal_frequency(lockin, frequency)

	else:
		#turn on the current source
		if amplitude.replace('a', '') == amplitude:
			raise ValueError('supply a current for amplitude if using current source cannot interpret{}'.format(amplitude))
		k6221.set_wave_on(current_source)


	return

def set_lockin_sensitivity(lockin, sensitivity='default', sleep_time = 10):
	"""set the sensitivity on the lockin. 'default' will auto-gain the lockin
	----
	sensitivity: (str) sensitivity to set. default will auto-gain
	sleep_time: (int or float) time to sleep to let the lockin stabilize
	"""
	time.sleep(sleep_time)

	if sensitivity == 'default':
		#autogain the lockin
		srs.auto_gain(lockin)

		#wait for the autogain to progress
		time.sleep(10)
	else:
		srs.set_sensitivity(lockin, sensitivity)
		time.sleep(sleep_time)
	return

def magnon_run_function(lockin, harmonic, frequency, amplitude, current_source=False, 
	identifier='D', angle=0, channel_width=0, bar_width=0, channel_length=0, nave=100, 
	delay='default', time_constant='default', sensitivity='default'):
	"""
	run function for magnon (nonlocal) experiment.

	can be used with control.core.trial()

	returns: basename (str), meta_data (dict), data (pandas.dataframe)
	----
	lockin: (pyvisa.resources.gpib.GPIBInstrument)
	harmonic: (int) which harmonic to measure
	frequency: (str) e.g. 1khz
	amplitude in volts or amps: (str) e.g. 1v, 100ua
	current_source:(False or pyvisa.resources.gpib.GPIBInstrument) - if none provided, will use the lockin alone (internal reference)
	identifer: (str) e.g. D1
	angle: (int) e.g. 45
	nave: (int) how many averages to do
	delay: (float) delay time between averages default is 3xdelay 
	time_constant: (str) default will be 10 x 1/frequency (or cieling nearest allowed lockin timeconstant)
	sensitivity: (str) default will autogain the lockin
	"""
	#set up the basename and meta_data
	basename = '{}_{}_{}_{}_{}_{}_{}_{}_{}'.format(
		identifier, frequency, amplitude, harmonic, angle, nave, channel_width, bar_width, channel_length
		).replace('.', 'x').lower()
	
	#set up the lockin time constant
	if time_constant == 'default':
		time_constant = determine_time_constant_from_frequency(frequency, multiplier = 10) #by default

	#get the sleep time 10*time_constant
	if delay == 'default':
		sleep_time = 3*get_time_constant_float(time_constant)
	else:
		sleep_time = delay

	basename += '_{}_{}'.format(time_constant, sleep_time)

	meta_data = {
		'frequency':frequency,
		'amplitude':amplitude,
		'harmonic':harmonic,
		'nave':nave,
		'delay':sleep_time,
		'time_constant':time_constant,
		'angle':angle,
		'channel_width':channel_width,
		'channel_length':channel_length,
		'bar_width':bar_width,
		'identifier':identifier
	}

	if current_source == False:
		trigger = 'internal'

		#for source_on
		current_source_to_source_on = None
		lockin_to_source_on = lockin
	else:
		trigger = 'external'

		#set up the current source
		k6221.restore(current_source)
		k6221.set_output_sin(current_source,frequency,amplitude)

		#for source_on
		lockin_to_source_on = None
		current_source_to_source_on = current_source

	#configure run
	initialize_lockin(lockin, trigger, harmonic, time_constant, frequency = frequency, amplitude = amplitude)

	#start the source (either current or lockin)
	source_on(frequency, amplitude, lockin_to_source_on, current_source_to_source_on)

	#set_lockin_sensitivity. must come after the source on
	set_lockin_sensitivity(lockin, sensitivity, sleep_time)

	#do the measurement
	rs, thetas = [], []
	for i in range(nave):
		time.sleep(sleep_time)
		r, theta = srs.get_lockin_r_theta(lockin)
		rs.append(r)
		thetas.append(theta)
	out = pd.DataFrame({'R':rs, 'theta':thetas})

	meta_data.update({'sensitivity': srs.get_sensitivity(lockin)})
	return basename, meta_data, out


class Magnon(core.experiment):
	"""need docstring"""

	def __init__(self, lockin, current_source=None, run_function=magnon_run_function):
		super().__init__()
		self.run_function = run_function
		self.lockin = lockin
		self.current_source = current_source
		return

	def checks(self, params):
		"""to be checked by """
		try:
			if self.current_source != None and (params['current_source'] != self.current_source):
				raise ValueError('current_source provided in initialization ({}) does not match that provided as an argument for run_function ({})'.format(self.current_source, params['current_source']))
		except KeyError:
			raise ValueError('current_source provided in initialization ({}) does not match that provided as an argument for run_function ({})'.format(self.current_source, None))
		if self.lockin != params['lockin']:
			try:
				raise ValueError('lockin provided in initialization ({}) does not match that provided as an argument for run_function ({})'.format(self.lockin, params['lockin']))

			except KeyError:
				raise ValueError('lockin provided in initialization ({}) does not match that provided as an argument for run_function ({})'.format(self.lockin, None))

	def terminate(self):
		"""turn off the current source"""
		if self.current_source != None:
			k6221.set_wave_off(self.current_source)
		srs.set_reference_source(self.lockin, 'external')
		srs.set_internal_amplitude(self.lockin, '5mv')
		return

#deprecated below

def nonlocal_run_function_lockin_only(lockin, frequency, amplitude, harmonic, identifier='D', angle=0, 
	channel_width = 0, bar_width = 0, channel_length = 0, nave = 100, delay = 'default', time_constant = 'default', 
	sensitivity = 'default', test = False):
	"""need docstring. default time constant will be closest to 3x 1/frequency

	can be used with control.core.trial()

	returns: basename (str), meta_data (dict), data (pandas.dataframe)

	----
	lockin: (pyvisa.resources.gpib.GPIBInstrument)
	current_source:(pyvisa.resources.gpib.GPIBInstrument)
	frequency: (str) e.g. 1khz
	amplitude IN VOLTS: (str) e.g. 1v
	harmonic: (int) e.g. 1
	identifer: (str) e.g. D1
	angle: (int) e.g. 45
	nave: (int) how many averages to do
	delay: (float) delay time between averages default is 3xdelay 
	time_constant: (str) default will be 10 x 1/frequency (or cieling nearest allowed lockin timeconstant)
	sensitivity: (str) default will autogain the lockin. 
	"""
	warnings.showwarning('nonlocal_run_function_lockin_only() is deprecated please use .summary', DeprecationWarning, '', 0,)
	#set up the basename and meta_data
	basename = '{}_{}_{}_{}_{}_{}_{}_{}_{}'.format(
		identifier, frequency, amplitude, harmonic, angle, nave, channel_width, bar_width, channel_length
		).replace('.', 'x').lower()
	
	#set up the lockin time constant
	if time_constant == 'default':
		time_constant = determine_time_constant_from_frequency(frequency, multiplier = 10) #by default

	#get the sleep time 10*time_constant
	if delay == 'default':
		sleep_time = 3*get_time_constant_float(time_constant)
	else:
		sleep_time = delay

	basename += '_{}_{}'.format(time_constant, sleep_time)

	meta_data = {
		'frequency':frequency,
		'amplitude':amplitude,
		'harmonic':harmonic,
		'nave':nave,
		'delay':sleep_time,
		'time_constant':time_constant,
		'angle':angle,
		'channel_width':channel_width,
		'channel_length':channel_length,
		'bar_width':bar_width,
		'identifier':identifier
	}
	if not test:
		
		#configure lockin
		srs.set_reference_source(lockin, 'internal')
		srs.set_time_constant(lockin, time_constant)
		srs.set_harmonic(lockin, harmonic)
		srs.set_internal_amplitude(lockin, amplitude)
		srs.set_internal_frequency(lockin, frequency)
		
		time.sleep(sleep_time)

		if sensitivity == 'default':
			#autogain the lockin
			srs.auto_gain(lockin)
			#wait for the autogain to progress
			time.sleep(10)
		else:
			srs.set_sensitivity(lockin, sensitivity)
			time.sleep(sleep_time)

		
		#do the measurement
		rs, thetas = [], []
		for i in range(nave):
			time.sleep(sleep_time)
			r, theta = srs.get_lockin_r_theta(lockin)
			rs.append(r)
			thetas.append(theta)
		out = pd.DataFrame({'R':rs, 'theta':thetas})

		meta_data.update({'sensitivity': srs.get_sensitivity(lockin)})
	
	else: #for testing
		out = pd.DataFrame({'R':[1,2,3], 'theta':[1,2,3]})

	return basename, meta_data, out


def nonlocal_run_function(lockin, current_source, frequency, amplitude, harmonic, identifier='D', angle=0, 
	channel_width = 0, bar_width = 0, channel_length = 0, nave = 100, delay = .5, time_constant = 'default', test = False):
	"""need docstring. default time constant will be closest to 3x 1/frequency

	can be used with control.core.trial()

	returns: basename (str), meta_data (dict), data (pandas.dataframe)

	----
	lockin: (pyvisa.resources.gpib.GPIBInstrument)
	current_source:(pyvisa.resources.gpib.GPIBInstrument)
	frequency: (str) e.g. 1khz
	amplitude: (str) e.g. 80ua
	harmonic: (int) e.g. 1
	identifer: (str) e.g. D1
	angle: (int) e.g. 45
	nave: (int) how many averages to do
	delay: (float) delay time between averages
	time_constant: (str) default will be 3 x 1/frequency (or cieling nearest allowed lockin timeconstant)
	"""
	warnings.showwarning('nonlocal_run_function() is deprecated please use .summary', DeprecationWarning, '', 0,)
	#set up the basename and meta_data
	basename = '{}_{}_{}_{}_{}_{}_{}_{}_{}_{}'.format(
		identifier, frequency, amplitude, harmonic, angle, nave, delay, channel_width, bar_width, channel_length
		).replace('.', 'x').lower()

	if not test:
		#set up the current source
		k6221.restore(current_source)
		k6221.set_output_sin(current_source,frequency,amplitude)
	
	#set up the lockin
	if time_constant == 'default':
		time_constant = determine_time_constant_from_frequency(frequency, multiplier = 10)

	basename += '_{}'.format(time_constant)

	meta_data = {
		'frequency':frequency,
		'amplitude':amplitude,
		'harmonic':harmonic,
		'nave':nave,
		'delay':delay,
		'time_constant':time_constant,
		'angle':angle,
		'channel_width':channel_width,
		'channel_length':channel_length,
		'bar_width':bar_width,
		'identifier':identifier
	}
	if not test:
		
		srs.set_time_constant(lockin, time_constant)

		srs.set_harmonic(lockin, harmonic)
		
		#start the current source
		k6221.set_wave_on(current_source)
		time.sleep(5)
		
		#autogain the lockin
		srs.auto_gain(lockin)
		
		#wait for the autogain to progress
		time.sleep(5)
		
		#do the measurement
		rs, thetas = [], []
		for i in range(nave):
			time.sleep(delay)
			r, theta = srs.get_lockin_r_theta(lockin)
			rs.append(r)
			thetas.append(theta)
		out = pd.DataFrame({'R':rs, 'theta':thetas})
	else:
		out = pd.DataFrame({'R':[1,2,3], 'theta':[1,2,3]})

	return basename, meta_data, out