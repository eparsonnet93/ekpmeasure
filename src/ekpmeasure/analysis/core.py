import os 
import pandas as pd
import numpy as np

import warnings

import matplotlib.pyplot as plt
from matplotlib import cm
from functools import wraps
from numpy import AxisError
import pickle
from pprint import pformat


__all__ = ('Dataset', 'Data',)

def construct_Dataset_from_dataframe(function):

	@wraps(function)
	def wrapper(*args, **kwargs):
		dataframe = function(*args, **kwargs)
		
		index_to_path = args[0].index_to_path

		map_new_index_to_old_index = {i:old for i, old in enumerate(dataframe.index)}
		new_index_to_path = pd.Series({i:index_to_path[map_new_index_to_old_index[i]] for i in map_new_index_to_old_index})

		new_path = _convert_ITP_to_path_to_index(new_index_to_path)
		dataframe.reset_index(inplace = True, drop = True)

		return Dataset(path = new_path, initializer = dataframe, readfileby = args[0].readfileby)

	return wrapper

def _convert_ITP_to_path_to_index(index_to_path):
	"""Convert index_to_path (``pandas.Series``) to path_to_index (``dict``) 

	args:
		index_to_path (pandas.Series): index_to_path to convert

	returns:
		(dict): path_to_index, key is path and value is list of indices for that path

	"""
	return {x:y.values for x,y in pd.Series(index_to_path.index, index = index_to_path.values).groupby(level=0)}

def _check_file_exists(path, filename):
	if filename in set(os.listdir(path)):
		return True
	else:
		return False


def _remove_nans_from_set(set_to_remove_from):
	"""Remove multiple nans from a set."""

	out = set()
	for item in set_to_remove_from:
		try:
			if np.isnan(item) and np.nan not in out:
				out.update({np.nan})
				continue
			if np.isnan(item):
				continue
			out.update({item})
		except TypeError:
			out.update({item})
		
	return out

