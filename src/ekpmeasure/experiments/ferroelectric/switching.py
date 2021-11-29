from ...control.instruments.berkeleynucleonics765 import *
from ...control.instruments.tektronixTDS620B import get_wf_from_scope as tds620B_get_wf
from ...control.instruments.tektronixTDS6604 import initialize_scope as initialize_scope_tds6604
from ...control.instruments.tektronixTDS6604 import get_waveform as get_wf_tds6604

import pyvisa as visa
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time
import os


identifier_to_diameter_dict = dict({'4':4, '6':6, '8':8, '5':5, '125':12.5, '95':9.5,'14':14, '185':18.5,'25':25, '23':23})


def single_pulse_run_function(pg, scope, identifier, pulsewidth, delay, high_voltage, polarity = 'up', scopetype = '6604', 
	area='fromdiameter', diameter = 'fromidentifier',  scope_channel = 'Ch1', test=False):
	"""
	Run a 2 pulse measurement using the BN765 and tektronix scope. Allowed scopes are 6604 and 620B. 6604 is preferred for fast measurements.

	args:
	pg (pyvisa.resources.gpib.GPIBInstrument): Pulse generator berkeley nucleonics 765
	scope (pyvisa.resources.gpib.GPIBInstrument): tektronix scope (either 6604 or 620B)
	identifier (str): some indentifier for the capacitor or sample you are studying
	pulsewidth (str): which pulsewidth to use on 2 pulse. example '500ns'
	delay (str): Example '10ns' delay between the two pulses
	high_voltage (str): Example '100mV' allowed units are V and mv. This parameter sets the amplitude of the two pulse.
	scopetype (str): Either '6604' or '620B' the scope you are using
	area ('fromdiameter' or float): Area of sample, if 'fromdiameter' will use pi*R^2 from diameter
	diameter ('fromidentifier' or float): Diameter of capacitor. If 'fromidentifier' will split identifier by 'um' and retrieve diameter that way. Example: 4um1 will give 4 as diameter. Arbitrary identifier will not work.


	returns:
	out (tuple): save_base_name, meta_data, data_df
	"""
	if scopetype != '6604' and scopetype != '620B':
		raise ValueError('scopetype must be "6604" or "620B". Recieved {}'.format(scopetype))

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


	if not test:

		for pulsen in [1,2]:
			initialize_trig(pg, pulsen, pulsewidth=pulsewidth, delay=delay)
			time.sleep(.8)
			initialize_2pulse(pg, polarity=polarity, pulsewidth=pulsewidth, delay=delay, high_voltage=high_voltage)
			time.sleep(.2)
			manual_trigger(pg)
			time.sleep(.1)
			pg.write('pulsegenc:stop') 

			if scopetype == '6604':
				initialize_scope_tds6604(scope, channel = scope_channel, force_yes = True)
				tdf = get_wf_tds6604(scope)
			elif scopetype == '620B':
				tdf = tds620B_get_wf(scope, channel = scope_channel.lower())
			else:
				raise ValueError('Please check scopetype. Set to {}, which is not allowed'.format(scopetype))

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

	save_base_name = identifier + '_'
	for namer in [save_pulsewidth, save_delay, save_highvoltage, scope_channel, polarity]:
		save_base_name += namer + '_'
	save_base_name = save_base_name[:-1] #remove final '_'

	meta_data = {
		'type':'2pulse', 
		'identifier':identifier, 
		'pulsewidth_ns':float(save_pulsewidth[:-2].replace('x','.')),
		'delay_ns':float(save_delay[:-2].replace('x','.')),
		'high_voltage_v':float(save_highvoltage.replace('x', '.')[:-2])/1000,
		'scope_channel':scope_channel,
		'polarity':polarity,
	}
	try:
		meta_data.update({
			'diameter':identifier_to_diameter_dict[identifier.split('um')[0]],
			'area':np.pi*(identifier_to_diameter_dict[identifier.split('um')[0]]/2)**2
		})
	except KeyError:
		print('unable to extract diameter and area from key {}'.format(identifier))
		meta_data.update({
			'diameter':np.nan,
			'area':np.nan
		})
			
	return save_base_name, meta_data, df

def two_pulse_run_function(pg, scope, identifier, pulsewidth, delay, high_voltage, polarity = 'up', scopetype = '6604', 
	area='fromdiameter', diameter = 'fromidentifier',  scope_channel = 'Ch1', test=False):
	"""
	Run a 2 pulse measurement using the BN765 and tektronix scope. Allowed scopes are 6604 and 620B. 6604 is preferred for fast measurements.

	args:
	pg (pyvisa.resources.gpib.GPIBInstrument): Pulse generator berkeley nucleonics 765
	scope (pyvisa.resources.gpib.GPIBInstrument): tektronix scope (either 6604 or 620B)
	identifier (str): some indentifier for the capacitor or sample you are studying
	pulsewidth (str): which pulsewidth to use on 2 pulse. example '500ns'
	delay (str): Example '10ns' delay between the two pulses
	high_voltage (str): Example '100mV' allowed units are V and mv. This parameter sets the amplitude of the two pulse.
	scopetype (str): Either '6604' or '620B' the scope you are using
	area ('fromdiameter' or float): Area of sample, if 'fromdiameter' will use pi*R^2 from diameter
	diameter ('fromidentifier' or float): Diameter of capacitor. If 'fromidentifier' will split identifier by 'um' and retrieve diameter that way. Example: 4um1 will give 4 as diameter. Arbitrary identifier will not work.


	returns:
	out (tuple): save_base_name, meta_data, data_df
	"""
	if scopetype != '6604' and scopetype != '620B':
		raise ValueError('scopetype must be "6604" or "620B". Recieved {}'.format(scopetype))

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


	if not test:

		for pulsen in [1,2]:
			initialize_trig(pg, pulsen, pulsewidth=pulsewidth, delay=delay)
			time.sleep(.8)
			initialize_2pulse(pg, polarity=polarity, pulsewidth=pulsewidth, delay=delay, high_voltage=high_voltage)
			time.sleep(.2)
			manual_trigger(pg)
			time.sleep(.1)
			pg.write('pulsegenc:stop') 

			if scopetype == '6604':
				initialize_scope_tds6604(scope, channel = scope_channel, force_yes = True)
				tdf = get_wf_tds6604(scope)
			elif scopetype == '620B':
				tdf = tds620B_get_wf(scope, channel = scope_channel.lower())
			else:
				raise ValueError('Please check scopetype. Set to {}, which is not allowed'.format(scopetype))

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

	save_base_name = identifier + '_'
	for namer in [save_pulsewidth, save_delay, save_highvoltage, scope_channel, polarity]:
		save_base_name += namer + '_'
	save_base_name = save_base_name[:-1] #remove final '_'

	meta_data = {
		'type':'2pulse', 
		'identifier':identifier, 
		'pulsewidth_ns':float(save_pulsewidth[:-2].replace('x','.')),
		'delay_ns':float(save_delay[:-2].replace('x','.')),
		'high_voltage_v':float(save_highvoltage.replace('x', '.')[:-2])/1000,
		'scope_channel':scope_channel,
		'polarity':polarity,
	}
	try:
		meta_data.update({
			'diameter':identifier_to_diameter_dict[identifier.split('um')[0]],
			'area':np.pi*(identifier_to_diameter_dict[identifier.split('um')[0]]/2)**2
		})
	except KeyError:
		print('unable to extract diameter and area from key {}'.format(identifier))
		meta_data.update({
			'diameter':np.nan,
			'area':np.nan
		})
			
	return save_base_name, meta_data, df