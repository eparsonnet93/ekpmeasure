from ..functions_on_data import iterable_data_array, data_array_builder

import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

__all__ = ('mapper', 'window', 'fit_sine', 'center_yaxis', 'shift')


def mapper(fname, path):
    file = path + fname
    with open(file, 'rb') as f:
        lines = f.readlines()

    heading_index = np.nan

    for i, line in enumerate(lines):
        if line.decode("utf-8") == '\r\n':
            heading_index = i
    
    if np.isnan(heading_index):
        raise ValueError('unable to find heading!!!')

    meta_data = {'filename':fname}
    for line in lines[:heading_index]:
        line_string = line.decode("utf-8")
        if '###' in line_string: #case for settings break in header
            continue
        spl = line_string.replace('\n', '').replace('\r', '').replace('\t', '').split(': ')
        try:
            meta_data.update({spl[0]:float(spl[1])})
        except ValueError:
            meta_data.update({spl[0]:spl[1]})
        except IndexError:
            meta_data.update({spl[0]:np.nan})
            
    ### get field ###
    tdf = pd.read_csv(file, skiprows=heading_index, delimiter = '\t')
    field_value = np.round(np.mean(np.round(tdf['Field digital (T)'], 2)), 2)
    meta_data.update({'Field':field_value})
    
    temp = np.round(np.mean(np.round(tdf['T Sample (K)'], 0)), 0)
    meta_data.update({'Temperature Average':temp})
    
    return meta_data

def window(data_dict, key = 'Y', window_size = 5, interval = [0,270]):
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

def center_yaxis(data_dict, key = 'Y',top_percentile = 90, bottom_percentile = 10):
    ida = iterable_data_array(data_dict, key)
    out = data_array_builder()
    for row in ida:
        center = np.mean((np.percentile(row, top_percentile), np.percentile(row, bottom_percentile)))
        out.append(row - center)
        
    to_return = data_dict.copy()
    to_return.update({key:out.build()})
    return to_return

from scipy.optimize import curve_fit
def fit_sine(data_dict, anglekey = 'angle', key = 'Y', periodicity = 1, units = 'degrees'):
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
    out_dict = data_dict.copy()
    ida = iterable_data_array(data_dict, key)
    
    out = data_array_builder()
    
    for i in ida:
        out.append(i + shift_amnt)
    out_dict.update({key:out.build()})
    return out_dict