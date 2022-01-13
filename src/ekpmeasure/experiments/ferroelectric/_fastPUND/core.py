from .... import control
from .... import universal
from ....control.instruments import berkeleynucleonics765 as bk
from ....control.instruments import tektronixTDS6604 as tds
from ....control.instruments import tektronix3252 as tek
from ....control import plotting
from ....analysis import plotting as _plotting

### PLOTTING config
import matplotlib.pyplot as plt
plt.style.use(_plotting.lane_martin)

import numpy as np
import pandas as pd

import time 

__all__ = ('PUND',)

def _get_frequency(pw, delay):
	"""Get the frequency to set the slow pulse gen"""
	tpund = pw
	for t in [pw, pw, delay, delay]:
		tpund = _add_time_strings(tpund, t)

	n, s = universal.get_number_and_suffix(tpund)
	desired_frequency = np.round(1/(4*float(str(n) + universal.time_suffix_to_scientic_str(s))), 2)
	if desired_frequency > 5e6:
		raise ValueError('desired frequency is higher than 5MHz')

	if desired_frequency < 100:
		raise ValueError('desired frequency is lower than 100Hz')

	out = str(desired_frequency/1e3) + 'kHz'
	return out

def _add_time_strings(str1, str2):
	"""returns a string in units of str1"""
	n1, s1 = universal.get_number_and_suffix(str1)
	n2, s2 = universal.get_number_and_suffix(str2)
	unit_multiplier = 1/float('1'+universal.time_suffix_to_scientic_str(s1))
	
	float_total = (n1*float('1'+universal.time_suffix_to_scientic_str(s1)) + 
				  n2*float('1'+universal.time_suffix_to_scientic_str(s2)))
	
	return str(np.round(float_total*unit_multiplier, 5)) + s1

def _add_voltage_strings(str1, str2):
	"""returned in units of str1"""
	n1, s1 = universal.get_number_and_suffix(str1)
	n2, s2 = universal.get_number_and_suffix(str2)
	unit_multiplier = 1/float('1'+universal.voltage_amp_mapper[s1])
	
	float_total = (n1*float('1'+universal.voltage_amp_mapper[s1]) + 
				  n2*float('1'+universal.voltage_amp_mapper[s2]))
	
	return str(np.round(float_total*unit_multiplier, 5)) + s1

def _get_delay_times(pw, delay):
	delay_P1 = _add_time_strings(pw, delay)
	delay_P2 = _add_time_strings(_add_time_strings(delay_P1, pw), delay)
	return delay_P1, delay_P2

def _config_bk(pg, pw:str, delay:str, voltage:str, offset:str, inverted:bool=False):
	"""Configure berkeley nucleonics pg for pund.

	args:
		pg (pyvisa.resources.tcpip.TCPIPInstrument): Berkeley Nucleonics 765
		pw (str): Pulsewidth, e.g. '100ns'
		delay (str): Delay, e.g. '100ns'
		voltage (str): Voltage amplitude, e.g. '1V'
		offset (str): Offset Voltage, e.g. '500mV'
	"""
	# set the trigger settings:
	bk.set_trigger_input_slope(pg, 'rising')
	bk.set_trigger_input_threshold(pg, '1v')
	
	
	# clear errors
	bk.clear_errors(pg)

	# turn everything off
	bk.stop(pg)
	bk.set_channel_off(pg, 'ch1')
	bk.set_channel_off(pg, 'ch2')

	# channel 1 is set pulse
	bk.set_pulse_mode(pg, 'single', channel='ch1')
	bk.set_polarity(pg, inverted=not inverted, channel='ch1')

	low_voltage = _add_voltage_strings('-'+voltage, offset)
	high_voltage = _add_voltage_strings(voltage, offset)

	if not inverted: # case where preset pulse IS inverted 
		bk.set_low_voltage(pg, low_voltage, channel='ch1')
		bk.set_high_voltage(pg, offset, channel='ch1')

	else: # case where preset pulse ISNOT inverted
		bk.set_high_voltage(pg, high_voltage, channel='ch1')
		bk.set_low_voltage(pg, offset, channel='ch1')

	bk.set_pulse_width(pg, pw, pulse_count=1, channel='ch1')
	bk.set_pulse_delay(pg, '0ns', pulse_count=1, channel='ch1')

	# channel 2 is double up pulses
	bk.set_pulse_mode(pg, 'double', channel='ch2')
	bk.set_polarity(pg, inverted=inverted, channel='ch2')

	if not inverted:
		bk.set_high_voltage(pg, high_voltage, channel='ch2')
		bk.set_low_voltage(pg, offset, channel='ch2')

	else:
		bk.set_low_voltage(pg, low_voltage, channel='ch2')
		bk.set_high_voltage(pg, offset, channel='ch2')
		
	bk.set_pulse_width(pg, pw, pulse_count=1, channel='ch2')
	bk.set_pulse_width(pg, pw, pulse_count=2, channel='ch2')

	delay_P1, delay_P2 = _get_delay_times(pw, delay)

	bk.set_pulse_delay(pg, delay_P1, pulse_count=1, channel='ch2')
	bk.set_pulse_delay(pg, delay_P2, pulse_count=2, channel='ch2')

	# check for errors
	bk.check_errors(pg)
	
	# set eveything on 
	bk.set_channel_on(pg, 'ch1')
	bk.set_channel_on(pg, 'ch2')
	bk.start(pg)
	
	return 
	
