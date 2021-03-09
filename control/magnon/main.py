import pyvisa
import pandas as pd
import numpy as np
import warnings
import time

from ..instruments import srs830 as srs
from ..instruments import keithley6221 as k6221
from ..instruments import misc

__all__ = ('nonlocal_run_function', 'determine_time_constant_from_frequency')

def nonlocal_run_function(lockin, current_source, frequency, amplitude, harmonic, identifier='D', angle=0, nave = 100, delay = .5, time_constant = 'default', test = False):
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
	#set up the basename and meta_data
	basename = '{}_{}_{}_{}_{}_{}_{}'.format(identifier, frequency, amplitude, harmonic, angle, nave, delay).replace('.', 'x').lower()

	if not test:
		#set up the current source
		k6221.restore(current_source)
		k6221.set_output_sin(current_source,frequency,amplitude)
	
	#set up the lockin
	if time_constant == 'default':
		time_constant = determine_time_constant_from_frequency(frequency)

	basename += '_{}'.format(time_constant)

	meta_data = {
		'frequency':frequency,
		'amplitude':amplitude,
		'harmonic':harmonic,
		'nave':nave,
		'delay':delay,
		'time_constant':time_constant,
		'angle':angle,
		'identifier':identifier
	}
	if not test:
		srs.set_time_constant(lockin, time_constant)
		srs.set_harmonic(lockin, harmonic)
		
		#start the current source
		k6221.set_wave_on(current_source)
		
		#autogain the lockin
		srs.auto_gain(lockin)
		
		#wait for the autogain to progress
		time.sleep(3)
		
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