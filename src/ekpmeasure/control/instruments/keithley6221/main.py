import numpy as np
from .. import misc
from ....universal import get_number_and_suffix

__all__ = ('restore', 'set_output_sin', 'set_wave_on', 'set_wave_off', 'is_on')

def restore(current_source):
    """Restore settings on current source.

    args:
        current_source (pyvisa.resources.gpib.GPIBInstrument): Keithley 6221

    
    """
    current_source.write("*rst")
    return

def set_output_sin(current_source, frequency, amplitude, compliance = 1.1):
    """Set the current source to output a sin waveform with specified amplitude and frequency. Does not start the current source.

    args:
        current_source (pyvisa.resources.gpib.GPIBInstrument): Keithley 6221
        frequency (str): Frequency. Allowed suffix 'khz', 'hz'.
        amplitude (str): Amplitude. Allowed suffix 'ua', 'ma'.
        compliance (float): Compliance in V. 


    """
    restore(current_source)
    
    freq_number, freq_suffix = get_number_and_suffix(frequency)
    if freq_suffix not in set(misc.freq_mapper.keys()):
        raise KeyError('frequency suffix {} is not allowed. (allowed are khz and hz)'.format(freq_suffix))
    amp_number, amp_suffix = get_number_and_suffix(amplitude)
    if amp_suffix not in set(misc.current_amp_mapper.keys()):
        raise KeyError('amplitude suffix {} is not allowed. (allowed are ma and ua)'.format(amp_suffix))
        
    freq = str(freq_number) + misc.freq_mapper[freq_suffix]
    amp = str(amp_number) + misc.current_amp_mapper[amp_suffix]

    command = """
    SOUR:WAVE:FUNC SIN
    SOUR:WAVE:FREQ {}
    SOUR:WAVE:AMPL {}
    SOUR:WAVE:PMAR:STAT ON
    SOUR:WAVE:PMAR:OLIN 4
    SOUR:WAVE:RANG BEST
    SOUR:CURR:COMP {}
    """.format(freq, amp, compliance)
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