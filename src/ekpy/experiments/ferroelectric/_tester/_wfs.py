import numpy as np

__all__ = ('standard_bipolar_sine', 'double_bipolar_sine', 'standard_bipolar', 'double_bipolar',
	'semicircle', 'double_semicircle', 'gaussian', 'double_gaussian')

def semicircle(a, T):
	"""Return semicircle bipolar wave with amplitude a (units of V) and period T (units of ms)

	args:
		a (float): Amplitude in Volts
		T (float): Period in ms
	"""
	if T < .01:
		raise ValueError("limit of Ferroelectric Tester")

	count = int(T*1000)

	int_amp = int(2047*a/10)

	wf = []

	for i in range(count):
		if i<=count/2:
			wf.append(np.sqrt(1 - ((i - count/4)/(count/4))**2))
		else:
			wf.append(-1*np.sqrt(1 - ((i - count/2 - count/4)/(count/4))**2))
			

	wf = np.array([int_amp*i + 2047 for i in wf])

	return wf

def double_semicircle(a, T):
	"""Return double semicircle bipolar wave with amplitude a (units of V) and period T (units of ms)

	args:
		a (float): Amplitude in Volts
		T (float): Period in ms
	"""
	wf = np.concatenate(
		(semicircle(a,T/2),semicircle(a,T/2))
	)
	return wf

def gaussian(a, T, sigma='default'):
	if T < .01:
		raise ValueError("limit of Ferroelectric Tester")

	count = int(T*1000)

	int_amp = int(2047*a/10)
	
	if sigma == 'default':
		sigma = count/20
	#sigma = (1/(a*np.sqrt(2*np.pi)))
	mu = count/4

	wf = []

	for i in range(count):
		if i<=count/2:
			#wf.append((1/(sigma*np.sqrt(2*np.pi)))*np.exp(-(i-mu)**2/(2*sigma**2)))
			wf.append((a)*np.exp(-(i-mu)**2/(2*sigma**2)))
		else:
			wf.append(-(a)*np.exp(-(i-count/2-mu)**2/(2*sigma**2)))
			
	wf = np.array([int_amp*i + 2047 for i in wf])
	return wf

def double_gaussian(a, T, sigma='default'):
	wf = np.concatenate(
		(gaussian(a, T/2, sigma), gaussian(a, T/2, sigma))
	)
	return wf

def standard_bipolar(a, T):
	"""Return standard bipolar triangle wave with amplitude a (units of V) and period T (units of ms)

	args:
		a (float): Amplitude in Volts
		T (float): Period in ms

	"""
	if T < .01:
		raise ValueError("limit of Ferroelectric Tester")

	count = int(T*1000)

	int_amp = int(2047*a/10)
	step = 4/(count)

	wf = []

	for i in range(count):
		if i<=count/4:
			wf.append(i*step)
		elif i>count/4 and i<=3*count/4:
			wf.append(wf[i-1]-step)
		else:
			wf.append(wf[i-1]+step)

	wf = np.array([int_amp*i + 2047 for i in wf])

	return wf

def double_bipolar(a, T):
	"""Return double bipolar triangle wave with amplitude a (units of V) and period T (units of ms)

	args:
		a (float): Amplitude in Volts
		T (float): Period in ms

	"""
	wf = np.concatenate((standard_bipolar(a, T/2),standard_bipolar(a, T/2)))

	return wf

def standard_bipolar_sine(a, T):
	"""Return standard bipolar sine wave with amplitude a (units of V) and period T (units of ms)
	
	args:
		a (float): Amplitude in Volts
		T (float): Period in ms
	
	"""
	if T < .01:
		raise ValueError("limit of Ferroelectric Tester")
	
	count = int(T*1000)
	
	int_amp = int(2047*a/10)
	
	wf = np.array([int_amp*np.sin(2*np.pi*i/(count)) + 2047 for i in range(count)])
	
	return wf


def double_bipolar_sine(a, T):
	"""Return standard bipolar sine wave with amplitude a (units of V) and period T (units of ms)
	
	args:
		a (float): Amplitude in Volts
		T (float): Period in ms
		
	"""
	if T < .01:
		raise ValueError("limit of Ferroelectric Tester")
	
	count = int(T*1000)
	
	int_amp = int(2047*a/10)
	
	wf = np.array([int_amp*np.sin(4*np.pi*i/(count)) + 2047 for i in range(count)])
	
	return wf