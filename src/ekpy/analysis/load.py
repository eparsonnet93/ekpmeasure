import os 
import pandas as pd
import numpy as np

import warnings
import pickle
import ast

from .core import Dataset, Data
from ..utils import read_ekpy_data

__all__ = ('load_Dataset', 'generate_meta_data', 'read_ekpds', 'read_ekpdat')

def load_Dataset(path, meta_data=None, readfileby=read_ekpy_data):
	"""
	Load a dataset from path. Path must contain (pickle or .csv) file ``'meta_data'``. 

	args:
		path (str): Path to data
		meta_data (pandas.DataFrame): meta_data if one wishes to provide different meta_data from that provided in path. 
		readfileby (callable): Method for reading data. 

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

	return Dataset(path, _build_df(path, meta_data), readfileby=readfileby)


def read_ekpdat(filename):
	"""Read Data from `.ekpdat` file.

	args:
		filename (str): Path to file

	returns:
		(Data): Data
	"""
	with open(filename, 'rb') as f:
		_dict = pickle.load(f)

	return Data(_dict)

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

	if type(meta_data) == type(None):
		try:
			return pd.read_csv(path + 'meta_data.csv')
		except FileNotFoundError:
			try:
				return pd.read_pickle(path + 'meta_data')
			except FileNotFoundError:
				raise FileNotFoundError('No file named "meta_data.csv" (or legacy pickle file "meta_data") exists in path "{}", you may want to create one or both of these with `.generate_meta_data()`'.format(path))
	else:
		return meta_data

def generate_meta_data(path, mapper, pass_path=False, pointercolumn='filename', overwrite=False, ignore_errors=True):
	"""
	Generate meta_data from a path for a given mapper function. **Important** mapper must include pointercolumn which is `(key,value) = ('<pointer column name>', <filename>)`. Default is to call such a column `filename`, i.e. `{'filename':'a.csv'}`

	args:
		path (str): Specify the path to the directory
		mapper ( function ) : filename (str) -> dict. A function which operates on a single file name in order to get the columns (dict key) and values (dict value) for meta_data of that file.
		pass_path (bool) : Pass the pass of each file to `mapper`. This is used to parse meta data from **within** the file, as one can now open the file within mapper. If True, `mapper` must take argument `path`.
		pointercolumn (str) : The name of the pointercolumn in the created meta_data
		overwrite (bool) : True will overwrite any existing meta_data in path. 
		ignore_errors (bool) : False will hault generation of meta data if a single file fails. Default is True (ignore)


	examples:

		Basic usage where mapper operates only on filename:

		.. code-block:: python

			def mapper(file,):
				spl = file.split('_')

				meta_data = {
						'param1':spl[0] # the first parameter of interest is located at the first split location.
						'filename':file # must include the filename (or other `pointercolumn`)
					} 

				return meta_data

			generate_meta_data(path, mapper, pointercolumn='filename')


		Parse the data file itself for metadata:

		.. code-block:: python

			def mapper(file, path): # must contain kwarg path!
				full_path = path+file

				with open(full_path, 'r') as f:
					lines = f.readlines()

				### extract metadata from lines ###
				param1 = lines[0].replace('\n','')

				meta_data = {
					'param1':param1,
					'filename':'file'
				}
				return meta_data

			generate_meta_data(path, mapper, pass_path=True)

	"""
	if 'meta_data.csv' in set(os.listdir(path)):
		if not overwrite:
			yn = input('this path ({}) already has meta_data.csv, do you wish to recreate it? (y/n)'.format(path))
			if yn.lower() != 'y':
				print('skipping. NOT overwriting.')
				return
			else:
				print('overwriting.')

	for file in os.listdir(path):
		try:
			if pass_path:
				# used to open the file to read meta data
				meta_data = pd.DataFrame(mapper(file, path=path), index=[0])
			else:
				# does not open file
				meta_data = pd.DataFrame(mapper(file), index=[0])
		except Exception as e:
			if ignore_errors:
				# don't error if unable to process one file.
				print('unable to process file: {} \nError: {}'.format(file, e))
				continue
			else:
				raise e
		try:
			existing_meta_data = pd.concat([existing_meta_data, meta_data], ignore_index=True)
		except NameError:
			existing_meta_data = meta_data.copy()

	if pointercolumn not in set(existing_meta_data.columns): 
		warnings.showwarning('there is no map to key "{}" in mapping function "{}" provided\nEnsure self.pointercolumn property has been set appropriately or else you will be unable to retrieve data'.format(pointercolumn, mapper.__name__), SyntaxWarning, '', 0,)

	# new 
	existing_meta_data.to_csv(path+'meta_data.csv', index=False)
	print('meta_data.csv saved to "{}"'.format(path))
	return
