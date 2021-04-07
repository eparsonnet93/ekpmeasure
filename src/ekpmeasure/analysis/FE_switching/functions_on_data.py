import pandas as pd
import numpy as np
from scipy.integrate import cumtrapz
import warnings
from scipy import signal

__all__ = (
	'polarization_transients_from_dps', 
	'switching_times_from_polarization_transients', 
	'get_dps',
	'find_start_reset_and_delete_before',
	'reset_time', 
	'get_polarization_transients_from_dps', 
	'get_saturation_and_switching_time',
	'smooth', 
	'subtract_median_of_lastN'
	)

def get_startarg_1d(p, cutoff = 0.01):
    """returns the index of where p (could be p1 or p2) is first greater than cutoff"""
    assert type(p) == type(np.array([])), "p must be numpy array"
    if len(p.shape) > 1:
        raise ValueError('p must be 1dimensional. not shape {}'.format(p.shape))
        
    arg = np.argwhere(p > cutoff).flatten()[0]
    return arg

def get_starttime_from_startarg_1d(time, start_arg):
    """return the time at start_arg"""
    assert type(time) == type(np.array([])), "time must be numpy array"
    if len(time.shape) > 1:
        raise ValueError('time must be 1dimensional. currently has shape {}'.format(time.shape))
    return time[start_arg].flatten()[0]

def reset_time(data_dict, key = 'p1', cutoff = 0.01, grace = 10):
    """finds the start of the pulse and resets it to zero time
    ----
    data_dict: (dict) with keys 'time', 'p1', 'p2'
    key: (str) key of data_dict to find where first above cutoff
    cutoff: (float) a voltage value above which to call the start of the pulse
    grace: (int) how many datapoints to include before time = 0

    returns dict with keys 'time', 'p1' and 'p2'
    """
    assert set(data_dict.keys()) == set({'p1', 'p2', 'time'}), "data_dict keys ({}) do not match required keys: {}".format(set(data_dict.keys()), set({'p1', 'p2', 'time'}))
    key = key.lower()
    assert key in set({'p1', 'p2'}), "key {} is not in allowed. must be 'p1' or 'p2'".format(key)
    assert key in set(data_dict.keys()), "key {} does not exist in data_dict keys ({})".format(key, data_dict.keys())
    
    time, p1, p2 = data_dict['time'], data_dict['p1'], data_dict['p2']
    assert time.shape == p1.shape and time.shape == p2.shape, "shapes do not match: time - {}, p1 - {}, p2 - {}".format(time.shape, p1.shape, p2.shape)
    if len(time.shape) > 2:
        raise ValueError('len(time.shape) > 2 meaning the dimensionality of the data is greater than 2. this is not allowed')
    
    #dimensionality of data:
    if len(time.shape) == 1:
        time = time.reshape((1, len(time)))
        p1 = p1.reshape((1, len(p1)))
        p2 = p2.reshape((1, len(p2)))
    
    ndim = time.shape[0]
    
    #which p do we want to use to be above the cutoff?
    p_dict = {'p1':p1, 'p2':p2}
    
    time_list, p1_list, p2_list = [], [], []
    
    for d in range(ndim):
        ttime = time[d, :]
        tp = p_dict[key][d, :]
        arg = get_startarg_1d(tp, cutoff = cutoff)
        start_time = get_starttime_from_startarg_1d(ttime, arg)
        
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
    """calculate the difference between p1 and p2
    ----
    data_dict: (dict) with keys 'time', 'p1', 'p2'

    returns dict with keys 'dp' and 'time'
    """
    p1 = data_dict['p1']
    p2 = data_dict['p2']
    
    if len(p1.shape) == 1:
        p1 = p1.reshape((1, len(p1)))
        p2 = p2.reshape((1, len(p2)))
    
    for i in range(p1.shape[0]):
        if i == 0:
            dp = p1[i,:] - p2[i,:]
        else:
            dp = np.vstack((dp,p1[i,:] - p2[i,:]))
    return {'time':data_dict['time'], 'dp':dp}

def get_polarization_transients_from_dps(data_dict):
    """
    returns integrated dp
    ----
    data_dict: (dict) with keys 'time', 'dp'

    returns dict with keys 'intdp' and 'time'
    """ 
    dp = np.nan_to_num(data_dict['dp'], 0)
    time = np.nan_to_num(data_dict['time'], 0)
    
    if len(dp.shape) == 1:
        dp = dp.reshape((1, len(dp)))
        time = time.reshape(1, len(time))
    
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
    assert key in set(data_dict.keys()), "key {} is does not exist in data_dict".format(key)
    
    to_smooth = np.nan_to_num(data_dict[key], 0)
    
    if len(to_smooth.shape) == 1:
        to_smooth = to_smooth.reshape((1, len(to_smooth)))
        
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
    assert key in set(data_dict.keys()), "key {} is does not exist in data_dict".format(key)
    
    to_subtract = np.nan_to_num(data_dict[key], 0)
    
    if len(to_subtract.shape) == 1:
        to_subtract = to_subtract.reshape((1, len(to_subtract)))
        
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
    assert 'intdp' in set(data_dict.keys()), '"intdp" does not exist in data_dict'
    assert 'time' in set(data_dict.keys()), "'time' does not exist in data_dict"
    
    intdp = data_dict['intdp']
    time = data_dict['time']
    
    if len(intdp.shape) == 1:
        intdp = intdp.reshape((1, len(intdp)))
        time = time.reshape((1, len(time)))
    
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

