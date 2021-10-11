import os 
import pandas as pd
import numpy as np

import warnings

import matplotlib.pyplot as plt
from matplotlib import cm
from functools import wraps
from numpy import AxisError
import pickle


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
	path_to_index = dict()
	for i in index_to_path.index:
		index, path = i, index_to_path[i]
		if path in set(path_to_index.keys()):
			path_to_index[path].append(index)
		else:
			path_to_index.update({path:[index]})
	return path_to_index

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
		preamble = 'pointercolumn:{}|'.format(self.pointercolumn)
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
		remove_index = []
		for ind, path in enumerate(self.index_to_path):
			if _check_file_exists(path, self.meta_data[self.pointercolumn].iloc[ind]):
				continue
			else:
				remove_index.append(ind)

		return self.remove_index(remove_index)


	def _group(self, by):
		"""Group data by 'by' and return a pandas dataframe. makes use of pandas.groupby

		args:
			by (str, int, label or array-like of): on what to group. 
		"""
		groups = self.meta_data.groupby(by = by).groups
		for ijk, key in enumerate(groups):
			original_dataset_indices = groups[key]
			new_row = None
			for index in original_dataset_indices:
				original_row = self.loc[index] #this is a pandas series of a row from the original dataset
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

				>>> data[0]['data']['p1'] # This corresponds to a single trial (1D data)
				array([  0.00898495,  0.00765674,  0.00351585, ..., -0.00679731,
						-0.00101569, -0.00039065])

				# now we will group by high_voltage_v. There are many .csv files that correspond to such a case
				# for example how many are there for a high_voltage_v of .125? (there are 5, see here)
				>>> len(dset.query('high_voltage_v == .125'))
				5

				# let's retrieve the data but with grouping
				>>> data = dset.get_data(groupby = 'high_voltage_v')
				>>> data[0]['data']['p1'] #vstack of all different .csv files grouped by high_voltage_v (a meta data parameter)
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
			data_to_retrieve = self._group(by = pointercolumn) #gives us a unique col for each
		else:
			data_to_retrieve = self._group(by = groupby)

		out = {}
		for counter, i in enumerate(data_to_retrieve.index): #for each row
			#data_to_retrieve.at[i, self.pointercolumn] is a dict
			filename_index_to_path_dict = data_to_retrieve.at[i, self.pointercolumn]
			for k, index_of_original in enumerate(filename_index_to_path_dict): #datafile in the set of datafiles in that row
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

