import os 
import pandas as pd
import numpy as np

import warnings

import matplotlib.pyplot as plt
from matplotlib import cm


__all__ = ('Dataset', 'Data', 'dataset')

def construct_Dataset_from_dataframe(function):

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
	"""convert index_to_path pandas series to path_to_index dict 
	----
	index_to_path:(pandas.series)

	returns
	path_to_index:(dict) {path:[indices corresponding to that path]}
	"""
	path_to_index = dict()
	for i in index_to_path.index:
		index, path = i, index_to_path[i]
		if path in set(path_to_index.keys()):
			path_to_index[path].append(index)
		else:
			path_to_index.update({path:[index]})
	return path_to_index

class Dataset(pd.DataFrame):
	"""
	Dataset class for analysis. subclass of pandas.DataFrame. Used to manipulate meta data with reference to the real files that can be retrieved when necessary.
	----

	path: (str or dict) a path to where the real data lives. if dict, form is {path: [indices of initializer for this path]}  
	initializer: (pandas.DataFrame) meta_data. one column must contain a pointer (filename) to where each the real data is stored
	"""

	def __init__(self, path, initializer,readfileby=None):
		super().__init__(initializer)
		self.attrs['path'] = path
		self.attrs['index_to_path'] = self._construct_index_to_path(path, initializer)
		self.pointercolumn = 'filename'
		if readfileby == None:
			self.readfileby = lambda file: pd.read_csv(file)
		else:
			self.readfileby = readfileby

	@property  
	def _is_empty(self):
		if len(self) == 0 and len(self.columns) == 0:
			return True
		else:
			return False

	@property
	def path(self):
		return self.attrs['path']

	@property
	def index_to_path(self):
		return self.attrs['index_to_path']
	
	@construct_Dataset_from_dataframe
	def query(*args, **kwargs):
		return pd.DataFrame.query(*args, **kwargs)

	@construct_Dataset_from_dataframe
	def head(*args, **kwargs):
		return pd.DataFrame.head(*args, **kwargs)
	
	def _construct_index_to_path(self, path, initializer):
		"""
		construct index_to_path from path provided
		----
		path: (str or dict) a path to where the real data lives. if dict, form is {path: [indices of initializer for this path]}  
		initializer: (pandas.DataFrame) meta_data. one column must contain a pointer (filename) to where each the real data is stored

		"""
		if type(path) != dict:
			assert type(path) == str, "path must be dict or str"
			#set all indices to the single path provided
			index_to_path = pd.Series({i:path for i in range(len(initializer))}, dtype = 'object')
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

	def summarize(self):
		"""return a brief summary of the data in your Dataset. Returns Dict"""
		summary = dict()
		for column in self.columns:
			if column == self.pointercolumn:
				continue
			summary.update({column: set(self[column].values)})
		return summary


	def group(self, by):
		"""group data by by and return a pandas dataframe. makes use of pandas.groupby
		----
		by: (str, int, label or array-like()) on what to group. 
		"""
		groups = self.groupby(by = by).groups
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

	def get_data(self, groupby=None, labelby=None,):
		"""
		return data for the current Dataset: returns Data class 
		----
		groupby: (str, label, index or array-like()) what to group on
		labelby: (str, label, index or array-like()) what to label the output data by. This will change 'definition' in output Data class
		"""
		pointercolumn = self.pointercolumn
		readfileby = self.readfileby

		if type(groupby) == type(None):
			data_to_retrieve = self.group(by = pointercolumn) #gives us a unique col for each
		else:
			data_to_retrieve = self.group(by = groupby)

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
					internal_out['data'].update({col: np.vstack((internal_out['data'][col], tdf[col].values)) for col in columns_set})

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
		
