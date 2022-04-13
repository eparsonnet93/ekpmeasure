from ...control import plotting, core
from ...control.instruments import srs830 as srs
from ...control.instruments import keithley6221 as k6221
from ...control.instruments import keithley2400 as k2400

import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
import time

__all__ = ('basic_run_function', 'BASIC', 'hysteresis_run_function', 'HYST', 'SWITCH', 'switching_run_function', 'BASIC_SINGLE_LI')

def switching_run_function(LI1, current_source, k24, samplename, LI2:'pyvisa.resources.gpib.GPIBInstrument'=None, min_voltage:float=-10, 
	max_voltage:float=10, current_amplitude:str='800ua', nplc:float=0.2, current_frequency:str='7hz', current_compliance:float=4, 
	ntimes:int=2, wait_time:float=.5,ignore:int=100,count:int=500,sleep_before_start:float=60,note:str='none', plot:bool=True, 
	fig=None, axs=None, harmonic:int=2):
	meta_data = {
		'min_voltage':min_voltage,
		'max_voltage':max_voltage,
		'current_amplitude':current_amplitude,
		'current_frequency':current_frequency,
		'current_compliance':current_compliance,
		'wait_time':wait_time,
		'ntimes':ntimes,
		'ignore':ignore,
		'count':count,
		'sleep_before_start':sleep_before_start,
		'note':note
	}
	if LI1 is None and LI2 is None:
		raise ValueError('Must provide a lockin')

	single_lockin = False

	if LI2 is None:
		single_lockin = True
		meta_data.update({'harmonic':harmonic})
	else:
		meta_data.update({'harmonic':12})

	meta_data.update({'single_lockin':single_lockin})

	if LI1 is None:
		raise ValueError('If using a single lockin, it must be LI1, not NoneType.')

	base_name = 'switching{}_{}'.format(str(min_voltage).replace('-','n').replace('+',''), str(max_voltage).replace('-','n').replace('+',''))

	out = {'V':[],'X1':[],'Y1':[],'X2':[],'Y2':[]}

	k6221.set_output_sin(current_source, frequency=current_frequency, 
		amplitude=current_amplitude, compliance=current_compliance)

	if not single_lockin:
		srs.set_harmonic(LI1, 1)
		srs.set_harmonic(LI2, 2)
	else:
		srs.set_harmonic(LI1, harmonic)

	# get voltages:
	voltages = []
	for i in range(ntimes):
		voltages.append(min_voltage)
		voltages.append(max_voltage)

	for voltage in voltages:
		# apply pulse
		print('Voltage', voltage)
		k6221.set_wave_off(current_source)
		if voltage != 0:
			time.sleep(1)
			#input('Connect')
			k2400.config_voltage_pulse(k24, amplitude=voltage, nplc=nplc)
			k2400.enable_source(k24)
			time.sleep(2)
			k2400.read(k24)
			time.sleep(1)
			#input('Disconnect')
		k6221.set_wave_on(current_source)
		time.sleep(sleep_before_start)

		for i in range(count):
			time.sleep(wait_time)
			if i <= ignore:
				continue
			if single_lockin:
				X, Y = srs.get_X_Y(LI1)
				out['X1'].append(X)
				out['Y1'].append(Y)
				out['X2'].append(X)
				out['Y2'].append(Y)
				out['V'].append(voltage)
			else:
				X1, Y1 = srs.get_X_Y(LI1)
				X2, Y2 = srs.get_X_Y(LI2)
				out['X1'].append(X1)
				out['Y1'].append(Y1)
				out['X2'].append(X2)
				out['Y2'].append(Y2)
				out['V'].append(voltage)

		if plot:
			for key, ax in zip(['X1', 'Y1', 'X2', 'Y2'], axs):
				ax.plot(out[key], color='blue', marker='o')
				plotting.update_plot(fig)
				plt.show(fig)

	return base_name, meta_data, pd.DataFrame(out)

