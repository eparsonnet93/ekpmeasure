import pandas as pd
import numpy as np
from scipy.integrate import cumtrapz
import warnings
from scipy import signal

from ..functions_on_data import _fod_dimensionality_fixer

__all__ = (
	'get_dps',
	'reset_time', 
	'get_polarization_transients_from_dps', 
	'get_saturation_and_switching_time',
	'smooth', 
	'subtract_median_of_lastN'
	)

def _get_startarg_1d(p, cutoff = 0.01):
    """returns the index of where p (could be p1 or p2) is first greater than cutoff"""
    assert type(p) == type(np.array([])), "p must be numpy array"
    if len(p.shape) > 1:
        raise ValueError('p must be 1dimensional. not shape {}'.format(p.shape))
        
    arg = np.argwhere(p > cutoff).flatten()[0]
    return arg

def _get_starttime_from_startarg_1d(time, start_arg):
    """return the time at start_arg"""
    assert type(time) == type(np.array([])), "time must be numpy array"
    if len(time.shape) > 1:
        raise ValueError('time must be 1dimensional. currently has shape {}'.format(time.shape))
    return time[start_arg].flatten()[0]

def reset_time(data_dict, key = 'p1', cutoff = 0.01, grace = 10):
    """Finds the start of the data (defined as first time data[key]>cutoff) and resets it to zero time

    args:
        data_dict (dict): data dict. 
        key (str):  key of data_dict to find where first above cutoff
        cutoff (float):  A voltage value above which to call the start of the pulse
        grace (int):  How many datapoints to include before new time = 0

    returns 
        out: (dict) with keys 'time', 'p1' and 'p2'
    """
    assert set(data_dict.keys()) == set({'p1', 'p2', 'time'}), "data_dict keys ({}) do not match required keys: {}".format(set(data_dict.keys()), set({'p1', 'p2', 'time'}))
    key = key.lower()
    assert key in set({'p1', 'p2'}), "key {} is not in allowed. must be 'p1' or 'p2'".format(key)
    assert key in set(data_dict.keys()), "key {} does not exist in data_dict keys ({})".format(key, data_dict.keys())
    
    #dimensionality of data:
    time, p1, p2 = _fod_dimensionality_fixer(data_dict, check_key = 'time', keys_to_fix = ['time', 'p1', 'p2'])

    assert time.shape == p1.shape and time.shape == p2.shape, "shapes do not match: time - {}, p1 - {}, p2 - {}".format(time.shape, p1.shape, p2.shape)
    if len(time.shape) > 2:
        raise ValueError('len(time.shape) > 2 meaning the dimensionality of the data is greater than 2. this is not allowed')
    
    ndim = time.shape[0]
    
    #which p do we want to use to be above the cutoff?
    p_dict = {'p1':p1, 'p2':p2}
    
    time_list, p1_list, p2_list = [], [], []
    
    for d in range(ndim):
        ttime = time[d, :]
        tp = p_dict[key][d, :]
        arg = _get_startarg_1d(tp, cutoff = cutoff)
        start_time = _get_starttime_from_startarg_1d(ttime, arg)
        
        new_1d_time = ttime[arg - grace:] - start_time
        tp1 = p1[d, :]
        tp2 = p2[d, :]
        new_p1 = tp1[arg - grace:]
        new_p2 = tp2[arg - grace:]
        
        #in order to account for nans in vstacking later we need to keep allow for different shapes
        time_list.append(new_1d_time)
        p1_list.append(new_p1)
        p2_list.append(new_p2)
        
    max_number_of_timestamps = max([len(x) for x in time_list])
    for i in range(len(time_list)):
        l = len(time_list[i])
        nnans_to_add_to_front = max_number_of_timestamps - l
        for ticker in range(nnans_to_add_to_front):
            time_list[i] = np.concatenate(([np.nan], time_list[i]))
            p1_list[i] = np.concatenate(([np.nan], p1_list[i]))
            p2_list[i] = np.concatenate(([np.nan], p2_list[i]))

    time_out = np.array(time_list[0])
    p1_out = np.array(p1_list[0])
    p2_out = np.array(p2_list[0])
    for i, tlist in enumerate(time_list[1:]):
        time_out = np.vstack((time_out, tlist))
        p1_out = np.vstack((p1_out, p1_list[i]))
        p2_out = np.vstack((p2_out, p2_list[i]))

    out = {'time':time_out, 'p1':p1_out, 'p2':p2_out}
        
    return out

def get_dps(data_dict):
    """Calculate the difference between data keys 'p1' and 'p2'

    args:
        data_dict (dict): dict with keys 'time', 'p1', 'p2'

    returns:
        out (dict) : dict with keys 'dp' and 'time'. Key 'dp' corresponds to 'p1' - 'p2' for each timestep.
    """
    #dimensionality
    p1, p2 = _fod_dimensionality_fixer(data_dict, check_key = 'p1', keys_to_fix = ['p1', 'p2'])
    
    for i in range(p1.shape[0]):
        if i == 0:
            dp = p1[i,:] - p2[i,:]
        else:
            dp = np.vstack((dp,p1[i,:] - p2[i,:]))
    return {'time':data_dict['time'], 'dp':dp}