class Data(dict):
	"""subclass of dict

	used for grouped real data. dict structure is as follows: 
	{index:
		{
		'data':np.array(the real data), 
		'definition':dict(describing which data is contained)
		}
	}
	"""

	def __init__(self, initializer):
		super().__init__(initializer)

	def mean(self, inplace = False):
		"""
		return data class where data is average across axis 0
		----
		inplace: (bool) do the operation inplace
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
						mean_data.update({k:np.mean(data[k], axis = 0)})
				tmp_out[key].update({'data':mean_data})
			return Data(tmp_out)

		else:
			for key in self:
				data = self[key]['data']
				mean_data = {k:np.mean(data[k], axis = 0) for k in data}
				self[key].update({'data':mean_data})
			return Data(self)

	def apply(self, data_function, kwargs_for_function=None, inplace = False):
		"""apply data_function to the data in each index. returns a data class
		----
		data_function: (function or array-like(function,)) f(dict) -> dict. if array-like, functions will be applied sequentially
		kwargs_for_function: (dict or array-like(dict,)) kwargs for data_function in order to pass additional arguments to the functions being applied
		inplace: (bool) do the operation inplace
		"""
		data_functions = np.array([data_function]).flatten()
		if type(kwargs_for_function) == type(None):
			kwargs_for_functions = [{} for ijk in range(len(data_functions))]
		else:
			kwargs_for_functions = np.array([kwargs_for_function]).flatten()

		if len(kwargs_for_functions) != len(data_functions):
			raise ValueError('kwargs_for_function does not match in count to the number of data_functions supplied')

		tmp_out = self.to_dict().copy()

		for data_function, kwargs_for in zip(data_functions, kwargs_for_functions):
			for key in tmp_out.keys():
				internal_out = {
					'definition':tmp_out[key]['definition'],
					'data':data_function(tmp_out[key]['data'], **kwargs_for)
				}
				tmp_out.update({key:internal_out})

		if inplace:
			self.__init__(tmp_out)
			return
		return Data(tmp_out)

	def to_dict(self):
		"""returns a dict class with identical structure"""
		return {key: self[key] for key in self.keys()}

	def plot(self, x=None, y=None):
		"""simple plot of all data vs key specified by x

		colors correspond to different keys (groups)
		"""

		#todo improve this function
		fig, ax = plt.subplots()

		
		colors = [cm.viridis(x) for x in np.linspace(0, 1, len(self.keys()))]

		for color, index in zip(colors, self.keys()):
			if x == None:
				data_keys_to_plot = list(self[index]['data'].keys())
			else:
				xs = self[index]['data'][x]
				data_keys_to_plot = set(self[index]['data'].keys()) - set({x})

			if type(y) == type(None):
				pass
			else:
				data_keys_to_plot = set(np.array([y]).flatten())
				

			for plotkey in data_keys_to_plot:
				to_plot = self[index]['data'][plotkey]
				
				if len(to_plot.shape) == 1: #1d data
					if x == None:
						ax.plot(to_plot, color = color)
					else:
						ax.plot(xs, to_plot, color = color)
					continue
					
				for i in range(to_plot.shape[0]):
					if x == None:
						ax.plot(to_plot[i,:], color = color)
					else:
						ax.plot(xs[i,:], to_plot[i,:], color = color)

		return fig, ax

class dataset(Dataset):
	"""
	subclass of Dataset - used to initialize/read from a specific folder. dataset, unlike Dataset will search a folder for meta_data and help create it if it does not exist
	----
	path: (str or dict) a path to where the real data lives. if dict, form is {path: [indices of initializer for this path]}  
	initializer: (pandas.DataFrame) meta_data. one column must contain a pointer (filename) to where each the real data is stored

	"""

	def __init__(self, path, meta_data = None):
		"""
		subclass of Dataset - used to initialize/read from a specific folder
		"""
		warnings.showwarning('dataset class is deprecated. use load_Dataset() instead', DeprecationWarning, '', 0,)
		tmp_df = self._build_df(path, meta_data)
		super().__init__(path, tmp_df)

	def _build_df(self, path, meta_data):
		if type(meta_data) == type(None):
			try:
				return pd.read_pickle(path + 'meta_data')
			except FileNotFoundError:
				print('meta_data does not exist in path {} you may want to create it with .generate_meta_data()'.format(path))
				return pd.DataFrame()
		else:
			return meta_data

	def generate_meta_data(self, mapper):
		"""
		generate meta_data from a Dataset
		----

		mapper: (function: filename (str) -> dict) operates on a single file name in order to get the columns (dict key) and values (dict value) for meta_data of that file 
		"""
		if not self._is_empty:
			yn = input('this Dataset already has meta_data, do you wish to recreate it? (y/n)')
			if yn.lower() != 'y':
				return

		for file in os.listdir(self.path):
			try:
				meta_data = pd.DataFrame(mapper(file), index = [0])
			except Exception as e:
				print('unable to process file: {} \nError: {}'.format(file, e))
				continue
			try:
				existing_meta_data = pd.concat([existing_meta_data, meta_data], ignore_index = True)
			except NameError:
				existing_meta_data = meta_data.copy()

		if self.pointercolumn not in set(existing_meta_data.columns): 
			warnings.showwarning('there is no map to key "{}" in mapping function "{}" provided\nEnsure self.pointercolumn property has been set appropriately or else you will be unable to retrieve data'.format(self.pointercolumn, mapper.__name__), SyntaxWarning, '', 0,)

		existing_meta_data.to_pickle(self.path+'meta_data')
		self.__init__(path = self.path, meta_data = existing_meta_data)
		return


	def print_file_name(self):
		"""use this function if you wish to print an example file for help building a mapping function for generate_met_data()"""
		for fname in os.listdir(self.path):
			if fname == 'meta_data' or fname == '.ipynb_checkpoints':
				continue
			else:
				print(fname)
				break