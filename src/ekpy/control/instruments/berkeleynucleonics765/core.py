from ....utils import get_number_and_suffix, time_to_sci_mapper, voltage_amp_mapper



__all__  = ('get_pulse_mode', 'set_pulse_mode', 'set_pulse_width', 'set_pulse_delay',
	'set_pulse_mode', 'set_polarity', 'set_channel_on', 'set_channel_off', 'set_low_voltage', 
	'set_high_voltage', 'set_trigger_mode', 'set_trigger_source', 'set_trigger_input_slope',
	'set_trigger_input_threshold', 'check_errors', 'clear_errors', 'stop', 'start',
	# next will soon be deprecated
	'single_pulse_SCPI', 'symmetric_up_down_SCPI', 
	'initialize_2pulse', 'initialize_pulse', 'manual_trigger',
	'initialize_trig', 'stop')

pulse_modes = {'single', 'double', 'triple', 'quadruple'}
channels = {'ch1', 'ch2'}
puslewidth_suffixes = {'ns', 'us', 'ms'}
triggers = {'external', 'timer', 'manual'}
trigger_modes = {'single', 'burst', 'gated', 'continuous'}
trigger_slopes = {'rising', 'falling'}

def check_channel(channel: str):
	if channel.lower() not in channels:
		raise ValueError('Channel "{}" not allowed. Please use one of {}'.format(channel, channels))
	else:
		return channel[-1]

def get_pulse_mode(pg, channel: str):
	"""Return 'single', 'double', 'triple', 'quadruple'"""
	channel_int_str = check_channel(channel)
	out = pg.query("output{}:pulse:mode?".format(channel_int_str)).replace('\n', '').lower()
	if out not in {'single','double', 'triple', 'quadruple'}:
		raise ValueError('Expected .get_pulse_mode to return one of {}. Instead got {}'.format("'single','double', 'triple', 'quadruple'", "out"))
	return out

def set_pulse_mode(pg, pulse_mode: str, channel: str = 'Ch1'):
	"""docstring"""
	if pulse_mode.lower() not in pulse_modes:
		raise ValueError('Pulse mode "{}" not allowed. Please use one of {}'.format(pulse_mode, pulse_modes))

	channel_int_str = check_channel(channel)

	pg.write('output{}:pulse:mode {}'.format(channel_int_str, pulse_mode))
	return

def _check_pulse_count_vs_pulse_mode(pulse_count: int, pulse_mode: str):
	checker_dict = {'single':1,'double':2, 'triple':3, 'quadruple':4}
	if pulse_count>checker_dict[pulse_mode]:
		raise ValueError('Cannot modify pulse number {} in pulse mode "{}"'.format(pulse_count, pulse_mode))

def set_pulse_width(pg, pulsewidth: str, pulse_count: int = 1, channel: str = 'Ch1'):
	"""docstring"""
	if pulsewidth[-2:] not in puslewidth_suffixes:
		raise ValueError('Pulsewidth "{}" not allowed. Allowed are {}'.format(pulsewidth, puslewidth_suffixes))

	channel_int_str = check_channel(channel)
	pulse_mode = get_pulse_mode(pg, channel)

	_check_pulse_count_vs_pulse_mode(pulse_count, pulse_mode)

	pg.write('source{}:pulse{}:width {}'.format(channel_int_str,pulse_count,pulsewidth))
	return

def set_pulse_delay(pg, delay: str, pulse_count: int = 1, channel: str = 'Ch1'):
	"""docstring"""

	channel_int_str = check_channel(channel)
	pulse_mode = get_pulse_mode(pg, channel)

	_check_pulse_count_vs_pulse_mode(pulse_count, pulse_mode)

	number, suffix = get_number_and_suffix(delay)
	scientific_delay = str(number)+time_to_sci_mapper[suffix]

	pg.write('source{}:pulse{}:delay {}'.format(channel_int_str, pulse_count, scientific_delay))
	return


def set_polarity(pg, inverted: bool = False, channel: str = "Ch1"):
	"""docstring"""
	channel_int_str = check_channel(channel)
	_dict = {True: 'on', False: 'off'}
	pg.write("source{}:inv {}".format(channel_int_str, _dict[inverted]))
	return

def set_high_voltage(pg, high_voltage: str, channel: str = 'Ch1'):
	"""docstring"""
	channel_int_str = check_channel(channel)
	number, suffix = get_number_and_suffix(high_voltage)
	if suffix.lower() not in {'v', 'mv'}:
		raise ValueError('High Voltage "{}" not allowed. Must have suffix "V or mV"'.format(high_voltage))

	pg.write("source{}:voltage:level:immediate:high {}".format(channel_int_str, high_voltage))
	return


