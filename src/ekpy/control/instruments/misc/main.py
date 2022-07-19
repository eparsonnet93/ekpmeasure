import numpy as np
import warnings

__all__ = ('get_number_and_suffix', '_get_number_and_suffix','freq_mapper', 'current_amp_mapper', 
    'sci_to_time_mapper', 'time_to_sci_mapper', '_scientific_notation', 'voltage_amp_mapper')

freq_mapper = {'Mhz':'e6','khz':'e3', 'hz':'e0'}
current_amp_mapper = {'ma':'e-3', 'ua':'e-6'}
sci_to_time_mapper = {'e0':'s', 'e3':'ks', 'e-3':'ms', 'e-6':'us', 'e-9':'ns'}
time_to_sci_mapper = {'ms':'e-3', 'us':'e-6', 'ns':'e-9', 'ps':'e-12', 's':'e0', 'ks':'e3'}
voltage_amp_mapper = {'mv':'e-3', 'v':''}


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
    warnings.showwarning("get_number_and_suffix will be deprecated. Please use ekpmeasure.universal.get_number_and_suffix", DeprecationWarning, '', 0)
    return _get_number_and_suffix(string)

def _get_number_and_suffix(string):
    """Return number and suffix of a string. e.g. 1khz will return (1.0, 'khz').

    args:
        string (str): String.

    returns:
        (tuple): number, suffix


    """
    warnings.showwarning("_get_number_and_suffix will be deprecated. Please use ekpmeasure.universal._get_number_and_suffix", DeprecationWarning, '', 0)
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
    warnings.showwarning("scientific_notation will be deprecated. Please use ekpmeasure.universal.scientific_notation", DeprecationWarning, '', 0)
    return _scientific_notation(number)

def _scientific_notation(number):
    warnings.showwarning("_scientific_notation will be deprecated. Please use ekpmeasure.universal._scientific_notation", DeprecationWarning, '', 0)
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