class Dataset():
	"""Dataset class for analysis. Used to manipulate meta data while keeping track of location for the real data, which can be retrieved when necessary.

	Args:
		path (str or dict): Path to the real data. 
		initializer (pandas.DataFrame or dict):  Initializer for a DataFrame. The meta data.
		readfileby (function): How to read the data. Default is ``pandas.read_csv``
		pointercolumn (str or index): Column name which holds name of file. Default is ``'filename'``

	Examples:

		.. code-block:: python

			>>> meta_data = pd.DataFrame(
				{
					'voltageApplied':['1v','2v'],
					'filename':['t1.csv','t2.csv']
				}
			)

			#Assuming the data is stored in './data/', create the Dataset
			>>> dset = Dataset('./data/', meta_data,)

			#Query the meta data for when voltageApplied is '1v':
			>>> dset.query('voltageApplied == "1v"')

			#return the Data
			>>> dset.get_data()


	"""

	def __init__(self, path, initializer, readfileby=pd.read_csv, pointercolumn = 'filename'):
		self.meta_data = pd.DataFrame(initializer)
		self.attrs = dict()
		self.attrs['path'] = path
		self.attrs['index_to_path'] = self._construct_index_to_path(path, initializer)
		self.pointercolumn = pointercolumn
		self.readfileby = readfileby

	def __str__(self):
		return self.meta_data.__str__()

	def __repr__(self):
		return self.meta_data.__repr__()
	
	def __len__(self):
		return self.meta_data.__len__()
	
	def _repr_html_(self):
		return self.meta_data._repr_html_()
	
	@property
	def columns(self):
		return self.meta_data.columns
	
	@property  
	def _is_empty(self):
		if len(self) == 0 and len(self.columns) == 0:
			return True
		else:
			return False

	@property
	def path(self):
		"""Return path to data."""
		return self.attrs['path']

	@property
	def index_to_path(self):
		"""Index to path ``pandas.Series``

		returns:
			(pandas.Series): Index to path


		"""
		return self.attrs['index_to_path']

	@property
	def summary(self):
		"""Return a brief summary of the data in your Dataset. 

		Returns:
			(Dict): a summary of the Dataset. keys are columns names, values are sets of values appearing in the Dataset.

		Examples:

			.. code-block:: python

				>>> dset.head()
				identifier  pulsewidth_ns  delay_ns  high_voltage_v  preset_voltage_v  \
				0      185um          100.0     200.0            0.25               0.5   
				1      185um          100.0     200.0            0.25               0.5   
				2      185um          100.0     200.0            0.25               0.5   
				3      185um          100.0     200.0            0.25               0.5   
				4      185um          100.0     200.0            0.25               0.5   

				   preset_pulsewidth_ns                                      filename  trial  
				0               10000.0  185um100e-9_200e-9_0x25V_500mv_10000ns_0.csv      0  
				1               10000.0  185um100e-9_200e-9_0x25V_500mv_10000ns_1.csv      1  
				2               10000.0  185um100e-9_200e-9_0x25V_500mv_10000ns_2.csv      2  
				3               10000.0  185um100e-9_200e-9_0x25V_500mv_10000ns_3.csv      3  
				4               10000.0  185um100e-9_200e-9_0x25V_500mv_10000ns_4.csv      4  

				>>> dset.summary
				{
					'identifier': {'185um'},
					'pulsewidth_ns': {10.0, 50.0, 100.0},
					'delay_ns': {10.0, 20.0, 50.0, 200.0, 300.0, 500.0},
					'high_voltage_v': {0.125, 0.25, 0.375, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5},
					'preset_voltage_v': {0.5},
					'preset_pulsewidth_ns': {10000.0},
					'trial': {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
				}


		"""
		summary = dict()
		for column in self.columns:
			if column == self.pointercolumn:
				continue
			summary.update({column: _remove_nans_from_set(set(self.meta_data[column].values))})

		return summary
	
	@construct_Dataset_from_dataframe
	def query(self, *args, **kwargs):
		"""Query the columns of a Dataset with a boolean expression.

		Parameters:
			expr (str): The query string to evaluate. You can refer to variables in the environment by prefixing them with an ‘@’ character like @a + b. You can refer to column names that are not valid Python variable names by surrounding them in backticks. Thus, column names containing spaces or punctuations (besides underscores) or starting with digits must be surrounded by backticks. (For example, a column named “Area (cm^2) would be referenced as Area (cm^2)). Column names which are Python keywords (like “list”, “for”, “import”, etc) cannot be used. For example, if one of your columns is called a a and you want to sum it with b, your query should be `a a` + b.

		Returns:
			(Dataset): the result of the query
		"""
		return self.meta_data.query(*args, **kwargs)
	
	@construct_Dataset_from_dataframe
	def head(self, *args, **kwargs):
		return self.meta_data.head(*args, **kwargs)

	@construct_Dataset_from_dataframe
	def filter_on_column(self, column, function, **kwargs_for_function):
		"""Filter Dataset. Keeps rows with column satisfying function.

		args:
			column (str or index): Specify column
			function (function): Filter function. ``function(value) -> bool``
			kwargs_for_function (kwargs): kwargs to pass to function

		returns:
			(Dataset): Filtered Dataset.

		examples:

			.. code-block:: python

				>>> dset.summary
				{
					'identifier': {'185um'},
					'pulsewidth_ns': {10.0, 50.0, 100.0},
					'delay_ns': {10.0, 20.0, 50.0, 200.0, 300.0, 500.0},
					'high_voltage_v': {0.125, 0.25, 0.375, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5},
					'preset_voltage_v': {0.5},
					'preset_pulsewidth_ns': {10000.0},
					'trial': {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
				}

				#Return only rows with where the high_voltage_v is greater than 1 and print the summary
				>>> dset.filter_on_column('high_voltage_v', lambda x: x>1).summary
				{   'identifier': {'185um'},
					'pulsewidth_ns': {50.0},
					'delay_ns': {10.0},
					'high_voltage_v': {1.5, 2.0, 2.5},
					'preset_voltage_v': {0.5},
					'preset_pulsewidth_ns': {10000.0},
					'trial': {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
				}



		"""
		return self.meta_data[self.meta_data[column].apply(function, **kwargs_for_function).values].reset_index(drop = True)

	@construct_Dataset_from_dataframe
	def select_index(self, index):
		"""Return dataset with single index specified.

		args:
			index (int or index): Index to select

		returns:
			(Dataset): Single row Dataset.


		"""
		return pd.DataFrame(self.meta_data.iloc[index]).T.reset_index(drop = True)

	def _write_ekpds_file(self, filename):
		preamble = 'pointercolumn:{}|path:{}'.format(self.pointercolumn, {key:list(self.path[key]) for key in self.path})
		with open(filename, 'wb+') as f:
			f.write(pickle.dumps(preamble))
			f.write(b'########')
			f.write(pickle.dumps(self.readfileby))
			f.write(b'##|##|##|##')
			f.write(pickle.dumps(self.meta_data))

		return
	
	def _construct_index_to_path(self, path, initializer):
		"""Construct index_to_path from path provided

		args:
			path (str or Dict): A path to where the real data lives. if dict, form is {path: [indices of initializer for this path]}  
			initializer (pandas.DataFrame): Meta data. one column must contain a pointer (filename) to where each the real data is stored

		"""
		if len(self) == 0:
			warnings.showwarning("No meta data.", UserWarning, '', 0)
			return {}
		if type(path) != dict:
			assert type(path) == str, "path must be dict or str"
			#set all indices to the single path provided
			index_to_path = pd.Series({i:path for i in range(len(self.meta_data))}, dtype = 'object')
		else:
			for l, key in enumerate(path):
				#path is {path:[indices]}, need inverse
				if l == 0:
					index_to_path = pd.Series(
						{
							i:key for i in path[key]
						}
					)
				else:
					#do not ignore index
					index_to_path = pd.concat(
						(
							index_to_path,
							pd.Series({i:key for i in path[key]})
						)
					)
		#check for duplicate indices:
		if len(index_to_path) != len(set(index_to_path.index)):
			raise ValueError('Duplicate indices provided in path dict!')

		return index_to_path
	
	def remove_index(self, index):
		"""
		Remove an index or array-like of indices.

		args:
			index (index or array-like): index to be removed

		returns:
			(Dataset): updated Dataset

		"""
		index = np.array([index]).flatten()

		#adjust index_to_path and convert to path_to_index
		path = _convert_ITP_to_path_to_index(self.index_to_path.drop(index = index).reset_index(drop = True))
		meta_data = self.meta_data.drop(index = index).reset_index(drop = True)
		return Dataset(path, meta_data, readfileby=self.readfileby)


	def remove_nonexistent_files_from_metadata(self):
		"""
		Remove references to files that do not exist in path. This may occur, for example, if you know certain data files are bad (and thus delete them from the data dir), but did not delete them while collecting data. 
		"""
		# determine available paths in the dataset
		if type(self.path) == str:
			paths = {self.path:self.meta_data.index.values}
		else:
			paths = self.path
			
		remove_index = []
			
		for path in paths:
			indices_to_check = paths[path]
			existing_files = set(os.listdir(path))
			pointercolumn_values_for_path = self.meta_data.iloc[indices_to_check][self.pointercolumn].values
			
			for index, value in zip(indices_to_check, pointercolumn_values_for_path):
				if value not in existing_files:
					remove_index.append(index)

		return self.remove_index(remove_index)


	def _group(self, by, level=None):
		"""Group data by 'by' and return a pandas dataframe. makes use of pandas.groupby

		args:
			by (str, int, label or array-like of): on what to group. 
		"""
		groups = self.meta_data.groupby(by = by, level = level).groups
		for ijk, key in enumerate(groups):
			original_dataset_indices = groups[key]
			new_row = None
			for index in original_dataset_indices:
				original_row = self.meta_data.loc[index] #this is a pandas series of a row from the original dataset
				#columns in this row
				if type(new_row) == type(None):
					#import pdb; pdb.set_trace()
					new_row = {col:dict({index:original_row[col]}) for col in original_row.index}
				else:
					for col in new_row:
						#import pdb; pdb.set_trace()
						new_row[col].update(dict({index:original_row[col]}))

			for col in new_row:
				if col != self.pointercolumn:
					new_row[col] = set(list([new_row[col][x] for x in new_row[col].keys()]))

			if ijk == 0:
				new_df = pd.DataFrame(
					{key:[new_row[key]] for key in new_row}
				)
			else:
				new_df = pd.concat(
					(
						new_df, 
						pd.DataFrame(
							{key:[new_row[key]] for key in new_row}
						)
					),
					ignore_index = True
				)

		return new_df   

	def add_calculated_column(self, column_name, how):
		"""Add a calculated column to the Dataset.

		args:
			column_name (str): The new column name
			how (function): f(self) -> column data. A function which operates on self (pandas.DataFrame) and returns new column data.

		returns:
			(Dataset): Updated Dataset.

		examples:

			Convert 25um and 10um to measured areas. This will only work if no other diameters are present in the Dataset.

			.. code-block:: python

				>>> def how(dataframe):
						nominal_diameter_to_measured_area_dict = {'25um':190, '10um':60}
						return [nominal_diameter_to_measured_area_dict[x] for x in dataframe['diameter'].values]

				>>> dset.add_calculated_column('measured_area_um', how = how)


		"""

		if not hasattr(how, '__call__'):
			raise TypeError('how must be a function that operates on a DataFrame')

		new_column_data = how(pd.DataFrame(self.meta_data))
		self.add_column(column_name, new_column_data)

		return self

	def save_meta_data(self,):
		"""Save the current meta_data as ``pandas.DataFrame`` to path. This is not allowed for merged datasets *i.e.* Dataset resulting from ``analysis.utils.merge_Datasets``. To save a Dataset (including merged) see :func:`to_ekpds <.ekpds>`.

		"""
		if len(set(self.index_to_path)) != 1:
			raise ValueError('Dataset does not contain a unique path to data. Saving of this type of Dataset is not supported.')

		path = list(set(self.index_to_path))[0]
		self.meta_data.to_pickle(path + 'meta_data')

		return

	def to_ekpds(self, path):
		"""Save Dataset to file (extension .ekpds).

		args:
			path (str): Path to save location

		example:

			.. code-block:: python

				dset.to_ekpds('./dset1.ekpds')

		"""
		self._set_index_to_path_absolute()
		self._set_path_absolute()

		#check if file exits:
		dirname = os.path.dirname(path)
		name = path.split('/')[-1]
		if _check_file_exists(dirname, name):
			yn = input('file ({}) already exists. Overwrite? (y/n)'.format(path))
			if yn.lower() == 'y':
				os.remove(path)
				self._write_ekpds_file(path)
			else:
				pass
		else:
			self._write_ekpds_file(path)

		return 




	def _set_index_to_path_absolute(self):
		"""Modify ``.index_to_path`` to absolute paths."""
		itp = self.index_to_path

		for ind, x in zip(itp.index, itp):
			abspath = (os.path.abspath(x)).replace('\\', '/')
			if not abspath[-1] == '/':
				abspath += '/' #put final slash in place

			itp.at[ind] = abspath

		return

	def _set_path_absolute(self):
		"""Modify ``.path`` to absolute paths."""
		if type(self.path) == str:
			abspath = (os.path.abspath(self.path)).replace('\\', '/')
			if not abspath[-1] == '/':
				abspath += '/' #put final slash in place
			out = abspath
		elif type(self.path) == dict:
			pdict = self.path
			new_pdict = {}
			for key in pdict:
				indices = pdict[key]

				abspath = (os.path.abspath(key)).replace('\\', '/')
				if not abspath[-1] == '/':
					abspath += '/' #put final slash in place

				new_pdict.update({abspath:indices})
			del pdict
			out = new_pdict
		else:
			raise TypeError('Only str or dict supported as self.path. Please report this issue.')

		self.attrs['path'] = out

		return



	def add_column(self, column_name, column_data):
		"""Add a column to a Dataset.

		args:
			column_name (str): The new column name.
			column_data (array-like): The data for the column

		"""
		path_to_index = _convert_ITP_to_path_to_index(self.index_to_path)
		self.meta_data[column_name] = column_data
		return Dataset(path_to_index, self.meta_data)      

	def get_data(self, groupby=None, labelby=None,):
		"""
		Return data in Data (Data class) for the current Dataset. If using groupby kwarg, resulting Data will vstack all data which corresponds to that grouping. (See examples)
		
		args:
				groupby (str, label, index or array-like of):  what to group on
				labelby (str, label, index or array-like of):  what to label the output data by. This will change 'definition' in output Data class

		returns:
				(Data): the data

		examples:
			
			.. code-block:: python

				>>> dset.summary
				{
					'identifier': {'185um'},
					'pulsewidth_ns': {10.0, 50.0, 100.0},
					'delay_ns': {10.0, 20.0, 50.0, 200.0, 300.0, 500.0},
					'high_voltage_v': {0.125, 0.25, 0.375, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5},
					'preset_voltage_v': {0.5},
					'preset_pulsewidth_ns': {10000.0},
					'trial': {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
				}

				>>> data = dset.get_data() #no groupby yet
				>>> data.data_keys
				['time', 'p1', 'p2']

				>>> data.iloc[0].p1 # This corresponds to a single trial (1D data)
				array([  0.00898495,  0.00765674,  0.00351585, ..., -0.00679731,
						-0.00101569, -0.00039065])

				# now we will group by high_voltage_v. There are many .csv files that correspond to such a case
				# for example how many are there for a high_voltage_v of .125? (there are 5, see here)
				>>> len(dset.query('high_voltage_v == .125'))
				5

				# let's retrieve the data but with grouping
				>>> data = dset.get_data(groupby = 'high_voltage_v')
				>>> data.iloc[0]['p1'] #vstack of all different .csv files grouped by high_voltage_v (a meta data parameter)
				array([[ 0.00898495,  0.00765674,  0.00351585, ..., -0.00679731,
						-0.00101569, -0.00039065],
					   [-0.02172014, -0.02773615, -0.03695549, ..., -0.0203138 ,
						-0.0085943 , -0.00117195],
					   [-0.0351585 , -0.02859558, -0.02289209, ..., -0.03093948,
						-0.01968876, -0.01289145],
					   [-0.02765802, -0.02453282, -0.02070445, ..., -0.00679731,
						-0.00257829, -0.0093756 ],
					   [-0.0375024 , -0.04656548, -0.04930003, ..., -0.03789305,
						-0.02609542, -0.01632917]])

				# no longer is it 1D data. 
				>>> data[0]['data']['p1'].shape
				(5, 500)

				#recall that there were 5 rows in the Dataset corresponding to a high_voltage_v of .125. Is this that grouping? we can check:
				>>> data[0]['definition']
				# indeed it is!!!
				{   
					'identifier': {'185um'},
					'pulsewidth_ns': {10.0},
					'delay_ns': {20.0},
					'high_voltage_v': {0.125},
					'preset_voltage_v': {0.5},
					'preset_pulsewidth_ns': {10000.0},
					'trial': {0, 1, 2, 3, 4}
				}


		"""
		if len(self) == 0:
			raise ValueError('No meta data to return data for!!')
		pointercolumn = self.pointercolumn
		readfileby = self.readfileby

		if type(groupby) == type(None):
			data_to_retrieve = self._group(by = None, level = 0) # gives us a unique col for each
		else:
			data_to_retrieve = self._group(by = groupby)

		out = {}
		for counter, i in enumerate(data_to_retrieve.index): # for each row
			# NOTE data_to_retrieve.at[i, self.pointercolumn] is a dict
			filename_index_to_path_dict = data_to_retrieve.at[i, self.pointercolumn]
			for k, index_of_original in enumerate(filename_index_to_path_dict):
				try:
					tdf = readfileby(self.index_to_path[index_of_original] + filename_index_to_path_dict[index_of_original])
				except Exception as e:
					raise Exception('error reading data. ensure self.readfileby is correct and that readfileby returns a pandas dataframe. self.readfileby is currently set to {}.\nError was: {}'.format(self.readfileby.__name__, e))

				if i == 0:
					columns_set = set(tdf.columns)

				if set(tdf.columns) != columns_set:
					raise ValueError('not all data in this Dataset has the same columns!')

				if k == 0: #build the internal data out
					internal_out = (
						{
							'definition': {col: data_to_retrieve.at[i, col] for col in self.columns},
							'data': {col: tdf[col].values for col in tdf.columns}
						}
					)

				else:
					try: #catch ValueError if the concatenation fails for having different lengths. Allows us to merge data of different lengths
						for col in columns_set:
							internal_out['data'].update({col: np.vstack((internal_out['data'][col], tdf[col].values))})
					except ValueError as e:
						if 'all the input array dimensions for the concatenation axis must match exactly' in str(e):
							for col in columns_set:
								current_stack = internal_out['data'][col]
								if len(current_stack.shape) != 2: 
									if len(current_stack.shape) == 1:
										current_stack = np.reshape(current_stack, (1, len(current_stack)))
									else:
										raise ValueError('Current vstack is not 2 dimensional, meaning each row contains at least 2D data. Merging non-matching shapes is not allowed at higher dimensionality.')
								current_nrows = current_stack.shape[0]
								current_len = current_stack.shape[1]
								new_len = max((current_len, len(tdf[col].values)))
								for index in range(current_nrows):
									row = current_stack[index, :]
									n_nans_to_add = new_len - len(row)
									row = np.concatenate((row, np.array([np.nan for i in range(n_nans_to_add)])))
									if index == 0:
										new_stack = row
									else:
										new_stack = np.vstack((new_stack, row))

								new_data = tdf[col].values
								to_stack_on_end = np.concatenate((new_data, np.array([np.nan for i in range(new_len - len(new_data))])))
								internal_out['data'].update({col:np.vstack((new_stack,to_stack_on_end))})
						else:
							raise(e)
					

			out.update({counter:internal_out})

		for counter in out:
			definition = out[counter]['definition']
			try:
				definition.pop(self.pointercolumn)
			except:
				pass

		if type(labelby) == type(None):
			return Data(out)


		labelby = set(np.array([labelby]).flatten())

		for counter in out:
			#pop off the labels we don't want
			definition = out[counter]['definition']
			to_pop = set(definition.keys()) - labelby
			for key in to_pop:
				try:
					definition.pop(key)
				except KeyError:
					pass
		return Data(out)