def set_low_voltage(pg, low_voltage: str, channel: str = 'Ch1'):
	"""docstring"""
	channel_int_str = check_channel(channel)
	number, suffix = get_number_and_suffix(low_voltage)
	if suffix.lower() not in {'v', 'mv'}:
		raise ValueError('Low Voltage "{}" not allowed. Must have suffix "V or mV"'.format(low_voltage))

	pg.write("source{}:voltage:level:immediate:low {}".format(channel_int_str, low_voltage))
	return

def set_trigger_source(pg, _type: str):
	if _type.lower() not in triggers:
		raise ValueError('Trigger type "{}" not allowed, must be {}'.format(_type, triggers))

	pg.write('trig:seq:sour {}'.format(_type))
	return

def set_trigger_mode(pg, _mode: str):
	if _mode.lower() not in trigger_modes:
		raise ValueError('Trigger mode "{}" not allowed, must be {}'.format(_mode, trigger_modes))

	pg.write('trig:seq:mode {}'.format(_mode))
	return

def set_trigger_input_slope(pg, _type: str):
	if _type.lower() not in trigger_slopes:
		raise ValueError('Trigger slope {} not allowed, must be {}'.format(_type, trigger_slopes))

	pg.write('trig:seq:slope {}'.format(_type))
	return

def set_trigger_input_threshold(pg, threshold_voltage: str):
	number, suffix = get_number_and_suffix(threshold_voltage)
	if suffix.lower() not in {'v', 'mv'}:
		raise ValueError('Threshold Voltage "{}" not allowed. Must have suffix "V or mV"'.format(threshold_voltage))

	pg.write('trig:seq:threshold {}'.format(str(number) + voltage_amp_mapper[suffix]))
	return

def start(pg):
	pg.write('PULSEGENControl:START')
	return

def stop(pg):
	pg.write('PULSEGENControl:STOP')

def check_errors(pg):
	error_check = pg.query('syst:err:next?')

	if error_check != 'Error: 0, No error\n':
		raise ValueError('Error. Error Message: {}'.format(error_check))

	return

def clear_errors(pg, max_iterations: int = 10):
	error_check = pg.query('syst:err:next?')
	_iter = 0
	while error_check != 'Error: 0, No error\n':
		_iter += 1
		if _iter>=max_iterations:
			raise ValueError('Maximum number of iterations reached in clearing errors.')
		error_check = pg.query('syst:err:next?')

	return

def set_channel_on(pg, channel: str = 'Ch1'):
	channel_int_str = check_channel(channel)
	pg.write('outp{}:stat on'.format(channel_int_str))
	return

def set_channel_off(pg, channel: str = 'Ch1'):
	channel_int_str = check_channel(channel)
	pg.write('outp{}:stat off'.format(channel_int_str))
	return

def single_pulse_SCPI(pulsewidth, updown, high_voltage, low_voltage, channel = '1', *args, **kwargs):
	"""
	Returns SCPI string that can be written to the pulse generator to put it in the correct state to apply a single pulse.

	args:
		pulsewidth (str): Pulsewidth. i.e. '10ns' allowed units {ns, us, ms, s}
		updown (str): Specify polarity. 'up' or 'down'.
		high_voltage (str): High voltage of pulse. i.e. '1000mv' allowed units {V, mv}
		low_voltage (str): Low voltage of pulse. i.e. '-1000mv' allowed units {V, mv}
		channel (str): Specify the output channel. '1' or '2'


	"""
	if pulsewidth[-2:] not in set({'ns', 'us', 'ms',}):
		if pulsewidth[-1] != 's':
			raise ValueError('pulsewidth ' + str(pulsewidth) + ' not supported')
	if updown not in set({'up', 'down'}):
		raise ValueError('updown ' + str(updown) + ' not supported')
	if high_voltage[-2:].lower() not in set({'mv'}):
		if high_voltage[-1].lower() != 'v':
			raise ValueError('high_voltage ' + str(high_voltage) + ' not supported')
	if low_voltage[-2:].lower() not in set({'mv'}):
		if low_voltage[-1].lower() != 'v':
			raise ValueError('low_voltage ' + str(low_voltage) + ' not supported')
	if channel not in set({'1', '2'}):
		raise ValueError('channel ' + str(channel) + ' not supported')
	
	if updown == 'up':
		out = 'outp'+channel+':puls:mode sin;'
		out += ':sour'+channel+':inv off;'
		out += ':sour'+channel+':volt:lev:imm:high '+high_voltage + ';'
		out += ':sour'+channel+':volt:lev:imm:low '+low_voltage + ';'
		#puls1 means the first pulse because we are in single mode
		out += ':sour'+channel+':puls1:wid '+pulsewidth + ';'
		return out
	else:
		out = 'outp'+channel+':puls:mode sin;'
		out += ':sour'+channel+':inv on;'
		out += ':sour'+channel+':volt:lev:imm:low '+low_voltage + ';'
		out += ':sour'+channel+':volt:lev:imm:high '+high_voltage + ';'
		#puls1 means the first pulse because we are in single mode
		out += ':sour'+channel+':puls1:wid '+pulsewidth + ';'
		return out


