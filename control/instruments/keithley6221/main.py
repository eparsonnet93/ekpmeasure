import numpy as np
from ..misc import *

__all__ = ('restore', 'set_output_sin', 'set_wave_on', 'set_wave_off')

def restore(current_source):
    """restore settings on current source"""
    current_source.write("*rst")
    return

def set_output_sin(current_source, frequency, amplitude):
    """sets the current source to output a sin waveform with specified amp and freq
    ----
    frequency: (str) allowed suffix: khz, hz
    amplitude: (str) allowed suffix: ua, ma
    """
    restore(current_source)
    
    freq_number, freq_suffix = _get_number_and_suffix(frequency)
    if freq_suffix not in set(freq_mapper.keys()):
        raise KeyError('frequency suffix {} is not allowed. (allowed are khz and hz)'.format(freq_suffix))
    amp_number, amp_suffix = _get_number_and_suffix(amplitude)
    if amp_suffix not in set(current_amp_mapper.keys()):
        raise KeyError('amplitude suffix {} is not allowed. (allowed are ma and ua)'.format(amp_suffix))
        
    freq = str(freq_number) + freq_mapper[freq_suffix]
    amp = str(amp_number) + amp_mapper[amp_suffix]

    command = """
    SOUR:WAVE:FUNC SIN
    SOUR:WAVE:FREQ {}
    SOUR:WAVE:AMPL {}
    SOUR:WAVE:PMAR:STAT ON
    SOUR:WAVE:PMAR:OLIN 4
    SOUR:WAVE:RANG BEST
    """.format(freq, amp)
    current_source.write(command)
    return

def set_wave_on(current_source):
    current_source.write("SOUR:WAVE:ARM")
    current_source.write("SOUR:WAVE:INIT")
    return

def set_wave_off(current_source):
    current_source.write("SOUR:WAVE:ABORT")
    return