def _check_definition_contains_or(definition_dict, key, values):
		"""need docstring"""
		out = False
		for value in values:
			if (np.array(list(definition_dict[key])) == value).any():
				out = True
				break
		return out

def _summarize_data(data):
	out = {}
	for index in data:
		defn = data[index]['definition']
		for key in defn:
			try:
				out[key].update(_remove_nans_from_set(set({value for value in defn[key]})))
			except KeyError:
				out.update({key:_remove_nans_from_set(set({value for value in defn[key]}))})
	return out
		
class iDataIndexer():
	
	def __init__(self, initializer):
		self.indexed_dict = initializer
		return 
	
	def __getitem__(self, i):

		if i<0:
			index = len(self.indexed_dict) + i
		else:
			index = i
		return Data({index: self.indexed_dict[index]})

class Data():
	"""Data class for maintaining and manipulating the real data. Typically retrieved via ``Dataset.get_data()``


	args:
		dict (Dict): a dict (with form shown below) of the data. 


	Examples:

		.. code-block:: python

			>>> data
			> {0: {
				'definition': {'frequency': {'1067hz'},
							   'amplitude': {'500ua'},
							   'nave': {5},
							   'low_current': {-2.5},
							   'high_current': {2.5},
							   'delay': {1},
							   'time_constant': {'30ms'},
							   'ramp_rate': {0.05},
							   'ramp_up_first': {True},
							   'identifier': {'B1'},
							   'sensitivity': {'50mv/na'},
							   'trial': {0}},
				'data': {'H_mean': array([-403.524  , -407.18   , -395.602  , -382.146  , -367.444  , ... ]),
					   'H_std': array([10.39320663,  4.7261697 ,  5.3691951 ,  5.71281577,  5.9829578 , ... ]),
					   'R_mean': array([0.0324881 , 0.03248582, 0.03248772, 0.03248544, 0.03248354, ... ]),
					   'R_std': array([1.69941166e-06, 1.42182981e-06, 1.42182981e-06, 3.31276320e-06, ...]),
					   'Theta_mean': array([0.0324881 , 0.03248582, 0.03248772, 0.03248544, 0.03248354, ...]),
					   'Theta_std': array([0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , ...])}
				}
			}

		.. code-block:: python

			# one can access data and/or definition as an attribute
			
			>>> data.definition
			>{'frequency': {'1067hz'},
			   'amplitude': {'500ua'},
			   'nave': {5},
			   'low_current': {-2.5},
			   'high_current': {2.5},
			   'delay': {1},
			   'time_constant': {'30ms'},
			   'ramp_rate': {0.05},
			   'ramp_up_first': {True},
			   'identifier': {'B1'},
			   'sensitivity': {'50mv/na'},
			   'trial': {0}
			}
			>>> data.data
			> {'H_mean': array([-403.524  , -407.18   , -395.602  , -382.146  , -367.444  , ... ]),
			   'H_std': array([10.39320663,  4.7261697 ,  5.3691951 ,  5.71281577,  5.9829578 , ... ]),
			   'R_mean': array([0.0324881 , 0.03248582, 0.03248772, 0.03248544, 0.03248354, ... ]),
			   'R_std': array([1.69941166e-06, 1.42182981e-06, 1.42182981e-06, 3.31276320e-06, ...]),
			   'Theta_mean': array([0.0324881 , 0.03248582, 0.03248772, 0.03248544, 0.03248354, ...]),
			   'Theta_std': array([0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , ...])}

			# one can also access individual attributes of definition or data:
			>>> data.H_mean
			> array([-403.524  , -407.18   , -395.602  , -382.146  , -367.444  , ... ])


	"""

	def __init__(self, initializer):
		self._dict = dict(initializer)
		
	def __getitem__(self, key):
		try:
			return self._dict.__getitem__(key)
		except KeyError:
			return self.__getattr__(key)

	def __iter__(self):
		return self._dict.__iter__()
	
	def __next__(self):
		return self._dict.__next__()
		
	def __str__(self):
		return self._dict.__str__()
	
	def __repr__(self):
		return pformat(self._dict, indent=1,)
		
	def __len__(self):
		return self._dict.__len__()

	def __getattr__(self, key):
		if key == 'definition' or key == 'data':            
			return self._get_defn_or_data(key)
		try:
			return self._get_defn_attr(key)
		except KeyError:
			return self._get_data_attr(key)

	def _get_defn_attr(self, key):
		if len(self) == 1:
			return self._dict[list(self._dict.keys())[0]]['definition'][key]

		return {i:self._dict[i]['definition'][key] for i in self._dict}

	def _get_data_attr(self, key):
		if len(self) == 1:
			return self._dict[list(self._dict.keys())[0]]['data'][key]

		return {i:self._dict[i]['data'][key] for i in self._dict}

	def _get_defn_or_data(self, key):
		if len(self) == 1:
			return self._dict[list(self._dict.keys())[0]][key]

		return {i:self._dict[i][key] for i in self._dict}

	@property
	def iloc(self):
		"""
		An indexer as in pandas .iloc Usage is Data.iloc[index]

		returns:
			(iDataIndexer): indexer for indexing

		example:

			.. code-block:: python

				>>> Data.iloc[0]

		"""
		return iDataIndexer(self._dict.copy())

	@property 
	def summary(self):
		"""Return a summary of the definitions in data

		returns:
			(dict): summary of the data included

		"""
		return _summarize_data(self._dict.copy())

	@property
	def data_keys(self):
		"""
		Return a list of keys corresponding to data. 

		returns:
			(list): data keys
		"""
		return list(self._dict[list(self._dict.keys())[0]]['data'].keys())

	def to_ekpdat(self, file):
		"""Save file as `.ekpdat` file.

		args:
			file (str): Path to file
		"""
		with open(file, 'wb') as f:
			pickle.dump(self._dict, f)

	def _get_indices_satisfying_definition_condtion(self, condition):
		"""need docstring"""
		for key in condition:
			if not hasattr(condition[key], '__iter__'):
				raise AttributeError('iterable not provided as value in condition arg. value associated with key "{}" is type {}'.format(key, type(condition[key])))

			if type(condition[key]) == str:
				raise TypeError('condition value must not be str. check key: {}.'.format(key) + ' try {' +  '"{}": ["{}"]'.format(key, condition[key]) + '}?')

		indices = [] #to hold which data satisfies condition

		for condition_key in condition:
			for index in self._dict:
				defn = self._dict[index]['definition']
				if _check_definition_contains_or(defn, condition_key, condition[condition_key]):
					indices.append(index)
		return indices

	def filter(self, data_condition_function_dict, definition_condition_dict=None, additional_data_keys_to_filter=None):
		"""Filter the data.

		args:
			data_condition_function_dict (dict): a dict with one entry. key is data key, value is function which operates on a single value.
			definition_condition_dict (dict): a dict specifying specific definition conditions, which when satisfied can allow their data to be operated on. If None, all data will be filtered.
			additional_data_keys_to_filter (str or key or array-like): Additional data keys that you wish to filter based on data_condition_function_dict.

		returns:
			(Data): filtered Data

		Examples:

			Filter the data such that the data key 'R' only contains values >10. This leaves all other data keys unchanged.

			.. code-block:: python

				>>> Data.filter({'R': lambda x: x>10}) 



			Filter data corresponding to an amplitude of '500ua' such that data key 'R' contains only values >10.

			.. code-block:: python

				>>> Data.filter({'R': lambda x: x>10}, {'amplitude':'500ua'}) 

			Filter data based on 'saturation' but also filter the 'switching_time' data.

			.. code-block:: python

				>>> Data.filter({'saturation': lambda x: x > .003}, additional_data_keys_to_filter='switching_time')


			You may use this method to remove outliers, for example.

		"""
		if definition_condition_dict == None:
			definition_condition_dict = {}

		if type(additional_data_keys_to_filter) == type(None):
			additional_data_keys_to_filter = []
		else:
			additional_data_keys_to_filter = np.array([additional_data_keys_to_filter]).flatten()

		assert len(data_condition_function_dict) <= 1, "more than one condition supplied in data_condition_function_dict. only one is supported at a time."
		data_function_key = list(data_condition_function_dict)[0]
		assert hasattr(data_condition_function_dict[data_function_key], '__call__'), "value associated with key '{}' in data_condition_function_dict is a not a function. is type {}".format(data_condition_function_dict, type(data_condition_function_dict[data_function_key]))
		assert data_function_key in set(self._dict[0]['data'].keys()), "data_function_key '{}' not in data. available keys are {}".format(data_function_key, set(self[0]['data'].keys()))

		sat_indices = self._get_indices_satisfying_definition_condtion(definition_condition_dict)
		if definition_condition_dict == {}:
			sat_indices = set(self._dict.keys())
		all_index = set(self._dict.keys())
		not_sat_indices = all_index - set(sat_indices)

		func = data_condition_function_dict[data_function_key]

		keys_to_update = [key for key in additional_data_keys_to_filter]

		keys_to_update.append(data_function_key)
		keys_to_update = keys_to_update[::-1]


		for index in sat_indices:
			checker = self._dict[index]['data'][data_function_key]
			for key in keys_to_update:
				old = self._dict[index]['data'][key]
				old_shape = old.shape
				#ensure that all keys in keys_to_update have the same dimensionality
				if old_shape != checker.shape:
					raise ValueError('data corresponding to data_key "{}" does not have the same shape as data corresponding to data_function_key "{}"'.format(key, data_function_key))
				self._dict[index]['data'].update({key:old[func(checker)]})

		return Data(self._dict)

	def contains(self, condition):
		"""Returns data specified by condition.

		args:
			condition (dict): key is definition key, value is value to find. Multiple values provided will be joined by logical OR. Multiple keys will be joined with logical AND.

		returns:
			(Data): data satisfying condition 

		examples:

			.. code-block:: python

				#Providing multiple values will be joined by logical or, i.e.
				Data.contains({'high_voltage_v':{'100mv', '200mv'}})
				#will search for all data with '100mv' OR '200mv' for high_voltage_v. 

				#Multiple keys provided will be joined with logical AND. i.e. 
				Data.contains({'x':1, 'y':2})
				#will search for x = 1 AND y = 2.



		"""
		indices = self._get_indices_satisfying_definition_condtion(condition)

		#we will append the index to indices everytime the logical or statement for the specific condition holds
		#to check the logical and statement over various keys, we need to ensure that for each key we did indeed append the index to indices:
		indices = np.array(indices)
		indices_set = set(indices)
		indices_out = []
		for index in indices_set:
			if len(indices[indices == index]) == len(condition.keys()):
				indices_out.append(index)
			else:
				pass


		#build the final Data:
		out = {}
		for new, old in enumerate(indices_out):
			out.update({new: self._dict[old]})

		return Data(out)


	def mean(self, inplace = False):
		"""
		Return data class where data is averaged across 0th axis. This is best used for averaging across trials or similar.

		args:
			inplace (bool): do operation inplace

		returns:
			(Data): averaged data across 0th axis.
		"""

		if not inplace:
			tmp_out = {}
			for key in self._dict:
				tmp_out.update({key:self._dict[key].copy()})
				data = self._dict[key]['data']
				mean_data = {}
				for k in data:
					if len(data[k].shape) == 1: #1d data
						mean_data.update({k:data[k]})
					else:
						try:
							mean_data.update({k:np.mean(data[k], axis = 0)})
						except AxisError:
							mean_data.update({k:data[k]})
				tmp_out[key].update({'data':mean_data})
			return Data(tmp_out)

	def collapse(self, data_key):
		"""
		Return collapsed (numpy.array) data corresponding to data_key. This will return all data for all indices concatenated into a single array.

		args:
			data_key (key): Key for data you wish to collapse

		returns:
			(numpy.array): Concatenated array of all data corresponding to data_key for all indices in self. 

		"""
		for ijk, i in enumerate(self._dict):
			current = self._dict[i]['data'][data_key].flatten()
			if ijk == 0:
				out = current
				continue
			out = np.concatenate((out, current))

		return out

	def apply(self, function_on_data, pass_defn=False, ignore_errors=True,**kwargs):
		"""Apply data_function to the data in each index. ``**kwargs`` will be passed to data_function. If function_on_data returns 'None', that piece of data will be dropped. 

		args:
			function_on_data (function): f(dict) -> dict. Function is passed the data_dict for each index.
			pass_defn (bool): Whether or not to pass the definition to function_on_data. If True, will be passed with other kwargs. 
			ignore_errors (bool): If True, errors in function_on_data will be printed, but not raised. Resulting data will be original data. If False, errors will be raised.

		returns:
				(Data): the new data after operating on it

		examples:

			.. code-block:: python

				>>> some_data
				>
				{
					0: {'definition': {'param1': {'10V'},
						'param2': {'100ns', '10ns', '50ns'},
						'param3': {'1mv', '2mv'}},
						'data': {'raw_data': array([[1, 2, 3],
							  [1, 2, 3],
							  [1, 2, 3],
							  [1, 2, 3]], dtype=int64)}},
					1: {'definition': {'param1': {'5V'}, 'param2': {'100ns'}, 'param3': {'1mv'}},
						'data': {'raw_data': array([1, 2, 3], dtype=int64)}}
				}

				#some function will square the data

				def some_function(data_dict):
					"a function which operates on the data dict and returns a data dict"
					out = dict()
					for key in data_dict:
						out.update({key:data_dict[key]**2})
					return out

				>>> some_data.apply(some_function)
				>
				{
					0: {'definition': {'param1': {'10V'},
						'param2': {'100ns', '10ns', '50ns'},
						'param3': {'1mv', '2mv'}},
						'data': {'raw_data': array([[1, 4, 9],
						  [1, 4, 9],
						  [1, 4, 9],
						  [1, 4, 9]], dtype=int64)}},
					1: {'definition': {'param1': {'5V'}, 'param2': {'100ns'}, 'param3': {'1mv'}},
						'data': {'raw_data': array([1, 4, 9], dtype=int64)}}}

		"""

		data_function = function_on_data
		tmp_out = {}
		new_key = 0

		for key in self._dict.keys():
			try:

				if pass_defn:
					#ensure no overlap between passed arguments and definition arguments:
					overlap = set(kwargs.keys()).intersection(set(self._dict[key]['definition'].keys()))
					if len(overlap) != 0:
						raise ValueError('kwargs passed in both definition and as kwargs in .apply(). Overlapping keys are "{}"'.format(overlap))

					to_pass = self._dict[key]['definition'].copy()
					for key in kwargs:
						to_pass.update({key:kwargs})
					internal_out = {
						'definition':self._dict[key]['definition'],
						'data':data_function(self._dict[key]['data'].copy(), defn = self._dict[key]['definition'], **to_pass)
					}
				else:
					internal_out = {
						'definition':self._dict[key]['definition'],
						'data':data_function(self._dict[key]['data'].copy(), **kwargs)
					}
				if internal_out['data'] == 'None':
					continue

				tmp_out.update({new_key:internal_out})
				new_key += 1
			except Exception as e:
				if ignore_errors:
					print('Error in data_function: {} \n{}'.format(data_function.__name__, e))
					print('Skipping data key: {} with defintion: \n{}'.format(key, self._dict[key]['definition']))
				else:
					raise e

		return Data(tmp_out)

	def to_dict(self):
		"""
		Return a dict of the Data class.  


		returns:
			(dict): a dict class with identical structure"""
		return self._dict

	def plot(self, x=None, y=None, ax=None, color = None, cmap = 'viridis', labelby = None, **kwargs):
		"""
		Plot the data. If ax is provided returns ax, otherwise returns fig, ax.

		args:
			x (key): data dict key for x axis.
			y (key or array-like): data dict key for y axis
			ax (matplotlib.axis): axis to plot on 
			color (str): Color of plot. (Override colormap)
			cmap (str): Color map. See matplotlib.cm.cmaps_listed for allowed colormaps.
			labelby (str): Definition key to use for plot legend.

		returns:
			fig (matplotlib.figure): figure of plot
			ax (matplotlib.axis): axis of plot. if ax is provided as an argument, only returns ax.
		"""
		if ax == None:
			fig, ax = plt.subplots()
			return_fig = True
		else:
			return_fig = False

		if cmap not in set(cm.cmaps_listed.keys()):
			raise KeyError('cmap "{}" not supported. Supported colormaps are {}'.format(cmap, cm.cmaps_listed.keys()))  

		if color == None:
			colors = [cm.cmaps_listed[cmap](x) for x in np.linspace(0, 1, len(self._dict.keys()))]
		else: 
			colors = [color for i in range(len(self._dict.keys()))]

		for color, index in zip(colors, self._dict.keys()):
			if x == None:
				data_keys_to_plot = list(self._dict[index]['data'].keys())
			else:
				xs = self._dict[index]['data'][x]
				data_keys_to_plot = set(self._dict[index]['data'].keys()) - set({x})

			if labelby == None:
				label = None
			else:
				label = self._dict[index]['definition'][labelby]

			if type(y) == type(None):
				pass
			else:
				data_keys_to_plot = set(np.array([y]).flatten())


			for plotkey in data_keys_to_plot:
				to_plot = self._dict[index]['data'][plotkey]

				if len(to_plot.shape) == 1: #1d data
					if x == None:
						ax.plot(to_plot, color = color, label = label, **kwargs)
					else:
						ax.plot(xs, to_plot, color = color, label = label, **kwargs)
					continue

				for i in range(to_plot.shape[0]):
					if i == 0: #label only the first becuase we don't want a big legend with many trials
						if x == None:
							ax.plot(to_plot[i,:], color = color, label = label, **kwargs)
						else:
							ax.plot(xs[i,:], to_plot[i,:], color = color, label = label, **kwargs)
					else:
						if x == None:
							ax.plot(to_plot[i,:], color = color, **kwargs)
						else:
							ax.plot(xs[i,:], to_plot[i,:], color = color, **kwargs)

		if labelby != None:
			ax.legend()

		if return_fig:
			return fig, ax
		else:
			return ax

	def scatter(self, x=None, y=None, ax=None, color = None, cmap = 'viridis', labelby = None, **kwargs):
		"""
		Scatter plot the data. If ax is provided returns ax, otherwise returns fig, ax.

		args:
			x (key): data dict key for x axis.
			y (key or array-like): data dict key for y axis
			ax (matplotlib.axis): axis to plot on 
			color (str): Color of plot. (Override colormap)
			cmap (str): Color map. See matplotlib.cm.cmaps_listed for allowed colormaps.
			labelby (str): Definition key to use for plot legend.

		returns:
			fig (matplotlib.figure): figure of plot
			ax (matplotlib.axis): axis of plot. if ax is provided as an argument, only returns ax.
		"""
		if ax == None:
			fig, ax = plt.subplots()
			return_fig = True
		else:
			return_fig = False

		if cmap not in set(cm.cmaps_listed.keys()):
			raise KeyError('cmap "{}" not supported. Supported colormaps are {}'.format(cmap, cm.cmaps_listed.keys()))  

		if color == None:
			colors = [cm.cmaps_listed[cmap](x) for x in np.linspace(0, 1, len(self._dict.keys()))]
		else: 
			colors = [color for i in range(len(self._dict.keys()))]

		for color, index in zip(colors, self._dict.keys()):
			if x == None:
				data_keys_to_plot = list(self._dict[index]['data'].keys())
			else:
				xs = self._dict[index]['data'][x]
				data_keys_to_plot = set(self._dict[index]['data'].keys()) - set({x})

			if labelby == None:
				label = None
			else:
				label = self._dict[index]['definition'][labelby]

			if type(y) == type(None):
				pass
			else:
				data_keys_to_plot = set(np.array([y]).flatten())


			for plotkey in data_keys_to_plot:
				to_plot = self._dict[index]['data'][plotkey]

				if len(to_plot.shape) == 1: #1d data
					if x == None:
						ax.scatter(to_plot, color = color, label = label, **kwargs)
					else:
						ax.scatter(xs, to_plot, color = color, label = label, **kwargs)
					continue

				for i in range(to_plot.shape[0]):
					if i == 0: #label only the first becuase we don't want a big legend with many trials
						if x == None:
							ax.scatter(to_plot[i,:], color = color, label = label, **kwargs)
						else:
							ax.scatter(xs[i,:], to_plot[i,:], color = color, label = label, **kwargs)
					else:
						if x == None:
							ax.scatter(to_plot[i,:], color = color, **kwargs)
						else:
							ax.scatter(xs[i,:], to_plot[i,:], color = color, **kwargs)

		if labelby != None:
			ax.legend()

		if return_fig:
			return fig, ax
		else:
			return ax

	def sort(self, by, key=None, reverse=False):
		"""
		Sort `Data` by definition key. This might be useful, for example in plotting with color maps. This Method sorts Data over mulitple indices, does not sort Data within an index. 

		args:
			by (str or key): Definition key. The definition key that you are sorting on must be unique for each index in your `Data` object. 
			key (function): Method for accessing value to sort.
			reverse (bool): Reverse order

		returns:
			(Data): Sorted Data

		examples:

			Sort Data on parameter 'test'

			.. code-block:: python

				>>> data = dset.get_data()
				>>> data.summary
				> 
				{'param': {'v'},
				 'test': {0, 1, 2, 3, 4},
				 'test2': {'100mv', '15mv', '1mv', '20mv', '32mv'}}

				# Sort by definition key 'test'
				>>> data = data.sort(by='test')

				# Confirm sorted:
				>>> data.test
				> {0: {0}, 1: {1}, 2: {2}, 3: {3}, 4: {4}}

				### Sort in reverse order:

				>>> data = dset.get_data()
				>>> data.sort(by = 'test', reverse = True).test
				> {0: {4}, 1: {3}, 2: {2}, 3: {1}, 4: {0}}

			
			Sort Data on a key that is not int or float:

			.. code-block:: python

				>>> data = dset.get_data()
				>>> data.summary
				> 
				{'param': {'v'},
				 'test': {0, 1, 2, 3, 4},
				 'test2': {'100mv', '15mv', '1mv', '20mv', '32mv'}}
				
				# unsorted data
				>>> data.test2
				> {0: {'1mv'}, 1: {'100mv'}, 2: {'20mv'}, 3: {'15mv'}, 4: {'32mv'}}

				# Sort by definition key 'test2'
				>>> sort_by = lambda x: float(x.replace('mv', '')) # get rid of 'mv' suffix and convert to float
				>>> data = data.sort(by='test2', key=sort_by)
				>>> data.test2
				> {0: {'1mv'}, 1: {'15mv'}, 2: {'20mv'}, 3: {'32mv'}, 4: {'100mv'}}

		"""
		sorter = _data_sorter(self._dict, by).sort(key=key, reverse=reverse)
		sorted_out = {}
		for i in sorter.mapper:
			sorted_out.update({i:self._dict[sorter.mapper[i]]})
			
		return Data(sorted_out)
	