def symmetric_up_down_SCPI(pulsewidth, amplitude, offset='0mv', channel = '1', *args, **kwargs):
	"""
	Return a tuple of two SCPI strings. The first, an up SCPI string (from single_pulse_SCPI) and the second down. The strings describe symmetric pulses.

	args:
		pulsewidth (str): Pulsewidth. allowed units {'ns', 'us', 'ms', 's'}.
		amplitude (str): Amplitude. allowed units {mv, v}.
		offset (str): Offset. allowed units {mv, v}.
		channel (str): Specify channel. '1' or '2'


	"""
	if amplitude[-2:].lower() not in set({'mv'}):
		if amplitude[-1].lower() != 'v':
			raise ValueError('amplitude ' + str(amplitude) + ' not supported')
	if offset[-2:].lower() not in set({'mv'}):
		if offset[-1].lower() != 'v':
			raise ValueError('offset ' + str(offset) + ' not supported')
	
	try: 
		amp = int(float(amplitude[:-1]))*1000
	except ValueError:
		#means mv is the unit
		amp = int(float(amplitude[:-2]))
	try: 
		off = int(float(offset[:-1]))*1000 #now in mv units
	except ValueError:
		off = int(float(offset[:-2]))
		
	high = str(off + amp) + 'mv'
	low = str(off) + 'mv'
	high2 = str(off - amp) + 'mv'
	
	out1 = single_pulse_SCPI(pulsewidth = pulsewidth ,updown = 'up',
						  high_voltage = high, low_voltage = low, *args, **kwargs)
	out2 = single_pulse_SCPI(pulsewidth = pulsewidth ,updown = 'down',
						  high_voltage = low, low_voltage = high2, *args, **kwargs)
	return out1, out2


def initialize_pulse(inst, channel = '1', *args, **kwargs):
	"""
	Initializes the pulse generator for application of a single pulse which will output a pulse on manual trigger. 

	args:
		inst (pyvisa.resources.ENET-Serial INSTR): Berkeley Nucleonics 765
		channel (str): Output channel. 



	"""
	err = inst.query('syst:err:next?')
	if err != 'Error: 0, No error\n':
		raise ValueError('Before initializing, 765 has error message: ' + err)
		
	inst.write('outp'+channel+':puls:mode sin;')
	inst.write('trig:seq:mode sin')
	chan = inst.query('outp'+channel+':stat?')[0]
	if chan == '0':
		inst.write('outp'+channel+':stat on')
	
	stat = inst.query('pulsegenc:stat?')[0]
	if stat == '0':
		inst.write('pulsegenc:start')
		
	inst.write('trig:seq:sour man')
	
	try:
		inst.write('sour'+channel+':puls1:del ' + kwargs['delay'])
	except KeyError:
		inst.write('sour'+channel+':puls1:del 0ns')
	
	err = inst.query('syst:err:next?')  
	if err != 'Error: 0, No error\n':
		raise ValueError('During initialization, error: ' + err)
	return 

def manual_trigger(pg):
	"""Trigger BN765 to apply whatever pulse configuration is set.

	args:
		pg (pyvisa.resources.ENET-Serial INSTR): Berkeley Nucleonics 765


	"""
	pg.write('trig:seq:imm') #execute
	return

