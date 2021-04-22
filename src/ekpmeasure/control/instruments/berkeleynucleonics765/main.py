__all__= ('single_pulse_SCPI', 'symmetric_up_down_SCPI', 'initialize_2pulse', 'initialize_pulse', 'manual_trigger','initialize_trig', 'stop')

def single_pulse_SCPI(pulsewidth, updown, high_voltage, low_voltage, channel = '1', *args, **kwargs):
	"""
	returns SCPI string that can be written to the pulge generator to put it in the correct state to apply a single pulse
	----
	pulsewidth: (str) i.e. '10ns' allowed units {ns, us, ms, s}
	updown: (str) i.e. 'down' options {'up', 'down'} sets polarity
	high_voltage: (str) i.e. '1000mv' allowed units {V, mv}, sets high voltage for the pulse
	low_voltage: (str) i.e. '-1000mv' allowed units {V, mv}, sets low voltage for the pulse

	options
	----
	channel = (str) select output channel
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
	returns tuple of two SCPI strings, one up SCPI string (from single_pulse_SCPI) and one down. The strings describe symmetric pulses 
	----
	
	pulsewidth: (str) allowed units {ns, us, ms, s}
	ampitude: (str) allowed units {mv, v}

	options
	----
	offset: (str) allowed units {mv, v}
	channel: (str) select channel for output
	
	example: up_down_init(pulsewidth='10ns', amplitude='1v', offset='100mv',)
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
	initializes the pulse generator for application of a pulse (set trigger mode to manual, etc)
	----
	inst: (pyvisa.resources.gpib.GPIBInstrument)
	channel: (str) select output channel
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
	"""trigger BN765 to apply whatever pulse configuration is set"""
	pg.write('trig:seq:imm') #execute
	return

def initialize_2pulse(pg, channel = '1', pulsewidth = '10e-9', delay = '10e-9',
					  low_voltage = '0', high_voltage = '4.8'):
	"""
	initializes BN765 for application of 2 pulse sequenc. Pulses are positive polarity, and identical (as defined by low and high voltage) with given delay between pulses.
	----
	pg: (pyvisa.resources.gpib.GPIBInstrument) BN765 instrument

	options:
	----
	channel: (str) select output channel
	pulsewidth:(str) set pulsewidth example 1e-9
	delay: (str) set delay example 1e-9
	low_voltage: (str) set low voltage units are in volts
	high_voltage: (str) set high voltage units are in volts

	"""
	err = ''
	while err != 'Error: 0, No error\n':#clear errors
		err = pg.query('syst:err:next?')

	pgchannel = channel
	pw = pulsewidth

	delay1 = str(float(pw) + float(delay))
	delay2 = str(float(delay1)*2)
	pg.write('outp'+pgchannel+':puls:mode dou')
	pg.write('source'+pgchannel+':pulse1:wid '+pw)
	pg.write('source'+pgchannel+':pulse2:wid '+pw)

	pg.write('source'+pgchannel+':pulse1:del '+'0')
	pg.write('source'+pgchannel+':pulse2:del '+delay1)

	pg.write('source'+pgchannel+':volt:lev:imm:low '+low_voltage)
	pg.write('source'+pgchannel+':volt:lev:imm:high '+high_voltage)
	pg.write('trig:seq:sour man')
	pg.write('outp'+pgchannel+':stat on')
	pg.write('PULSEGENControl:START')
	if pg.query('syst:err:next?') != 'Error: 0, No error\n':
		stop(pg,)
		raise ValueError('error in initialize_2pulse init')
		
	return

#shut off
def stop(pg,):
	"""stop the BN765"""
	pg.write('PULSEGENControl:STOP')
	pg.write('outp1:stat off')
	pg.write('outp2:stat off')
	return

def initialize_trig(pg, pulsen, channel = '2', pulsewidth = '10e-9', delay = '10e-9',
					  low_voltage = '0', high_voltage = '1'):
	"""
	Initializes a channel for use as a trigger. This is used in conjunction with, for example, initialize_2pulse, so we can output a trigger pulse from the other channel in order to properly time the scope for acquisition. We can do this for any of the pulse n (in the case of 2 pulses one can send a trigger pulse synced to pulse 1 or 2)
	----
	pg: (pyvisa.resources.gpib.GPIBInstrument) BN765
	pulsen: (int) for which pulse number to ready a trigger pulse
	channel: (str) select channel for trigger pulse
	pulsewidth: (str) pulsewidth of the triggr pulse. this should match your stimulus pw
	delay: (str) should match your stimulus delay
	low_voltage: (str) units are volts - low voltage of trigger pulse
	high_voltage: (str) units are volts - high voltage of trigger pulse
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