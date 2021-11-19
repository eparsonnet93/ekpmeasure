import os 
import pandas as pd
import numpy as np

import warnings
import pickle
import ast

from .core import Dataset

__all__ = ('load_Dataset', 'generate_meta_data', 'read_ekpds')

def load_Dataset(path, meta_data = None):
	"""
	Load a dataset from path. Path must contain pickle file ``'meta_data'``. 

	args:
		path (str): Path to data
		meta_data (pandas.DataFrame): meta_data if one wishes to provide different meta_data from that provided in path. 

	returns: 
		(Dataset): Dataset 
	"""
	files = list(os.listdir(path))
	existing_ekpds = []
	for file in files:
		if '.ekpds' in file:
			existing_ekpds.append(file)

	if len(existing_ekpds) != 0:
		warnings.showwarning('There exist .ekpds files ({}) in this directory. If you want to load those Datasets, be sure to use ``.read_ekpds``'.format(existing_ekpds), UserWarning, '', 0)

	return Dataset(path, _build_df(path, meta_data))


def read_ekpdat(filename):
	"""Read Data from `.ekpdat` file.

	args:
		filename (str): Path to file

	returns:
		(Data): Data
	"""

def read_ekpds(filename):
	"""Read a Dataset from `.ekpds` file.

	args:
		filename (str): Path to file

	returns:
		(Dataset): Dataset

	"""

	with open(filename, 'rb') as f:
		out = f.read()

	_location1 = out.find(b'########') #up to here is preamble, after is readfileby
	preamble = pickle.loads(out[:_location1])
	preamble_spl = preamble.split('|')
	preamble_dict = {}

	y = None
	for x in preamble_spl:
		if 'pointercolumn' in x:
			key, value = x.split(':')
			preamble_dict.update({key:value})
		else:
			if type(y) == type(None):
				y = x
			else:
				raise ValueError('error in load. expected 2 items in preamble, recieved at least 3. This likely originated from a change in .to_ekpds without appropriate changes to reading ekpds.')

	assert 'path:' in y, '"path:" not in preamble, or incorrectly passed.'
	path = ast.literal_eval(y.split('path:')[-1])
	preamble_dict.update({'path':path})

	readfileby = pickle.loads(out[_location1+8:])
	_location2 = out.find(b'##|##|##|##') #after this is dset
	meta_data = pickle.loads(out[_location2+11:])
	
	return Dataset(preamble_dict['path'], pd.DataFrame(meta_data), readfileby, pointercolumn=preamble_dict['pointercolumn'])

def _build_df(path, meta_data):

	# I have noticed I'm getting an attribute error when the pickle file is created by a different version of pandas... TODO find the origin of this error, for now, updating to store meta_data as a csv as well in control.experiment
	if type(meta_data) == type(None):
		try:
			return pd.read_pickle(path + 'meta_data')
		except FileNotFoundError:
			try:
				return pd.read_csv(path + 'meta_data.csv')
			except FileNotFoundError:
				print('No file named "meta_data" exists in path "{}", you may want to create one or both of these with `.generate_meta_data()`'.format(path, path))
				return pd.DataFrame()
		except AttributeError:
			try:
				return pd.read_csv(path + 'meta_data.csv')
			except FileNotFoundError:
				print('Pickle file "meta_data" exists in path "{}", but failed to load (likely do to incompatible pandas versions). Backup, "meta_data.csv" does not exist in "{}", you may want to create one or both of these with `.generate_meta_data()`'.format(path, path))
				return pd.DataFrame()
	else:
		return meta_data

def generate_meta_data(path, mapper, pass_path = False, pointercolumn = 'filename', overwrite = False):
	"""
	Generate meta_data from a path for a given mapper function. **Important** mapper must include pointercolumn which is `(key,value) = ('<pointer column name>', <filename>)`. Default is to call such a column `filename`, i.e. `{'filename':'a.csv'}`

	args:
		path (str): Specify the path to the directory
		mapper ( function ) : filename (str) -> dict. A function which operates on a single file name in order to get the columns (dict key) and values (dict value) for meta_data of that file.
		pointercolumn (str) : The name of the pointercolumn in the created meta_data
		overwrite (bool) : True will overwrite any existing meta_data in path. 


	examples:

		.. code-block:: python

			def mapper(file, path):
				path_to_file = path + file

				meta_data = {'filename':file} # not full path to file, just file in path dir

				return meta_data

			generate_meta_data(path, mapper, pointercolumn = 'filename')
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