def hysteresis_run_function(LI1, LI2, current_source, k24, samplename, min_voltage:float=-10, max_voltage:float=10,
	nsteps:int=5, current_amplitude:str='800ua', current_frequency:str='7hz', current_compliance:float=4,
	wait_time:float=.5,ignore:int=100,count:int=500,sleep_before_start:float=60,note:str='none', plot:bool=True, 
	fig=None, axs=None):
	meta_data = {
		'min_voltage':min_voltage,
		'max_voltage':max_voltage,
		'nsteps':nsteps,
		'current_amplitude':current_amplitude,
		'current_frequency':current_frequency,
		'current_compliance':current_compliance,
		'wait_time':wait_time,
		'ignore':ignore,
		'count':count,
		'sleep_before_start':sleep_before_start,
		'note':note
	}

	base_name = 'hyst{}_{}'.format(str(min_voltage).replace('-','n').replace('+',''), str(max_voltage).replace('-','n').replace('+',''))

	out = out = {'V':[],'X1':[],'Y1':[],'X2':[],'Y2':[],
	'X1_err':[],'Y1_err':[],'X2_err':[],'Y2_err':[]}

	k6221.set_output_sin(current_source, frequency=current_frequency, 
		amplitude=current_amplitude, compliance=current_compliance)

	# get voltages:
	voltages = np.round(np.linspace(min_voltage, max_voltage, nsteps), 2)
	voltages = np.concatenate((voltages[:-1], voltages[::-1]))

	for voltage in voltages:
		# apply pulse
		print('Voltage', voltage)
		k6221.set_wave_off(current_source)
		if voltage != 0:
			time.sleep(1)
			#input('Connect')
			k2400.config_voltage_pulse(k24, amplitude=voltage)
			k2400.enable_source(k24)
			time.sleep(2)
			k2400.read(k24)
			time.sleep(1)
			#input('Disconnect')
		k6221.set_wave_on(current_source)
		time.sleep(sleep_before_start)

		internal_out = {'X1':[],'Y1':[],'X2':[],'Y2':[]}

		for i in range(count):
			time.sleep(wait_time)
			if i <= ignore:
				continue
			X1, Y1 = srs.get_X_Y(LI1)
			X2, Y2 = srs.get_X_Y(LI2)
			internal_out['X1'].append(X1)
			internal_out['Y1'].append(Y1)
			internal_out['X2'].append(X2)
			internal_out['Y2'].append(Y2)

		out['V'].append(voltage)
		out['X1'].append(np.mean(internal_out['X1']))
		out['Y1'].append(np.mean(internal_out['Y1']))
		out['X2'].append(np.mean(internal_out['X2']))
		out['Y2'].append(np.mean(internal_out['Y2']))
		out['X1_err'].append(np.std(internal_out['X1']))
		out['Y1_err'].append(np.std(internal_out['Y1']))
		out['X2_err'].append(np.std(internal_out['X2']))
		out['Y2_err'].append(np.std(internal_out['Y2']))
		if plot:
			for key, ax in zip(['X1', 'Y1', 'X2', 'Y2'], axs):
				ax.errorbar(voltage, np.mean(internal_out[key]), np.std(internal_out[key]),
					color='blue', marker='o')
				plotting.update_plot(fig)
				plt.show(fig)

	return base_name, meta_data, pd.DataFrame(out)


def basic_run_function(LI1, LI2, current_source, FE_applied_voltage, samplename, 
	current_amplitude, current_frequency='7hz', current_compliance=4, wait_time=.5, 
	ignore=100, count=500, sleep_before_start=60, note='none',hysteresis=False):

	if hysteresis:
		input('Click enter after applied voltage ({}).'.format(FE_applied_voltage))
	
	meta_data = {
		'FE_applied_voltage':FE_applied_voltage,
		'samplename':samplename,
		'wait_time':wait_time,
		'count':count,
		'current_amp_ua':float(current_amplitude.replace('ua','').replace('ma','1e3')),
		'current_frequency':current_frequency,
		'note':note,
	}
	
	base_name = '{}v_'.format(str(FE_applied_voltage).replace('-', 'n').replace('.', 'x'))
	
	out = {'X1':[],'Y1':[],'X2':[],'Y2':[]}

	if not k6221.is_on(current_source):
		k6221.set_output_sin(current_source, frequency=current_frequency, 
			amplitude=current_amplitude, compliance=current_compliance)
		k6221.set_wave_on(current_source)
		time.sleep(sleep_before_start)
	time.sleep(sleep_before_start/2)
	
	for i in range(count):
		time.sleep(wait_time)
		if i <= ignore:
			continue
		X1, Y1 = srs.get_X_Y(LI1)
		X2, Y2 = srs.get_X_Y(LI2)
		out['X1'].append(X1)
		out['Y1'].append(Y1)
		out['X2'].append(X2)
		out['Y2'].append(Y2)

	if not hysteresis:
		k6221.set_wave_off(current_source)
		
	return base_name, meta_data, pd.DataFrame(out)

