from ..instruments.berkeleynucleonics765 import *
from ..instruments.tektronixTDS620B import get_wf_from_scope as tds620B_get_wf
from ..misc import get_save_name
import pandas as pd
import numpy as np
import os 

import time

__all__ = ('run_pund', 'apply_preset_pulse', 'run_preset_then_2pusle_TDS620B', 'trial')

def run_pund(inst, up, down, up_first = False, wait_time = 1, channel = '1'):
	"""
	runs a pund for a given up and down SCPI sequence. This operates by applying single pulses only and using python for timing. This is not recommended for accurate timing. 
	----
	inst: (pyvisa.resources.gpib.GPIBInstrument)
	up: (SCPI str) defines up pulse parameters
	down: (SCPI_str) defines down pulse parameters

	options:
	----
	up_first: (bool) choose preset polarity. other pulses will follow
	wait_time: (int, float) how long to wait between pulses, this is not exact
	channel: (str) select output channel
	"""
	import time
	
	initialize_for_pund(inst)
	time.sleep(wait_time)
	if up_first:
		sequence = [up, down, down, up,up]
	else:
		sequence = [down, up, up, down, down]
	inst.write('outp'+channel+':stat off')
	for i, s in enumerate(sequence):
		inst.write(s)
		time.sleep(wait_time/2)
		inst.write('outp'+channel+':stat on')
		time.sleep(wait_time/4)
		inst.write('trig:seq:imm') #execute
		time.sleep(wait_time/4)
		inst.write('outp'+channel+':stat off')
	
	inst.write('pulsegenc:stop')
	
	return 

def apply_preset_pulse(pg, pulsewidth, amplitude, channel = '1', wait_time = 1,  *args, **kwargs):
	"""
	apply a preset pulse and then ready for next pulse sequency by leaving the pulsegen at reset values (+-50mV). 
	Preset is always negative 
	----
	pg: (pyvisa.resources.gpib.GPIBInstrument) BN765
	pulsewidth: (str) allowed units {ns, us, ms, s}
	ampitude: (str) allowed units {mv, v}

	"""
	#initialization
	initialize_pulse(pg, channel = channel)

	#only need down (second output argument) of the following line. todo: refactor
	up, down = symmetric_up_down_SCPI(pulsewidth = pulsewidth, 
										 amplitude = amplitude,
										 offset = '0v',
										 channel=channel,
										 *args, **kwargs)
	
	time.sleep(wait_time)
	pg.write('outp'+channel+':stat off')
	
	 #need this to reset to ranges otherwise get an error out of range
	reset = ':sour1:volt:lev:imm:high 50mv;:sour1:volt:lev:imm:low -50mv;'
	pg.write(reset)
	time.sleep(wait_time)
	pg.write( down)
	time.sleep(wait_time)
	pg.write('outp'+channel+':stat on')
	time.sleep(wait_time)
	manual_trigger(pg) #execute
	time.sleep(wait_time)

	pg.write('outp'+channel+':stat off')
	pg.write(reset)
	time.sleep(wait_time)
	pg.write(reset + ':sour'+channel+':inv off;') #turn off inversion in case
	pg.write('pulsegenc:stop') 
	
	return 

