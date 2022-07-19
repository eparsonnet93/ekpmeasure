import numpy as np
from ....utils import get_number_and_suffix, freq_mapper, current_amp_mapper, time_to_sci_mapper

__all__ = ('restore', 'set_output_waveform', 'set_wave_on', 'set_wave_off', 'is_on')

def restore(current_source):
    """Restore settings on current source.

    args:
        current_source (pyvisa.resources.gpib.GPIBInstrument): Keithley 6221

    
    """
    current_source.write("*rst")
    return

def set_output_waveform(current_source, frequency, amplitude, waveform='sin', offset=0,
                        duty_cycles=50, duration='inf', num_cycles='inf', compliance=1.1):
    """Set the current source to output a specified waveform with specified amplitude and frequency.
    Does not start the current source. By default a sine wave with a 0mA DC offset.

    args:
        current_source (pyvisa.resources.gpib.GPIBInstrument): Keithley 6221
        waveform(str): Waveform. Allowed values: 'sine', 'square', 'ramp'
        frequency (str): Frequency. Allowed suffix 'khz', 'hz'.
        amplitude (str): Amplitude. Allowed suffix 'ua', 'ma'.
        offset (str): Offset. Allowed suffix 'ua', 'ma'.
        duty_cycles (float): Range: 0-100, 100 is all positive, 0 is all negative.
        duration (str): Duration in time. Allowed suffix 'ps', 'ns', 'us', 's', 'ks'.
        num_cycles (float): Duration in cycles.
        compliance (float): Compliance in V. 


    """
    restore(current_source)
    
    freq_number, freq_suffix = get_number_and_suffix(frequency)
    if freq_suffix not in set(freq_mapper.keys()):
        raise KeyError('frequency suffix {} is not allowed. (allowed are khz and hz)'.format(freq_suffix))
    amp_number, amp_suffix = get_number_and_suffix(amplitude)
    if amp_suffix not in set(current_amp_mapper.keys()):
        raise KeyError('amplitude suffix {} is not allowed. (allowed are ma and ua)'.format(amp_suffix))
    offs_number, offs_suffix = get_number_and_suffix(offset)
    if offs_suffix not in set(current_amp_mapper.keys()):
        raise KeyError('Offset suffix {} is not allowed. (allowed are {})'.format(offs_suffix,set(current_amp_mapper.keys())))
    offs = str(offs_number) + current_amp_mapper[offs_suffix]    
    freq = str(freq_number) + freq_mapper[freq_suffix]
    amp = str(amp_number) + current_amp_mapper[amp_suffix]
    dur = duration
    if dur != 'inf':
        dur_number, dur_suffix = get_number_and_suffix(duration)
        if dur_suffix not in set(time_to_sci_mapper.keys()):
            raise KeyError('duration suffix {} is not allowed. (allowed are {})'.format(dur_suffix, set(time_to_sci_mapper.keys())))
        dur = str(dur_number) + time_to_sci_mapper[dur_suffix]
    ncyc = str(num_cycles)
    dcyc = str(duty_cycles)
    waveform = waveform.lower()
    if waveform == 'sine' or waveform == 'sin':
        wf = 'SIN'
    if waveform == 'square' or waveform == 'squ':
        wf = 'SQU'
    if waveform == 'ramp':
        wf = "RAMP"
    command = """
    SOUR:WAVE:FUNC {}
    SOUR:WAVE:FREQ {}
    SOUR:WAVE:AMPL {}
    SOUR:WAVE:OFFS {}
    SOUR:WAVE:DCYC {}
    SOUR:WAVE:DUR:TIME {}
    SOUR:WAVE:DUR:CYCL {}
    SOUR:WAVE:PMAR:STAT ON
    SOUR:WAVE:PMAR:OLIN 4
    SOUR:WAVE:RANG BEST
    SOUR:CURR:COMP {}
    """.format(wf, freq, amp, offs, dcyc, dur, ncyc, compliance)
    current_source.write(command)
    return

def set_wave_on(current_source):
    """Start the current source.

    args:
        current_source (pyvisa.resources.gpib.GPIBInstrument): Keithley 6221


    """
    current_source.write("SOUR:WAVE:ARM")
    current_source.write("SOUR:WAVE:INIT")
    return

def is_on(current_source):
    """Query the current source as on or off.

    args:
        current_source (pyvisa.resources.gpib.GPIBInstrument): Keithley 6221

    returns:
        (bool): True (on) or False (off)
    """
    result = current_source.query('output?')
    if float(result.replace('\n', '')) == 1:
        return True
    else:
        return False


def set_wave_off(current_source):
    """Turn off the current source.

    args:
        current_source (pyvisa.resources.gpib.GPIBInstrument): Keithley 6221


    """
    current_source.write("SOUR:WAVE:ABORT")
    return