import numpy as np

__all__ = ('get_number_and_suffix', 'frequency_suffix_to_scientific_str', 'current_suffix_to_scientific_str', 
    'scientific_str_to_time_suffix', 'voltage_suffix_to_scientic_str', 'time_suffix_to_scientic_str', 'voltage_amp_mapper')

freq_mapper = {'Mhz':'e6','khz':'e3', 'hz':'e0', 'mhz':'e-3'}
current_amp_mapper = {'ma':'e-3', 'ua':'e-6', 'na':'e-9', 'mA':'e-3', 'uA':'e-6', 'nA':'e-9'}
sci_to_time_mapper = {'e0':'s', 'e3':'ks', 'e-3':'ms', 'e-6':'us', 'e-9':'ns'}
voltage_amp_mapper = {'mv':'e-3', 'v':'e0', 'mV':'e-3','V':'e0','kV':'e3','kv':'e3'}
time_to_sci_mapper = {'ms':'e-3', 'us':'e-6', 'ns':'e-9', 'ps':'e-12', 's':'e0', 'ks':'e3'}

def scientific_str_to_time_suffix(sci_str):
    """Convert scientific notation string to suffix for time. *i.e.* 'e-9' -> 'ns'

    args:
        sci_str (str): Scientific string to convert

    returns:
        (str): Time suffix
    """
    assert sci_str in set(sci_to_time_mapper.keys()), "sci_str {} not in sci_to_time_mapper. Allowed keys are {}".format(sci_str, list(sci_to_time_mapper.keys()))
    return sci_to_time_mapper[sci_str]

def time_suffix_to_scientic_str(time_suffix):
    """Convert time suffix to scientific. *i.e.* 'ms' -> 'e-3'.

    args:
        time_suffix (str): Suffix to convert

    returns:
        (str): Scientific notation str
    """
    assert time_suffix in set(time_to_sci_mapper.keys()), "time_suffix {} not in time_to_sci_mapper. Allowed keys are {}".format(time_suffix, list(time_to_sci_mapper.keys()))
    return time_to_sci_mapper[time_suffix]

def voltage_suffix_to_scientic_str(volt_suffix):
    """Convert voltage suffix to scientific. *i.e.* 'mV' -> 'e-3'.

    args:
        volt_suffix (str): Suffix to convert

    returns:
        (str): Scientific notation str
    """
    assert volt_suffix in set(voltage_amp_mapper.keys()), "volt_suffix {} not in voltage_amp_mapper. Allowed keys are {}".format(volt_suffix, list(voltage_amp_mapper.keys()))
    return voltage_amp_mapper[volt_suffix]

def frequency_suffix_to_scientific_str(freq_suffix):
    """Convert frequency suffix to scientific. *i.e.* 'MHz' -> 'e6'

    args:
        freq_suffix (str): Suffix to convert

    returns:
        (str): Scientific notation str
    """
    freq_suffix = freq_suffix.replace('H', 'h').replace('Z', 'z')
    assert freq_suffix in set(freq_mapper.keys()), "Suffix {} not in freq_mapper. Allowed keys are {}".format(freq_suffix, list(freq_mapper.keys()))
    return freq_mapper[freq_suffix]

def current_suffix_to_scientific_str(current_suffix):
    """Convert current suffix to scientific. *i.e.* 'mA' -> 'e-3'

    args:
        current_suffix (str): Suffix to convert

    returns:
        (str): Scientific notation str
    """
    assert current_suffix in set(freq_mapper.keys()), "Suffix {} not in freq_mapper. Allowed keys are {}".format(current_suffix, list(freq_mapper.keys()))
    return freq_mapper[current_suffix]

def get_number_and_suffix(string):
    """Return number and suffix of a string.

    args:
        string (str): String.

    returns:
        (tuple): number, suffix

    examples:
        ```
        >>> get_number_and_suffix('1khz')
        > (1.0, 'khz')
        ```


    """
    return _get_number_and_suffix(string)

def _get_number_and_suffix(string):
    """Return number and suffix of a string. e.g. 1khz will return (1.0, 'khz').

    args:
        string (str): String.

    returns:
        (tuple): number, suffix


    """
    iteration = 0
    number = np.nan
    while np.isnan(number):
        if iteration >= len(string):
            raise ValueError('unable to find a valid number in str: {}'.format(string))
        try:
            number = float(string[:-(1+iteration)])
        except ValueError:
            iteration+=1
            
    return number, string[-(iteration + 1):]

def scientific_notation(number):
    """Return a string of a number in scientific notation.

    args:
        number (int or float): Number

    returns:
        (str): String of number in scientific notation. 


    """
    return _scientific_notation(number)

def _scientific_notation(number):
    number = float(number)

    if len(str(number).split('e'))>1:
        out = str(number)
    else:
        number_string = str(number)
        before_decimal, after_decimal = number_string.split('.')
        if before_decimal[0] == '0' and len(before_decimal) == 1:
            #the hard case

            n_zeros_after_decimal = 0
            for x in after_decimal:
                if x == '0':
                    n_zeros_after_decimal += 1
                else:
                    break
            exponent = -(1 + n_zeros_after_decimal)
            out = '{}.{}e{}'.format(
                after_decimal[n_zeros_after_decimal], 
                after_decimal[n_zeros_after_decimal+1:],
                exponent
            )
        else:
            #the easy case
            exponent = len(before_decimal) - 1
            out = '{}.{}e{}'.format(
                before_decimal[0], 
                before_decimal[1:] + after_decimal, 
                exponent
            )
    return out