def initialize_2pulse(pg, polarity = 'up', channel = '1', pulsewidth = '10e-9', delay = '10e-9',
					  low_voltage = '0', high_voltage = '4.8'):
	"""
	Initialize BN765 for application of 2 pulse sequence. Pulses are positive polarity, and identical (as defined by low and high voltage) with given delay between pulses.

	args:
		pg: (pyvisa.resources.ENET-Serial INSTR): BN765
		channel (str): Specify output channel. '1' or '2'.
		pulsewidth (str): Pulsewidth in scientific notation.
		delay (str): Delay between pulses in scientific notation.
		low_voltage (str): Low voltage in units of volts.
		high_voltage (str): High voltage in units of volts.




	"""
	err = ''
	while err != 'Error: 0, No error\n':#clear errors
		err = pg.query('syst:err:next?')

	polarity = polarity.lower()
	assert polarity in set({'up', 'down'}), "polarity must be 'up' or 'down'. Recieved {}".format(polarity)

	pgchannel = channel
	pw = pulsewidth

	delay1 = str(float(pw) + float(delay))
	delay2 = str(float(delay1)*2)
	pg.write('outp'+pgchannel+':puls:mode dou')
	if polarity == 'down':
		pg.write('source'+pgchannel+':inv on')

	pg.write('source'+pgchannel+':pulse1:wid '+pw)
	pg.write('source'+pgchannel+':pulse2:wid '+pw)

	pg.write('source'+pgchannel+':pulse1:del '+'0')
	pg.write('source'+pgchannel+':pulse2:del '+delay1)

	if polarity == 'down':
		pg.write('source'+pgchannel+':volt:lev:imm:high '+low_voltage)
		pg.write('source'+pgchannel+':volt:lev:imm:low -'+high_voltage)
	else:
		pg.write('source'+pgchannel+':volt:lev:imm:low '+low_voltage)
		pg.write('source'+pgchannel+':volt:lev:imm:high '+high_voltage)

	pg.write('trig:seq:sour man')
	pg.write('outp'+pgchannel+':stat on')
	pg.write('PULSEGENControl:START')
	error_check = pg.query('syst:err:next?')
	if error_check != 'Error: 0, No error\n':
		stop(pg,)
		raise ValueError('error in initialize_2pulse init. Error Message: {}'.format(error_check))
		
	return

#shut off
def stop(pg,):
	"""Stop the BN765.

	args:
		pg (pyvisa.resources.ENET-Serial INSTR): BN765




	"""
	pg.write('PULSEGENControl:STOP')
	pg.write('outp1:stat off')
	pg.write('outp2:stat off')
	return

def initialize_trig(pg, pulsen, channel = '2', pulsewidth = '10e-9', delay = '10e-9',
					  low_voltage = '0', high_voltage = '1'):
	"""
	Initialize a channel for use as a trigger. This is used in conjunction with, for example, initialize_2pulse, so we can output a trigger pulse from the other channel in order to properly time the scope for acquisition. We can do this for any of the pulse n (in the case of 2 pulses one can send a trigger pulse synced to pulse 1 or 2).

	args:
		pg (pyvisa.resources.ENET-Serial INSTR): BN765
		pulsen (int): Specify which pulse number to ready a trigger pulse (1 or 2)
		channel (str): Specify a channel for trigger output.
		pulsewidth (str): Pulsewidth of the triggr pulse in scientific notation. This should match your stimulus pulsewidth.
		delay (str): Delay in scientific notation. This should match your stimulus delay.
		low_voltage (str): Low voltage of trigger pulse in Volts.
		high_voltage (str): High voltage of trigger pulse in Volts.




	"""
	err = ''
	while err != 'Error: 0, No error\n':#clear errors
		err = pg.query('syst:err:next?')
		
	if pulsen in set({1,2}):
		delay = str((float(pulsewidth) + float(delay))*(pulsen - 1))

	pgchannel = channel
	pw = pulsewidth

	delay1 = str(float(pw) + float(delay))
	delay2 = str(float(delay1)*2)
	pg.write('outp'+pgchannel+':puls:mode sin')
	pg.write('source'+pgchannel+':pulse1:wid '+pw)

	pg.write('source'+pgchannel+':pulse1:del '+delay)

	pg.write('source'+pgchannel+':volt:lev:imm:low '+low_voltage)
	pg.write('source'+pgchannel+':volt:lev:imm:high '+high_voltage)
	pg.write('trig:seq:sour man')
	pg.write('outp'+pgchannel+':stat on')
	pg.write('PULSEGENControl:START')
	if pg.query('syst:err:next?') != 'Error: 0, No error\n':
		stop(pg,)
		raise ValueError('error in initialize_2pulse init')
	return