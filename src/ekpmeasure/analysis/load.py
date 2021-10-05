import os 
import pandas as pd
import numpy as np

import warnings

from .core import Dataset

__all__ = ('load_Dataset', 'generate_meta_data')

def load_Dataset(path, meta_data = None):
	"""
	Load a dataset from path. Path must contain pickle file ``'meta_data'``. 

	args:
		path (str): Path to data
		meta_data (pandas.DataFrame): meta_data if one wishes to provide different meta_data from that provided in path. 

	returns: 
		Dataset
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

def generate_meta_data(path, mapper, pass_path = False, pointercolumn = 'filename', overwrite = False):
	"""
	Generate meta_data from a path for a given mapper function. 

	args:
		path (str): Specify the path to the directory
		mapper ( function ) : filename (str) -> dict. A function which operates on a single file name in order to get the columns (dict key) and values (dict value) for meta_data of that file.
		pointercolumn (str) : The name of the pointercolumn in the created meta_data
		overwrite (bool) : True will overwrite any existing meta_data in path. 
	"""
	if 'meta_data' in set(os.listdir(path)):
		if not overwrite:
			yn = input('this path ({}) already has meta_data, do you wish to recreate it? (y/n)'.format(path))
			if yn.lower() != 'y':
				print('skipping. NOT overwriting.')
				return
			else:
				print('overwriting.')

	for file in os.listdir(path):
		try:
			if pass_path:
				meta_data = pd.DataFrame(mapper(file, path = path), index = [0])
			else:
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
