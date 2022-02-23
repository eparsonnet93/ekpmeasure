from ....utils import (get_number_and_suffix,
    time_to_sci_mapper,
    )
import numpy as np

__all__ = ('frequency_from_delay',)


def frequency_from_delay(delay):
    """Determine what frequency to use to match a specified delay time.

    args:
        delay (str): Delay time. Example '1us'

    returns:
        frequency (float): Frequency in Hz.

    """
    d_number, d_suffix = get_number_and_suffix(delay)
    float_delay = float(str(d_number) + time_to_sci_mapper[d_suffix])

    frequency = np.round(1/float_delay, 0)

    return frequency