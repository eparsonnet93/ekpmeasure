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


def _source_on(frequency, amplitude, lockin=None, current_source=None):
	"""Turn on the source. If lockin is supplied, will turn on lockin output. If current_source is supplied, will turn on current source.

	args:
		frequency (str): Frequency
		amplitude (str): Amplitude
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS 830
		current_source (pyvisa.resources.gpib.GPIBInstrument): Keithley6221



	"""
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
	Run function for Magnon (nonlocal) experiment. 

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS830
		harmonic (int): Harmonic for lockin.
		frequency (str): Frequency.
		amplitude (str): Amplitude.
		current_source (pyvisa.resources.gpib.GPIBInstrument): Keithley6221. If none provided will use lockin alone (internal reference)
		identifier (str): Unique identifier 
		angle (int): Angle of device
		nave (int): Number of averages to perform
		delay (float): Delay time between averages. Default is 3 x delay.
		time_constant (str): Lockin time constant. Default is 10 x 1/frequency (or cieling of nearest alled lockin time constant).
		sensitivity (str): Sensitiviy of locking. Default is autogain.
		phase (str): Lockin phase
		compliance (float): Current source compliance


	returns:
		basename (str): Basename of file for saving.
		meta_data (pandas.DataFrame): Meta data associated with run. 
		data (pandas.DataFrame): Data of run.





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
	_source_on(frequency, amplitude, lockin_to_source_on, current_source_to_source_on)

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
	"""Magnon experiment.

	args:
		lockin (pyvisa.resources.gpib.GPIBInstrument): SRS830
		current_source (pyvisa.resources.gpib.GPIBInstrument): Keithley6221
		run_function (function): Run function. 


	"""

	def __init__(self, lockin, current_source=None, run_function=magnon_run_function):
		super().__init__()
		self.run_function = run_function
		self.lockin = lockin
		self.current_source = current_source
		return

	def checks(self, params):
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
		#turn off current source
		if self.current_source != None:
			k6221.set_wave_off(self.current_source)
		srs.set_reference_source(self.lockin, 'external')
		srs.set_internal_amplitude(self.lockin, '5mv')
		return