def basic_run_function_single_lockin(LI, current_source, FE_applied_voltage, samplename, 
	current_amplitude, current_frequency='7hz', current_compliance=4, wait_time=.5, 
	ignore=100, count=500, sleep_before_start=60, note='none',hysteresis=False):

	if hysteresis:
		input('Click enter after applied voltage ({}).'.format(FE_applied_voltage))
	
	meta_data = {
		'FE_applied_voltage':FE_applied_voltage,
		'samplename':samplename,
		'wait_time':wait_time,
		'count':count,
		'current_amp_ua':float(current_amplitude.replace('ua','').replace('ma','1e3')),
		'current_frequency':current_frequency,
		'note':note,
	}
	
	base_name = '{}v_'.format(str(FE_applied_voltage).replace('-', 'n').replace('.', 'x'))
	
	out = {'X':[],'Y':[]}

	if not k6221.is_on(current_source):
		k6221.set_output_sin(current_source, frequency=current_frequency, 
			amplitude=current_amplitude, compliance=current_compliance)
		k6221.set_wave_on(current_source)
		time.sleep(sleep_before_start)
	time.sleep(sleep_before_start/2)
	
	for i in range(count):
		# import pdb; pdb.set_trace()
		time.sleep(wait_time)
		if i <= ignore:
			continue
		X, Y = srs.get_X_Y(LI)
		out['X'].append(X)
		out['Y'].append(Y)

	if not hysteresis:
		k6221.set_wave_off(current_source)
		
	return base_name, meta_data, pd.DataFrame(out)


class BASIC_SINGLE_LI(core.experiment):
	
	def __init__(self, LI, current_source, run_function=basic_run_function_single_lockin):
		super().__init__(run_function)
		# self.run_function = run_function
		self.LI = LI
		self.current_source = current_source
	
	def checks(self, params):
		if self.LI != params['LI']:
			raise ValueError('Lockin does not match self.')
		if self.current_source != params['current_source']:
			raise ValueError('current_source does not match self.')
	
	def terminate(self, *args, **kwargs):
		k6221.set_wave_off(self.current_source)

	def _plot(self, data, scan_params):
		if hasattr(self, 'fig') and hasattr(self, 'ax'):
			pass
		else:
			fig, axs = plt.subplots(nrows=2, figsize=(10,15))
			self.fig = fig
			self.axs = axs
			
		for ax, data_key in zip(self.axs, ['X', 'Y']):
			dat = data[data_key]
			ax.plot(dat, color = 'blue')
			ax.set_title(data_key)
			plotting.update_plot(self.fig)
			plt.show(self.fig)

class BASIC(core.experiment):
	
	def __init__(self, LI1, LI2, current_source, run_function = basic_run_function):
		super().__init__()
		self.run_function = run_function
		self.LI1 = LI1
		self.LI2 = LI2
		self.current_source = current_source
	
	def checks(self, params):
		if self.LI1 != params['LI1']:
			raise ValueError('Lockin 1 does not match self.')
		if self.LI2 != params['LI2']:
			raise ValueError('Lockin 2 does not match self.')
		if self.current_source != params['current_source']:
			raise ValueError('current_source does not match self.')
	
	def terminate(self, *args, **kwargs):
		k6221.set_wave_off(self.current_source)

	def _plot(self, data, scan_params):
		if hasattr(self, 'fig') and hasattr(self, 'ax'):
			pass
		else:
			fig, axs = plt.subplots(nrows=4, figsize=(10,15))
			self.fig = fig
			self.axs = axs
			
		for ax, data_key in zip(self.axs, ['X1', 'Y1', 'X2', 'Y2']):
			dat = data[data_key]
			ax.plot(dat, color = 'blue')
			ax.set_title(data_key)
			plotting.update_plot(self.fig)
			plt.show(self.fig)

class HYST(core.experiment):

	def __init__(self, LI1, LI2, current_source, k24, run_function = hysteresis_run_function):
		super().__init__()
		self.run_function = run_function
		self.LI1 = LI1
		self.LI2 = LI2
		self.k24 = k24
		self.current_source = current_source
	
	def checks(self, params):
		if self.LI1 != params['LI1']:
			raise ValueError('Lockin 1 does not match self.')
		if self.LI2 != params['LI2']:
			raise ValueError('Lockin 2 does not match self.')
		if self.current_source != params['current_source']:
			raise ValueError('current_source does not match self.')
		if self.k24 != params['k24']:
			raise ValueError('k24 does not match self.')
	
	def terminate(self, *args, **kwargs):
		k6221.set_wave_off(self.current_source)
		k2400.disable_source(self.k24)


class SWITCH(core.experiment):

	def __init__(self, LI1, LI2, current_source, k24, run_function=switching_run_function):
		super().__init__(run_function)
		self.LI1 = LI1
		self.LI2 = LI2
		self.current_source = current_source
		self.k24 = k24
	
	def checks(self, params):
		if self.LI1 != params['LI1']:
			raise ValueError('Lockin 1 does not match self.')
		if self.LI2 != params['LI2']:
			raise ValueError('Lockin 2 does not match self.')
		if self.current_source != params['current_source']:
			raise ValueError('current_source does not match self.')
		if self.k24 != params['k24']:
			raise ValueError('k24 does not match self.')
	
	def terminate(self, *args, **kwargs):
		k6221.set_wave_off(self.current_source)
		k2400.disable_source(self.k24)