def _config_slowpg(pg, frequency:str):
	"""Config afg 3252 (triggering pg)

	args:
		pg (pyvisa.resources.gpib.GPIBInstrument): Tektronix AFG3252
		frequency (str): Frequency, e.g. '100kHz'

	"""


	slowpg = pg

	# stop everything
	tek.stop_pulse_gen(slowpg, both=True)

	# set things for both channels
	tek.set_frequency(slowpg, frequency=frequency, both=True)
	tek.set_function_to_pulse(slowpg, both=True)
	tek.set_run_mode_to_burst(slowpg, both=True)
	tek.set_polarity(slowpg, inverted=False, both=True)
	tek.set_ncylces_for_burst_mode(slowpg, ncycles=1, both=True)
	tek.set_high_voltage(slowpg, '3V', both=True)
	tek.set_low_voltage(slowpg, '0V', both=True)

	# trigger bk with channel 2
	tek.set_pulsewidth(slowpg, '100ns', channel=2)
	tek.set_pulse_delay(slowpg, '0ns', channel=2)

	# trigger scope with channel 1
	tek.set_pulsewidth(slowpg, '4ns', channel=1) 
	return

def _config_scope(scope):
	"""Config Scope (TDS6604)

	args:
		scope (pyvisa.resources.gpib.GPIBInstrument): Tektronix TDS6604
	"""
	
	tds.set_data_source(scope, channel='Ch3')
	tds.initialize_for_data_transfer(scope)
	tds.set_horizontal_resolution(scope, number_pts=5000)
	return

def _ready_scope(scope):
	tds.set_triggerA_mode(scope, 'norm')
	tds.set_acquire_state(scope, 1)
	tds.set_acquire_stopafter(scope, 'seq')
	return


def _stop_bk(pg):
	# turn everything off
	bk.stop(pg)
	bk.set_channel_off(pg, 'ch1')
	bk.set_channel_off(pg, 'ch2')
	return

def go(bk765, afg3252, tds6604, _delay_dict, pulsenumber:str):
    scope = tds6604
    pg = bk765
    slowpg = afg3252 
    
    _ready_scope(scope)
    
    # set the trigger pulse
    tek.set_pulse_delay(slowpg, _delay_dict[pulsenumber], channel=1)
    
    # start
    tek.start_pulse_gen(slowpg, both=True)
    time.sleep(1)
    
    # trigger
    tek.trigger(slowpg)
    time.sleep(1)
    
    # stop
    tek.stop_pulse_gen(slowpg, both=True)
    return tds.get_waveform(scope)

def run_function(bk765, afg3252, tds6604, pulsewidth:str, delay:str, 
	voltage:str, offset:str, offset_time_delay:str='90ns', identifier:str='none',
	inverted:bool=False, **kwargs):

	base_name = 'FastPUND_{}_{}_{}_{}_{}'.format(identifier, voltage, offset, pulsewidth, delay)

	meta_data = {
		'voltage':voltage,
		'offset':offset,
		'pulsewidth':pulsewidth,
		'delay':delay,
		'identifier':identifier,
		'inverted':inverted
	}
	meta_data.update(**kwargs)

	pw = pulsewidth
	# parameters
	delay_P1, delay_P2 = _get_delay_times(pulsewidth, delay)
	frequency = _get_frequency(pulsewidth, delay)
	offset_time_delay = offset_time_delay
	_delay_dict = {
	    'P0':offset_time_delay,
	    'P1':_add_time_strings(offset_time_delay, delay_P1),
	    'P2':_add_time_strings(offset_time_delay, delay_P2)
	}

	# configure pulse generators
	pg, slowpg, scope = bk765, afg3252, tds6604
	_config_bk(pg, pw, delay, voltage, offset,inverted=inverted)
	_config_slowpg(slowpg, frequency)
	_config_scope(scope)

	for i, pulsen in enumerate(['P0', 'P1', 'P2']):
		time.sleep(2) # wait to calibrate
		tdf = go(pg, slowpg, scope, _delay_dict, pulsenumber=pulsen)
		if i == 0:
			out = tdf.copy().rename(columns={'v':pulsen.lower()})
		else:
			out[pulsen.lower()] = tdf.v

	_stop_bk(pg)

	return base_name, meta_data, out


class PUND(control.experiment):
    
    def __init__(self, bk765, afg3252, tds6604):
        self.run_function = run_function
        self.pg = bk765
        self.slowpg = afg3252
        self.scope = tds6604
        
    def checks(self, params):
        
        if self.pg != params['bk765']:
            raise ValueError('BK765 does not match run_function params and self')
            
        if self.slowpg != params['afg3252']:
            raise ValueError('afg3252 does not match run_function params and self')
            
        if self.scope != params['tds6604']:
            raise ValueError('tds6604 does not match run_function params and self')  
        pass
    
    def terminate(self):
        _stop_bk(self.pg)
        
    def _plot(self, data, scan_params):
        if hasattr(self, 'fig') and hasattr(self, 'ax'):
            pass
        else:
            fig, ax = plt.subplots()
            self.fig = fig
            self.ax = ax
        self.ax.cla()
        self.ax.plot(data['time'], data['p1'] - data['p2'], color = 'blue')
        self.ax.set_title(scan_params['voltage'])
        plt.show(self.fig)
        plotting.update_plot(self.fig)
        return

    def set_horizontal_scale(self, scale:str):
    	tds.set_horizontal_scale(self.scope, scale=scale)
    	return