from ..functions_on_data import iterable_data_array, data_array_builder

import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

__all__ = ('window', 'fit_sine', 'center_yaxis', 'shift')

def window(data_dict, key = 'Y', window_size = 5, interval = [0,270]):
    """
    Window the data by angle (i.e., 'Measured Angle (deg)') as specifed by key. 

    args:
        data_dict (dict): Data dict
        key (str or key): The data key to operate on
        window_size (int): How big of a window to use
        interval (2-tuple or array-like): The interval over which to window

    returns:
        (dict): dict of windowed data, with keys 'angle' and key

    """
    ida = iterable_data_array(data_dict, key)
    angle_ida = iterable_data_array(data_dict, 'Measured Angle (deg)')
    
    angle_centers = [window_size*i + window_size/2 - interval[0] for i in range(int((interval[1]-interval[0])/window_size))]
    windows = [(center - window_size/2, center + window_size/2) for center in angle_centers]

    angle, voltage = data_array_builder(), data_array_builder()

    for ang, y in zip(angle_ida, ida):
        
        tangle, tvoltage = [], []
    
        for window in windows:
            indexer = (ang>window[0])*(ang<=window[1])
            data_to_average = y[indexer]
            average = np.mean(data_to_average)
            tvoltage.append(average)
            tangle.append(np.mean(window))
        tangle = np.array(tangle)
        tvoltage = np.array(tvoltage)
        angle.append(tangle)
        voltage.append(tvoltage)

        
    return {'angle':angle.build(), key:voltage.build()}

def center_yaxis(data_dict, key = 'Y',top_percentile = 90, bottom_percentile = 'symmetric'):
    """
    Center the data specified by key to ~zero. This operates by subtracting the mean(top_percentile(data), bottom_percentile(data)) from each data point. It is recommended you use symmetric top and bottom percentiles, (i.e., 90, 10 or 80, 20) though is not required.

    args:
        data_dict (dict): Data dict
        key (str or key): Data key to operate on
        top_percentile (int or float): Top percentile
        bottom_percentile (int or float or str): Default is 'symmetric', any other str will error. Default behavior will use symmetric value as given by top_percentile (i.e. if top_percentile = 90, bottom_percentile will be set to 10)

    returns:
        (dict): dict with all original keys and specified key centered at zero.  

    """
    ida = iterable_data_array(data_dict, key)
    out = data_array_builder()

    if bottom_percentile == 'symmetric':
        bottom_percentile = 100 - top_percentile
    else:
        pass

    for row in ida:
        center = np.mean((np.percentile(row, top_percentile), np.percentile(row, bottom_percentile)))
        out.append(row - center)
        
    to_return = data_dict.copy()
    to_return.update({key:out.build()})
    return to_return

def fit_sine(data_dict, anglekey = 'angle', key = 'Y', periodicity = 1, units = 'degrees'):
    """
    Fit data to sine wave with specified periodicity. 

    args:
        data_dict (dict): Data dict.
        anglekey (str or key): Key specifying angle.
        key (str or key): Key to fit to sine
        periodicity (int or float): Periodicity in units of 2pi, i.e. periodicity = 1 corresponds to 2pi (360 degrees) periodicity
        units (str): angle units for the data specified by anglekey 'degrees' or 'radians'

    returns:
        (dict): Fit data. Keys: 'params' - fit parameters, 'fakex' - fake angle data (for plotting), 'simulated' - simulated fit data (for plotting)
    """
    if units != 'degrees' and units != 'radians':
        raise ValueError('units must be either degrees or radians. Not {}'.format(units))

    ang_ida = iterable_data_array(data_dict, anglekey)
    ida = iterable_data_array(data_dict, key)

    def sin(x, a, phase):
        return a*np.sin(periodicity*x + phase)

    out_params = data_array_builder()
    out_fake_angle = data_array_builder()
    out_simulation = data_array_builder()
    for x, y in zip(ang_ida, ida):
        where_nan = np.isnan(x)+np.isnan(y)
        where_not_nan = [False if b else True for b in where_nan]
        x = x[where_not_nan]
        y = y[where_not_nan]
        if units == 'degrees':
            x = x*np.pi/180
        popt, pcov = curve_fit(sin, x, y)
        out_params.append(popt)
        fakex = np.linspace(min(x), max(x), 100)
        if units == 'degrees':
            out_fake_angle.append(fakex*180/np.pi)
        else:
            out_fake_angle.append(fakex)
        out_simulation.append(sin(fakex, *popt))
        
    return {'params':out_params.build(), 'fakex':out_fake_angle.build(), 'simulated':out_simulation.build()}

def shift(data_dict, shift_amnt, key):
    """
    Shift the data by a constant amount. 

    args:
        data_dict (dict): Data dict
        shift_amnt (float or int): Amount to offset data by
        key (str or key): Data key to shift.

    returns:
        (dict): all keys are maintained, specified key is shifted by shift_amnt

    """
    out_dict = data_dict.copy()
    ida = iterable_data_array(data_dict, key)
    
    out = data_array_builder()
    
    for i in ida:
        out.append(i + shift_amnt)
    out_dict.update({key:out.build()})
    return out_dict