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
	"""Dataset class for analysis. 

	Dataset is a subclass of pandas.DataFrame. Used to manipulate meta data while keeping track of location for the real data, which can be retrieved when necessary.

	Args:
	    path (str or dict): a path to where the real data lives. if dict, form is 

	    		{path: [indices of initializer for this path]} 

	    initializer (pandas.DataFrame):  the meta data. one column must contain a pointer (i.e. filename) to where the real data is stored
	    readfileby (function): how to read the data. default of None corresponds to 

	    		pandas.read_csv()

	"""

	def __init__(self, path, initializer, readfileby=None):
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
		"""Return path to data."""
		return self.attrs['path']

	@property
	def index_to_path(self):
		"""Return Dict of index and corresponding path"""
		return self.attrs['index_to_path']

	@property
	def summary(self):
		"""Return a brief summary of the data in your Dataset. 

		Returns:
		    summary (Dict): a summary of the Dataset"""
		summary = dict()
		for column in self.columns:
			if column == self.pointercolumn:
				continue
			summary.update({column: set(self[column].values)})
		return summary
	
	@construct_Dataset_from_dataframe
	def query(*args, **kwargs):
		"""Query the columns of a DataFrame with a boolean expression.

		Parameters:
			expr (str): The query string to evaluate. You can refer to variables in the environment by prefixing them with an ‘@’ character like @a + b. You can refer to column names that are not valid Python variable names by surrounding them in backticks. Thus, column names containing spaces or punctuations (besides underscores) or starting with digits must be surrounded by backticks. (For example, a column named “Area (cm^2) would be referenced as Area (cm^2)). Column names which are Python keywords (like “list”, “for”, “import”, etc) cannot be used. For example, if one of your columns is called a a and you want to sum it with b, your query should be `a a` + b.
		
		Returns:
			dataset (Dataset): the result of the query
		"""
		return pd.DataFrame.query(*args, **kwargs)

	@construct_Dataset_from_dataframe
	def head(*args, **kwargs):
		return pd.DataFrame.head(*args, **kwargs)

	@construct_Dataset_from_dataframe
	def filter_on_column(self, column, function, **kwargs_for_function):
		return self[self[column].apply(function, **kwargs_for_function).values].reset_index()

	def remove_index(self, index):
        """
        Remove an index or array-like of indices.

        args:
        	index (index or array-like): index to be removed

        returns:
			out (Dataset): updated Dataset

        """
        index = np.array([index]).flatten()
        
        #adjust index_to_path and convert to path_to_index
        path = _convert_ITP_to_path_to_index(self.index_to_path.drop(index = index).reset_index(drop = True))
        meta_data = self.drop(index = index).reset_index(drop = True)
        return Dataset(path, meta_data, readfileby=self.readfileby)
    
    
    def remove_nonexistant_files_from_metadata(self):
        """
        Remove references to files that do not exist in path.
        """
        remove_index = []
        for ind, path in enumerate(t.index_to_path):
            if _check_file_exists(path, self[self.pointercolumn].iloc[ind]):
                continue
            else:
                remove_index.append(ind)
        
        return self.remove_index(remove_index)
	
	def _construct_index_to_path(self, path, initializer):
		"""construct index_to_path from path provided
		
		args:
			path (str or Dict): a path to where the real data lives. if dict, form is {path: [indices of initializer for this path]}  
			initializer (pandas.DataFrame: meta data. one column must contain a pointer (filename) to where each the real data is stored

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

	def _summarize(self):
		"""return a brief summary of the data in your Dataset. Returns Dict"""
		warnings.showwarning('_summarize() is deprecated please use .summary', DeprecationWarning, '', 0,)
		summary = dict()
		for column in self.columns:
			if column == self.pointercolumn:
				continue
			summary.update({column: set(self[column].values)})
		return summary


	def _group(self, by):
		"""Group data by 'by' and return a pandas dataframe. makes use of pandas.groupby

		args:
			by (str, int, label or array-like of): on what to group. 
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
		Return data in Data (Data class) for the current Dataset: returns Data class 
		
		args:
				groupby (str, label, index or array-like of):  what to group on
				labelby (str, label, index or array-like of):  what to label the output data by. This will change 'definition' in output Data class

		returns:
				data (Data): the data
		"""
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
				out[key].update(set({value for value in defn[key]}))
			except KeyError:
				out.update({key:set({value for value in defn[key]})})
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

	@property
	def iloc(self):
		"""indexing like pandas iloc. This returns Data class of specified index. 
		usage : Data.iloc[0]
		"""
		return iDataIndexer(self.to_dict().copy())

	@property 
	def summary(self):
		"""return a summary of the definitions in data"""
		return _summarize_data(self.to_dict().copy())

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

	def filter(self, data_condition_function_dict, definition_condition_dict):
		"""need docstring"""
		
		assert len(data_condition_function_dict) == 1, "more than one condition supplied in data_condition_function_dict. only one is supported at a time."
		data_function_key = list(data_condition_function_dict)[0]
		assert hasattr(data_condition_function_dict[data_function_key], '__call__'), "value associated with key '{}' in data_condition_function_dict is a not a function. is type {}".format(data_condition_function_dict, type(data_condition_function_dict[data_function_key]))
		assert data_function_key in set(self[0]['data'].keys()), "data_function_key '{}' not in data. available keys are {}".format(data_function_key, set(self['data'].keys()))
		
		sat_indices = self._get_indices_satisfying_definition_condtion(definition_condition_dict)
		all_index = set(self.keys())
		not_sat_indices = all_index - set(sat_indices)
		
		func = data_condition_function_dict[data_function_key]
		
		for index in sat_indices:
			old = self[index]['data'][data_function_key]
			old_shape = old.shape
			self[index]['data'].update({data_function_key:old[func(old)]})
			
		return Data(self.to_dict())

	def contains(self, condition):
		"""returns data specified by condition
		----
		condition: (dict) key is definition key, value is value to search for. multiple values provided will be joined by logical or, i.e. {'high_voltage_v':{'100mv', '200mv'}} will search for all data with '100mv' or '200mv' for high_voltage_v. multiple keys provided will be joined with logical AND. i.e. {'x':1, 'y':2} will search for x = 1 and y = 2.

		example: 
		Data.constains({'high_voltage_v':'100mv'}) will return all data indices with high_voltage_v containing 100mv
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
		kwargs_for_function: (dict or array-like(dict,)) kwargs for data_function in order to pass additional arguments tfo the functions being applied
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
				try:
					internal_out = {
						'definition':tmp_out[key]['definition'],
						'data':data_function(tmp_out[key]['data'].copy(), **kwargs_for)
					}
					tmp_out.update({key:internal_out})
				except Exception as e:
					print('Error in data_function: {} \n{}'.format(data_function.__name__, e))
					print('Skipping data key: {} with defintion: \n{}'.format(key, tmp_out[key]['definition']))

		if inplace:
			self.__init__(tmp_out)
			return
		return Data(tmp_out)

	def to_dict(self):
		"""returns a dict class with identical structure"""
		return {key: self[key] for key in self.keys()}

	def plot(self, x=None, y=None, ax=None):
		"""simple plot of all data vs key specified by x

		colors correspond to different keys (groups)
		----
		
		"""
		if ax == None:
			fig, ax = plt.subplots()
			return_fig = True
		else:
			return_fig = False

		
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

		if return_fig:
			return fig, ax
		else:
			return ax

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