class Data(dict):
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


	"""

	def __init__(self, initializer):
		super().__init__(initializer)

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
		return iDataIndexer(self.to_dict().copy())

	@property 
	def summary(self):
		"""Return a summary of the definitions in data
		
		returns:
			(dict): summary of the data included

		"""
		return _summarize_data(self.to_dict().copy())

	@property
	def data_keys(self):
		"""
		Return a list of keys corresponding to data. 

		returns:
			(list): data keys
		"""
		return list(self[list(self.keys())[0]]['data'].keys())

	def _get_indices_satisfying_definition_condtion(self, condition):
		"""need docstring"""
		for key in condition:
			if not hasattr(condition[key], '__iter__'):
				raise AttributeError('iterable not provided as value in condition arg. value associated with key "{}" is type {}'.format(key, type(condition[key])))

			if type(condition[key]) == str:
				raise TypeError('condition value must not be str. check key: {}.'.format(key) + ' try {' +  '"{}": ["{}"]'.format(key, condition[key]) + '}?')

		indices = [] #to hold which data satisfies condition

		for condition_key in condition:
			for index in self:
				defn = self[index]['definition']
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
		assert data_function_key in set(self[0]['data'].keys()), "data_function_key '{}' not in data. available keys are {}".format(data_function_key, set(self[0]['data'].keys()))
		
		sat_indices = self._get_indices_satisfying_definition_condtion(definition_condition_dict)
		if definition_condition_dict == {}:
			sat_indices = set(self.keys())
		all_index = set(self.keys())
		not_sat_indices = all_index - set(sat_indices)
		
		func = data_condition_function_dict[data_function_key]

		keys_to_update = [key for key in additional_data_keys_to_filter]

		keys_to_update.append(data_function_key)
		keys_to_update = keys_to_update[::-1]

		
		for index in sat_indices:
			checker = self[index]['data'][data_function_key]
			for key in keys_to_update:
				old = self[index]['data'][key]
				old_shape = old.shape
				#ensure that all keys in keys_to_update have the same dimensionality
				if old_shape != checker.shape:
					raise ValueError('data corresponding to data_key "{}" does not have the same shape as data corresponding to data_function_key "{}"'.format(key, data_function_key))
				self[index]['data'].update({key:old[func(checker)]})
			
		return Data(self.to_dict())

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
			out.update({new: self[old]})

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
			for key in self:
				tmp_out.update({key:self[key].copy()})
				data = self[key]['data']
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

	def apply(self, function_on_data, pass_defn = False, kwargs_for_function=None,**kwargs):
		"""Apply data_function to the data in each index. ``**kwargs`` will be passed to data_function.

		args:
			function_on_data (function): f(dict) -> dict. Function is passed the data_dict (corresponding to self[index]['data']).
			pass_defn (bool): Whether or not to pass the definition to function_on_data. If True, will be passed with other kwargs. 
			kwargs_for_function (dict): Carryover from an older version. This serves as a error catch to help users convert older code. This argument is not supported.

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
		if type(kwargs_for_function) != type(None):
			raise ValueError("kwargs_for_function argument is no longer supported as of version 0.0.7. Pass kwargs for the apply function simply as kwargs in .apply()")

		#TODO delete kwargs_for_function argument

			


		data_function = function_on_data
		tmp_out = self.to_dict().copy()

		for key in tmp_out.keys():
			try:

				if pass_defn:
					#ensure no overlap between passed arguments and definition arguments:
					overlap = set(kwargs.keys()).intersection(set(tmp_out[key]['definition'].keys()))
					if len(overlap) != 0:
						raise ValueError('kwargs passed in both definition and as kwargs in .apply(). Overlapping keys are "{}"'.format(overlap))

					to_pass = tmp_out[key]['definition'].copy()
					for key in kwargs:
						to_pass.update({key:kwargs})
					internal_out = {
						'definition':tmp_out[key]['definition'],
						'data':data_function(tmp_out[key]['data'].copy(), defn = tmp_out[key]['definition'], **to_pass)
					}
				else:
					internal_out = {
						'definition':tmp_out[key]['definition'],
						'data':data_function(tmp_out[key]['data'].copy(), **kwargs)
					}

				tmp_out.update({key:internal_out})
			except Exception as e:
				print('Error in data_function: {} \n{}'.format(data_function.__name__, e))
				print('Skipping data key: {} with defintion: \n{}'.format(key, tmp_out[key]['definition']))

		return Data(tmp_out)

	def to_dict(self):
		"""
		Return a dict of the Data class.  


		returns:
			(dict): a dict class with identical structure"""
		return {key: self[key] for key in self.keys()}

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
			colors = [cm.cmaps_listed[cmap](x) for x in np.linspace(0, 1, len(self.keys()))]
		else: 
			colors = [color for i in range(len(self.keys()))]

		for color, index in zip(colors, self.keys()):
			if x == None:
				data_keys_to_plot = list(self[index]['data'].keys())
			else:
				xs = self[index]['data'][x]
				data_keys_to_plot = set(self[index]['data'].keys()) - set({x})

			if labelby == None:
				label = None
			else:
				label = self[index]['definition'][labelby]

			if type(y) == type(None):
				pass
			else:
				data_keys_to_plot = set(np.array([y]).flatten())
				

			for plotkey in data_keys_to_plot:
				to_plot = self[index]['data'][plotkey]
				
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
			colors = [cm.cmaps_listed[cmap](x) for x in np.linspace(0, 1, len(self.keys()))]
		else: 
			colors = [color for i in range(len(self.keys()))]

		for color, index in zip(colors, self.keys()):
			if x == None:
				data_keys_to_plot = list(self[index]['data'].keys())
			else:
				xs = self[index]['data'][x]
				data_keys_to_plot = set(self[index]['data'].keys()) - set({x})

			if labelby == None:
				label = None
			else:
				label = self[index]['definition'][labelby]

			if type(y) == type(None):
				pass
			else:
				data_keys_to_plot = set(np.array([y]).flatten())
				

			for plotkey in data_keys_to_plot:
				to_plot = self[index]['data'][plotkey]
				
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
