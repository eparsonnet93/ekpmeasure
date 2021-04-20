import pyvisa
import pandas as pd
import numpy as np
import warnings
import time

from ..instruments import srs830 as srs
from ..instruments import keithley6221 as k6221
from ..instruments import misc
from .. import core

__all__ = ('Magnon', 'magnon_run_function')


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

def magnon_run_function(lockin, harmonic, frequency, amplitude, current_source=False, 
	identifier='D', angle=0, channel_width=0, bar_width=0, channel_length=0, nave=100, 
	delay='default', time_constant='default', sensitivity='default',phase=None,compliance=1.1):
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
		time_constant = srs.get_time_constant_from_frequency(frequency, multiplier = 10) #by default

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
		'identifier':identifier,
		"phase":phase
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
		k6221.set_output_sin(current_source,frequency,amplitude, compliance = compliance)

		#for source_on
		lockin_to_source_on = None
		current_source_to_source_on = current_source

	#configure run
	srs.initialize_lockin(lockin, trigger, harmonic, time_constant, frequency = frequency, amplitude = amplitude)
	srs.set_phase(lockin, phase)

	#start the source (either current or lockin)
	source_on(frequency, amplitude, lockin_to_source_on, current_source_to_source_on)

	#set_lockin_sensitivity. must come after the source on
	srs.set_lockin_sensitivity(lockin, sensitivity, sleep_time)

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