import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

__all__ = ('convert_pCum2_to_uCcm2', 'fit_diode')


def convert_pCum2_to_uCcm2(value):
    """Convert from picocoulombs/um^2 to microcoulombs/cm^2. This is simply multpilying by 100, but it's a calculation I do a lot and always have to look up to make sure I'm correct.

    args:
        value (float): Value to convert.

    returns:
        (float): value*100

    """
    return value*100


def diode(x, a, b):
    return a*(np.exp(b*x) - 1)



def fit_diode(drive, current, time):
	"""Return a diode fitting function for the non-switching sections of a current loop. The Positive and Negative contributions are fit indepedently.

	args:
		drive (array-like): Drive voltage data
		current (array-like): Observed current data
		time (array-like): Time data

	returns:
		(callable): Fitting function, f : f(x) -> diode current at x
	"""

	grad_drive = np.gradient(drive)
	drive_increasing_indexer = grad_drive>0
	drive_decreasing_indexer = grad_drive<0
	positive_indexer = drive>0
	negative_indexer = drive<0

	positive_fit_indexer = (drive_decreasing_indexer)&(positive_indexer)
	negative_fit_indexer = (drive_increasing_indexer)&(negative_indexer)


	# positive case
	indexer = positive_fit_indexer
	X, Y = drive[indexer], current[indexer]
	pospop, poscov = curve_fit(diode, X, Y)

	# negative case
	indexer = negative_fit_indexer
	X, Y = drive[indexer], current[indexer]
	negpop, negcov = curve_fit(diode, -1*X, -1*Y)

	def _fit(x):
		"""Operates on single value because piecewise"""
		if x<0:
		    return -1*diode(-1*x, *negpop)
		elif x>0:
		    return diode(x, *pospop)
		else:
		    return 0


	def fit(x):
		"""Operates on array-like or single value"""
		if len(x)==1:
			return _fit(x)
		else:
			return np.array([_fit(X) for X in x])

	return fit