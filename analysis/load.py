import os 
import pandas as pd
import numpy as np

import warnings

from .core import Dataset

__all__ = ('load_Dataset', 'generate_meta_data')

def load_Dataset(path, meta_data = None):
	"""load a Dataset from a path
	----
	
	path: (str) path to data
	meta_data: (pandas.DataFrame) meta_data
	"""
	return Dataset(path, _build_df(path, meta_data))

def _build_df(path, meta_data):
	if type(meta_data) == type(None):
		try:
			return pd.read_pickle(path + 'meta_data')
		except FileNotFoundError:
			print('meta_data does not exist in path {} you may want to create it with generate_meta_data()'.format(path))
			return pd.DataFrame()
	else:
		return meta_data

def generate_meta_data(path, mapper, pointercolumn = 'filename'):
	"""
	generate meta_data from a path.
	----

	mapper: (function: filename (str) -> dict) operates on a single file name in order to get the columns (dict key) and values (dict value) for meta_data of that file 
	"""
	if 'meta_data' in set(os.listdir(path)):
		yn = input('this path ({}) already has meta_data, do you wish to recreate it? (y/n)'.format(path))
		if yn.lower() != 'y':
			print('skipping. NOT overwriting.')
			return
		else:
			print('overwriting.')

	for file in os.listdir(path):
		try:
			meta_data = pd.DataFrame(mapper(file), index = [0])
		except Exception as e:
			print('unable to process file: {} \nError: {}'.format(file, e))
			continue
		try:
			existing_meta_data = pd.concat([existing_meta_data, meta_data], ignore_index = True)
		except NameError:
			existing_meta_data = meta_data.copy()

	if pointercolumn not in set(existing_meta_data.columns): 
		warnings.showwarning('there is no map to key "{}" in mapping function "{}" provided\nEnsure self.pointercolumn property has been set appropriately or else you will be unable to retrieve data'.format(pointercolumn, mapper.__name__), SyntaxWarning, '', 0,)

	existing_meta_data.to_pickle(path+'meta_data')
	print('meta_data saved to {}'.format(path))
	return
