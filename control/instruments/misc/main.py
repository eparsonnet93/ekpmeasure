import numpy as np

__all__ = ('_get_number_and_suffix','freq_mapper', 'current_amp_mapper', 'sci_to_time_mapper', '_scientific_notation')

freq_mapper = {'khz':'e3', 'hz':'e0'}
current_amp_mapper = {'ma':'e-3', 'ua':'e-6'}
sci_to_time_mapper = {'e0':'s', 'e3':'ks', 'e-3':'ms', 'e-6':'us', 'e-9':'ns'}

def _get_number_and_suffix(string):
    """return number and suffix of a string. e.g. 1khz will return (1.0, 'khz')"""
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