class _data_sorter():
	"""Class for sorting data. Upon running `self.sort` self contains two attributes, `.values` and `.value_index_mapper`. `values` contains the sorted values corresponding to arg `_definition_key` and `value_index_mappper` is a dict mapping each (sorted) value to a `Data` index. 
		
		args:
			_dict (dict): Dict representation of Data object. 
			_definition_key (str or key): Definition key to sort on.

		examples:

			One can explicitly use the _data_sorter class

			.. code-block:: python 

				>>> data = dset.get_data()
				>>> data.summary
				> {'test':{0,1,2,3,4}}

				# Create a sorter for definition key 'test' 
				>>> sorter = _data_sorter(data._dict, 'test')
				>>> sorter.sort()
				>>> sorted_out = {}
				>>> for i in sorter.mapper:
						sorted_out.update({i:data._dict[sorter.mapper[i]]})
				>>> Data(sorted_out)
				> 
				{0: {'data': {'R': array([1, 2, 3], dtype=int64)},
					 'test': {0}}},
				 1: {'data': {'R': array([1, 2, 3], dtype=int64)},
					 'test': {1}}},
				 2: {'data': {'R': array([1, 2, 3], dtype=int64)},
					 'test': {2}}},
				 3: {'data': {'R': array([1, 2, 3], dtype=int64)},
					 'test': {3}}},
				 4: {'data': {'R': array([1, 2, 3], dtype=int64)},
					 'test': {4}}}}

			The same exact functionality can be accessed with `Data.sort()`

			.. code-block:: python

				>>> data = dset.get_data()
				>>> test.summary
				> {'data':{0,1,2,3,4}}

				# Sort by definition key 'test'
				>>> data.sort(by='test')
				> 
				{0: {'data': {'R': array([1, 2, 3], dtype=int64)},
					 'test': {0}}},
				 1: {'data': {'R': array([1, 2, 3], dtype=int64)},
					 'test': {1}}},
				 2: {'data': {'R': array([1, 2, 3], dtype=int64)},
					 'test': {2}}},
				 3: {'data': {'R': array([1, 2, 3], dtype=int64)},
					 'test': {3}}},
				 4: {'data': {'R': array([1, 2, 3], dtype=int64)},
					 'test': {4}}}}


		"""
	
	def __init__(self, _dict, _definition_key):
		self._dict = _dict
		self._definition_key = _definition_key
		self._keys = list(_dict.keys())
		
	def sort(self, key=None, reverse=False):
		"""
		Populate attributes `.values` and `value_index_mapper`. 

		args:
			key (function): Method for accessing value to sort. 
			reverse (bool): Reverse order

		returns:
			(_data_sorter) 
		"""
		values = []
		if type(key) == type(None):
			key = lambda x: x

		for i in self._keys:
			definition_value = self._dict[i]['definition'][self._definition_key]
			assert len(definition_value) == 1, "Definition for index '{}' is not unique. It contains multiple values: {}. Cannot sort.".format(i, definition_value)
			value = list(definition_value)[0]
			values.append(value)	

		float_values = [key(value) for value in values]
		argsort = np.argsort(float_values)
		if reverse:
			argsort = argsort[::-1]
		self.mapper = {i:old_index for i, old_index in enumerate(argsort)}
			
		return self