def run_preset_then_2pusle_TDS620B(pg, scope, identifier, pulsewidth, delay, high_voltage, preset_pulsewidth = '100ns', preset_voltage = '3000mv',test=False):
	"""
	run a preset and then 2 pulse measurement using the BN765 and tektronix tds620B. This oscope is not preferred for the fastest timing measurements
	returns tuple((str) save_base_name,  (pandas.DataFrame) data)

	this function is supported in trial()

	save_base_name has format: PRESET2PULSE_identifier_pulsewidth_delay_highvoltage_presetvoltage_presetpulsewidth
	----
	identifier: (str) some indentifier for the capacitor or sample you are studying
	pg: (pyvisa.resources.gpib.GPIBInstrument) bn765
	scope: (pyvisa.resources.gpib.GPIBInstrument) tektronix tds620B
	delay: (str) example '10ns' delay between the two pulses (preset delay is set at approximately 1s)
	high_voltage: (str) example '100mV' allowed units are V and mv. this parameter sets the amplitude of the two pulse 
	preset_pulsewidth: (str) example '100ns' sets the pulsewidth of the preset
	preset_voltage: (str) example '10mv' sets the amplitude of the preset
	"""

	#get types correct
	try:
		float(pulsewidth)
	except ValueError:
		try:
			pw = pulsewidth.replace('ns', 'e-9').replace('us', 'e-6').replace('ms', 'e-3').replace('s','')
			float(pw)
			pulsewidth = pw
		except ValueError:
			raise ValueError('unable to interpret pulsewidth {}, interpreted as {}'.format(pulsewidth, pw))
	#now should have scientific notation format (str)

	try:
		float(delay)
	except ValueError:
		try:
			dlay = delay.replace('ns', 'e-9').replace('us', 'e-6').replace('ms', 'e-3').replace('s','')
			float(dlay)
			delay = dlay
		except ValueError:
			raise ValueError('unable to interpret delay {}, interpreted as {}'.format(delay, dlay))
	#now has scientific notation format (str)

	#fix high_voltage units
	if high_voltage[-2:].lower() not in set({'mv'}):
		if high_voltage[-1].lower() != 'v':
			raise ValueError('high_voltage ' + str(high_voltage) + ' not supported')

	try: 
		high_voltage = float(high_voltage[:-1])*1000
	except ValueError:
		#means mv is the unit
		high_voltage = float(high_voltage[:-2])
	high_voltage = str(high_voltage) + 'mv' #put it in consistent units (mV)
	#now has units of mv with 'mv' on end

	#fix preset_voltage units
	if preset_voltage[-2:].lower() not in set({'mv'}):
		if preset_voltage[-1].lower() != 'v':
			raise ValueError('preset_voltage ' + str(preset_voltage) + ' not supported')

	try: 
		preset_voltage = float(preset_voltage[:-1])*1000
	except ValueError:
		#means mv is the unit
		preset_voltage = float(preset_voltage[:-2])
	preset_voltage = str(preset_voltage) + 'mv' #put it in consistent units (mV)
	#now has units of mv with 'mv' on end



	if preset_pulsewidth[-1] != 's':
		raise ValueError('preset_pulsewidth {} is not supported please use ns, us, ms, s suffix'.format(preset_pulsewidth))
	#now is a str with suffix like ms

	if not test:

		for pulsen in [1,2]:
			initialize_trig(pg, pulsen, pulsewidth=pulsewidth, delay=delay)
			time.sleep(.1)
			apply_preset_pulse(pg, preset_pulsewidth, preset_voltage)
			time.sleep(.8)
			initialize_2pulse(pg, pulsewidth=pulsewidth, delay=delay, high_voltage=high_voltage)
			time.sleep(.2)
			manual_trigger(pg)
			time.sleep(.1)
			pg.write('pulsegenc:stop') 

			tdf = tds620B_get_wf(scope)
			time.sleep(3)
			if pulsen == 1:
				df = tdf.copy()
				df.rename(columns={'v':'p1'}, inplace = True)
			else:
				df['p2'] = tdf.v
	else:
		df = pd.DataFrame({'data':[1,2,3]})


	save_pulsewidth = str(float(pulsewidth)*1e9).replace('.', 'x') + 'ns'
	save_delay = str(float(delay)*1e9).replace('.', 'x') + 'ns'
	save_highvoltage = high_voltage.replace('.','x')
	save_presetvoltage = preset_voltage.replace('.', 'x')
	save_presetpulsewidth = str(float(preset_pulsewidth.replace('ns', 'e-9').replace('us','e-6').replace('ms', 'e-3').replace('s', ''))*1e9).replace('.', 'x') + 'ns'

	save_base_name = 'PRESET2PULSE_'
	for namer in [save_pulsewidth, save_delay, save_highvoltage, save_presetvoltage, save_presetpulsewidth]:
		save_base_name += namer + '_'
	save_base_name = save_base_name[:-1] #remove final '_'

	meta_data = {
		'type':'preset2pulse', 
		'identifier':identifier, 
		'pulsewidth_ns':float(save_pulsewidth[:-2].replace('x','.')),
		'delay_ns':float(save_delay[:-2].replace('x','.')),
		'high_voltage_v':float(save_highvoltage.replace('x', '.')[:-2])/1000,
		'preset_voltage_v':float(save_presetvoltage.replace('x', '.')[:-2])/1000,
		'preset_pulsewidth_ns':float(save_presetpulsewidth[:-2].replace('x','.'))
	}
			
	return save_base_name, meta_data, df


def trial(run_function, run_function_args, path):
	"""
	A trial  for FE switching experiment. This will save to path with a unique name
	currently supported run_functions are (run_preset_then_2pusle_TDS620B,) more to come

	any run_function which returns ((str) base_name, (pandas.dataframe) data) should work, but only those indicated above are known to work
	----
	run_function: (function) which function you wish to run i.e. run_preset_then_2pusle_TDS620B - must return a tuple (base_name of trial, pandas.dataframe of data)
	run_function_args: (dict) arguments for run_function
	base_name: (str) string of base name
	path: (str) where to save
	"""
	base_name, meta_data, df = run_function(**run_function_args)
	try:
		save_name = get_save_name(base_name, path)
		trial = int(save_name.split('_')[-1].replace('.csv',''))
	except Exception as e:
		save_name = input('there was an error generating a save name: {}\n please enter a unique name'.format(e))
		trial = np.nan


	meta_data.update({'trial':trial, 'filename':save_name})

	assert type(df) == type(pd.DataFrame()), 'run_function {} does not return a pandas.DataFrame as its third return argument, it must'.format(run_function.__name__)

	df.to_csv(path+save_name, index=False)

	#update the meta_data file in this directory
	meta_data = pd.DataFrame(meta_data, index = [0])
	try:
		existing_meta_data = pd.read_pickle(path+'meta_data')
		if set(meta_data.columns) != set(existing_meta_data.columns):
			raise ValueError('the columns of meta_data do not match the existing columns of the data in this path ({}). Please ensure you are producing data of the same type, or move to a new path. Please note, your data was saved with file complete filename: {}, but it was not added to meta_data'.format(path, path+save_name))
		out = pd.concat([existing_meta_data, meta_data], ignore_index = True)
	except FileNotFoundError:
		out = meta_data.copy()

	out.to_pickle(path + 'meta_data')

	return