def get_polarization_transients_from_dps(data_dict):
    """
    Integrate dps.

    args:
        data_dict (dict): dict with keys 'time', 'dp'

    returns:
        out (dict): dict with keys 'intdp' and 'time'. 'intdp' is scipy.integrate.cumtrapz(dp, x = 'time')
    """ 

    #dimensionality
    dp, time = _fod_dimensionality_fixer(data_dict, check_key = 'dp', keys_to_fix = ['dp', 'time'])

    dp = np.nan_to_num(dp, 0)
    time = np.nan_to_num(time, 0)
    
    for i in range(dp.shape[0]):
        if i == 0:
            intdp = cumtrapz(dp[i,:], x = time[i,:])
            intdp = np.concatenate((np.array([0]), intdp))
        else:
            tintdp = cumtrapz(dp[i,:], x = time[i,:])
            tintdp = np.concatenate((np.array([0]), tintdp))
            intdp = np.vstack((intdp,tintdp))
    return {'time':data_dict['time'], 'intdp':intdp}

def smooth(data_dict, key='dp', N = 3, Wn = 0.05):
    """
    Apply butterworth filter (scipy.signal.butter) to specified key of data.

    args:
        data_dict (dict): Data
        key (str or key): Specify the key to apply filter to
        N (int): The order of the filter
        Wn (array-like): The critical frequency or frequencies. For lowpass and highpass filters, Wn is a scalar; for bandpass and bandstop filters, Wn is a length-2 sequence. For a Butterworth filter, this is the point at which the gain drops to 1/sqrt(2) that of the passband (the “-3 dB point”). For digital filters, Wn are in the same units as fs. By default, fs is 2 half-cycles/sample, so these are normalized from 0 to 1, where 1 is the Nyquist frequency. (Wn is thus in half-cycles / sample.) For analog filters, Wn is an angular frequency (e.g. rad/s).

    returns: 
        out (dict): dict with same as original keys. 

    """
    assert key in set(data_dict.keys()), "key {} is does not exist in data_dict".format(key)

    to_smooth = _fod_dimensionality_fixer(data_dict, check_key = key, keys_to_fix = [key])
    
    to_smooth = np.nan_to_num(to_smooth, 0)
        
    ndims = to_smooth.shape[0]
    out = data_dict.copy()
    
    for d in range(ndims):
        b, a = signal.butter(N, Wn)
        X = to_smooth[d, :]
        sig = signal.filtfilt(b, a, X)
        try:
            for_out = np.vstack((for_out, sig))
        except NameError:
            for_out = sig.copy()
    out.update({key:for_out})
    return out

def subtract_median_of_lastN(data_dict, key = 'dp', N=20):
    """
    Subtract the median of the last N samples. This may be used to account for constant offsets in the noise floor, for example.

    args:
        data_dict (dict): Data
        key (str or key): Which key to use.
        N ( int ) : The number of points to subtract median of.

    returns: 
        out ( dict ): dict with same as original keys. 

    """
    assert key in set(data_dict.keys()), "key {} is does not exist in data_dict".format(key)

    data_dict.update({key:np.nan_to_num(data_dict[key], 0)})
    
    to_subtract,  = _fod_dimensionality_fixer(data_dict, check_key = key, keys_to_fix = [key])
        
    ndims = to_subtract.shape[0]
    out = data_dict.copy()
    
    for d in range(ndims):
        X = to_subtract[d, :]
        median = np.median(X[-N:]).flatten()[0]
        sig = X - median
        try:
            for_out = np.vstack((for_out, sig))
        except NameError:
            for_out = sig.copy()
    out.update({key:for_out})
    return out

def get_saturation_and_switching_time(data_dict, n_points_for_saturation=50, 
                                      top_percent = 90, bottom_percent = 10):

    """
    Get the saturation and switching time for data. Calculates saturation value as average of n points (n_points_for_saturation) at the end of the data. Calculates switching time as time between bottom_percent and top_percent, both calcuated as percentages of saturation.

    args:
        data_dict (dict): Data
        n_points_for_saturation (int): The number of points to use at the end of the data to calculate the saturation value (mean).
        top_percent (int or float): The percent of saturation to use as switching completion.
        bottom_percent (int or float): The percent of saturaiton to use as switching start commencement. 

    returns: 
        out (dict): dict with keys 'saturation' and 'switching_time'

    """

    assert 'intdp' in set(data_dict.keys()), '"intdp" does not exist in data_dict'
    assert 'time' in set(data_dict.keys()), "'time' does not exist in data_dict"

    intdp, time = _fod_dimensionality_fixer(data_dict, check_key = 'intdp', keys_to_fix = ['intdp', 'time'])
    
    ndims = intdp.shape[0]
    out = {}
    
    for d in range(ndims):
        try:
            X = intdp[d, :]
            ttime = time[d, :]
            #saturation 
            saturation = np.mean(X[-n_points_for_saturation:])
            #define switching time as time from 10% of sat to 90% of sat
            arg_at_topsat = np.argwhere(X > saturation*top_percent/100).flatten()[0]
            arg_at_bottomsat = np.argwhere(X > saturation*bottom_percent/100).flatten()[0]
            time_at_top, time_at_bottom = ttime[arg_at_topsat], ttime[arg_at_bottomsat]

            t_switch = np.array([time_at_top - time_at_bottom])
            saturation = np.array([saturation])

            try:
                for_out_a = np.vstack((for_out_a, saturation))
                for_out_b = np.vstack((for_out_b, t_switch))
            except NameError:
                for_out_a = saturation
                for_out_b = t_switch
        except:
            continue
            
    out.update({'saturation':for_out_a})
    out.update({'switching_time':for_out_b})
        
    return out


####### deprecated below