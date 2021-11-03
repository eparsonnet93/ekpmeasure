from ....universal import get_number_and_suffix, current_suffix_to_scientific_str, voltage_suffix_to_scientic_str

__all__ = ('stop', 'start', 'apply')

def stop(inst,):
	"""Stop the waveform generator output"""
	inst.write('outp1 off')
	inst.write('outp2 off')
	return

def _check_channel(channel):
	"""Internal function to make sure channel is allowed (either 1,2 or all)"""

	try:
		assert channel.lower() in ['1', '2', 'all'], 'Channel must be in [1,2,"all"], not {}'.format(channel)
		return channel.lower()

	except AttributeError:
		assert channel in [1,2], 'Channel must be in [1,2,"all"], not {}'.format(channel)
		return channel

def start(inst, channel=1):
	"""Start the waveform generator.

	args:
		inst (pyvisa.pyvisa.resources.gpib.GPIBInstrument): Agilent 33500
		channel (int or str): Channel 1, 2, or 'all'
	"""
	channel = _check_channel(channel)

	if channel == 'all':
		inst.write('OUTPut1 ON')
		inst.write('OUTPut2 ON')
		return

	inst.write('OUTPut{} ON'.format(channel))
	return

def apply(inst, waveform: str, frequency: str, amplitude: str, offset: str='0v', channel=1):
	"""Apply subsystem. Configure an entire waveform with one command and turn output on. 

	args:
		inst(pyvisa.pyvisa.resources.gpib.GPIBInstrument): Agilent 33500
		waveform(str): Waveform type. 'sine', 'ramp', or 'square'
		frequency(str): Frequency
		amplitude(str): Amplitude voltage
		offset(str): Offset voltage
		channel(str or int): Which channel to use. 1,2, or 'all'

	examples:
		
		Start a 1V sine wave at 1kHz:

		.. code-block:: python

			>>> apply(wvfgen, 'sin', 1e3, 1, 0, channel = 1)

		This will replace all the following SCPI commands:

		.. code-block:: bash

			FUNCtion SIN
			FREQ 1e4
			VOLT 1
			VOLT:OFF 0.1
			OUTP ON
	"""
	channel = _check_channel(channel)

	options = ['sin', 'ramp', 'square']
	waveform = waveform.lower()
	assert waveform in options, 'waveform must be ({}) not {}'.format(options, waveform)


	freq_number, freq_suffix = get_number_and_suffix(frequency)
	freq = str(freq_number) + current_suffix_to_scientific_str(freq_suffix)

	amp_number, amp_suffix = get_number_and_suffix(amplitude)
	amp = str(amp_number) + voltage_suffix_to_scientic_str(amp_suffix)

	off_number, off_suffix = get_number_and_suffix(offset)
	offs = str(off_number) + voltage_suffix_to_scientic_str(off_suffix)

	if channel=='all':
		inst.write('APPLy:{} {},{},{}'.format(waveform, freq, amp, offs))

	else:
		inst.write('SOURce{}:APPLy:{} {},{},{}'.format(channel, waveform, freq, amp, offs))

	return



