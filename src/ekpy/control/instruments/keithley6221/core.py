import wave
import numpy as np
from .. import misc
from ....utils import get_number_and_suffix

__all__ = ('restore', 'set_output_waveform', 'set_wave_on', 'set_wave_off', 'is_on')

def restore(current_source):
    """Restore settings on current source.

    args:
        current_source (pyvisa.resources.gpib.GPIBInstrument): Keithley 6221

    
    """
    current_source.write("*rst")
    return

def set_output_waveform(current_source, frequency, amplitude, waveform='sin', offset=0, compliance = 1.1):
    """Set the current source to output a specified waveform with specified amplitude and frequency.
    Does not start the current source. By default a sine wave with a 0mA DC offset.

    args:
        current_source (pyvisa.resources.gpib.GPIBInstrument): Keithley 6221
        waveform(str): Waveform. Allowed values: 'sine', 'square', 'ramp'
        frequency (str): Frequency. Allowed suffix 'khz', 'hz'.
        amplitude (str): Amplitude. Allowed suffix 'ua', 'ma'.
        offset (str): Offset. Allowed suffix 'ua', 'ma'.
        compliance (float): Compliance in V. 


    """
    restore(current_source)
    
    freq_number, freq_suffix = get_number_and_suffix(frequency)
    if freq_suffix not in set(misc.freq_mapper.keys()):
        raise KeyError('frequency suffix {} is not allowed. (allowed are khz and hz)'.format(freq_suffix))
    amp_number, amp_suffix = get_number_and_suffix(amplitude)
    if amp_suffix not in set(misc.current_amp_mapper.keys()):
        raise KeyError('amplitude suffix {} is not allowed. (allowed are ma and ua)'.format(amp_suffix))
    offs_number, offs_suffix = get_number_and_suffix(offset)
    if offs_suffix not in set(misc.current_amp_mapper.keys()):
        raise KeyError('Offset suffix {} is not allowed. (allowed are {})'.format(offs_suffix,set(misc.current_amp_mapper.keys())))
    offs = str(offs_number) + misc.current_amp_mapper[offs_suffix]    
    freq = str(freq_number) + misc.freq_mapper[freq_suffix]
    amp = str(amp_number) + misc.current_amp_mapper[amp_suffix]
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
    SOUR:WAVE:PMAR:STAT ON
    SOUR:WAVE:PMAR:OLIN 4
    SOUR:WAVE:RANG BEST
    SOUR:CURR:COMP {}
    """.format(wf, freq, amp, offs, compliance)
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