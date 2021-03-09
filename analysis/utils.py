import pandas as pd
import numpy as np

from .core import Dataset
from .core import _convert_ITP_to_path_to_index

__all__ = ('merge',)

def merge(datasets):
	"""merge datasets. need docstring"""
	
	if not hasattr(datasets, '__iter__'):
		raise TypeError('datasets is not iterable.')
		
	columns = datasets[0].columns
	for dset in datasets[1:]:
		if (columns != dset.columns).all():
			raise ValueError('supplied datasets have different columns!')
	
	for i, dset in enumerate(datasets):
		if i == 0:
			new_path = dset.index_to_path
			new_df = pd.DataFrame(dset)
		else:
			new_path = pd.concat((new_path, dset.index_to_path), ignore_index = True)
			new_df = pd.concat((new_df, pd.DataFrame(dset)), ignore_index = True)
			
	path = _convert_ITP_to_path_to_index(new_path)
	
	return Dataset(path,new_df)