def find_start_reset_and_delete_before(data_dict, cutoff = 0.01, grace = 10):
	"""finds the start of the pulse and resets it to zero time
	----
	data_dict: (dict) with keys 'time', 'p1', 'p2'
	cutoff: (float) a voltage value above which to call the start of the pulse
	grace: (int) how many datapoints to include before time = 0
	
	returns dict with keys 'time', 'p1' and 'p2'
	"""
	warnings.showwarning('find_start_reset_and_delete_before is deprecated. please use reset_time()', DeprecationWarning, '', 0,)
	time = data_dict['time']
	p1 = data_dict['p1']
	p2 = data_dict['p2']
	time_list, p1_list, p2_list = [],[],[]
	for i in range(p1.shape[0]):
		try:
			tp1 = p1[i, :]
			tp2 = p2[i, :]
			ttime = time[i,:]
		except IndexError:
			tp1 = p1[:]
			tp2 = p2[:]
			ttime = time[:]
		where_start = np.argwhere(tp1 > cutoff).flatten()[0]
		grace = 10
		
		ttime = ttime[where_start-grace:] - ttime[where_start]
		tp1 = tp1[where_start-grace:]
		tp2 = tp2[where_start-grace:]
		time_list.append(list(ttime))
		p1_list.append(list(tp1))
		p2_list.append(list(tp2))
	 
	max_number_of_timestamps = max([len(x) for x in time_list])
	for time_series, p1_series, p2_series in zip(time_list, p1_list, p2_list):
		l = len(time_series)
		nnans_to_add = max_number_of_timestamps - l
		for ijk in range(nnans_to_add):
			time_series.append(np.nan)
			p1_series.append(np.nan)
			p2_series.append(np.nan)
	
	time_out = np.array(time_list[0])
	p1_out = np.array(p1_list[0])
	p2_out = np.array(p2_list[0])
	for i, tlist in enumerate(time_list[1:]):
		time_out = np.vstack((time_out, tlist))
		p1_out = np.vstack((p1_out, p1_list[i]))
		p2_out = np.vstack((p2_out, p2_list[i]))
	
	out = {'time':time_out, 'p1':p1_out, 'p2':p2_out}
	return out


def polarization_transients_from_dps(data_dict):
	"""
	returns integrated dp
	----
	data_dict: (dict) with keys 'time', 'dp'
	
	returns dict with keys 'intdp' and 'time'
	"""
	warnings.showwarning('polarization_transients_from_dps is deprecated. please use get_polarization_transients_from_dps()', DeprecationWarning, '', 0,)
	dp = data_dict['dp']
	time = data_dict['time']
	for i in range(dp.shape[0]):
		if i == 0:
			intdp = cumtrapz(dp[i,:], x = time[i,:])
			intdp = np.concatenate((np.array([0]), intdp))
		else:
			tintdp = cumtrapz(dp[i,:], x = time[i,:])
			tintdp = np.concatenate((np.array([0]), tintdp))
			intdp = np.vstack((intdp,tintdp))
	return {'time':data_dict['time'], 'intdp':intdp}

def switching_times_from_polarization_transients(data_dict, percentile = 70, npoints_on_end_for_saturation = 20):
	"""
	extract switching time for polarization transient
	----
	data_dict: (dict) with keys 'time', 'intdp'
	percentile: (float) what percent of the saturation to define as switching time. cutoff for switching defined as (percentile/100)*average(intdp[-npoints_on_end_for_saturation:])
	npoints_on_end_for_saturation: (int) how many points to average over at the end to define saturation
	"""
	warnings.showwarning('switching_times_from_polarization_transients is deprecated. please use get_saturation_and_switching_time()', DeprecationWarning, '', 0,)
	time = data_dict['time'].copy()
	intdp = data_dict['intdp'].copy()
	for i in range(intdp.shape[0]):
		try:
			currentdata = np.nan_to_num(intdp[i,:], 0)
			currenttime = np.nan_to_num(time[i,:], 0)
		except IndexError: #1d data
			currentdata = np.nan_to_num(intdp[:], 0)
			currenttime = np.nan_to_num(time[:], 0)
			
		cutoff = np.mean(currentdata[-npoints_on_end_for_saturation:])*percentile/100
		try:
			where_over_percentile = np.argwhere(currentdata > cutoff).flatten()[0]
			time_at_over_percentile = currenttime[where_over_percentile]
		except:
			time_at_over_percentile = np.nan
		if i == 0:
			times_at_over_percentile = time_at_over_percentile
		else:
			times_at_over_percentile = np.vstack((times_at_over_percentile, time_at_over_percentile))        
	return {'switching_time':times_at_over_percentile}