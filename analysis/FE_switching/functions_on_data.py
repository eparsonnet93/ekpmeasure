import pandas as pd
import numpy as np
from scipy.integrate import cumtrapz

__all__ = (
	'polarization_transients_from_dps', 
	'switching_times_from_polarization_transients', 
	'get_dps',
	'find_start_reset_and_delete_before'
	)

def find_start_reset_and_delete_before(data_dict, cutoff = 0.01, grace = 10):
	"""finds the start of the pulse and resets it to zero time
	----
	data_dict: (dict) with keys 'time', 'p1', 'p2'
	cutoff: (float) a voltage value above which to call the start of the pulse
	grace: (int) how many datapoints to include before time = 0
	
	returns dict with keys 'time', 'p1' and 'p2'
	"""
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

def get_dps(data_dict):
	"""calculate the difference between p1 and p2
	----
	data_dict: (dict) with keys 'time', 'p1', 'p2'
	
	returns dict with keys 'dp' and 'time'
	"""
	p1 = data_dict['p1']
	p2 = data_dict['p2']
	for i in range(p1.shape[0]):
		if i == 0:
			dp = p1[i,:] - p2[i,:]
		else:
			dp = np.vstack((dp,p1[i,:] - p2[i,:]))
	return {'time':data_dict['time'], 'dp':dp}

def polarization_transients_from_dps(data_dict):
	"""
	returns integrated dp
	----
	data_dict: (dict) with keys 'time', 'dp'
	
	returns dict with keys 'intdp' and 'time'
	"""
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