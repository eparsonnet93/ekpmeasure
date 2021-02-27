import os 
import pandas as pd
import numpy as np

import warnings

import matplotlib.pyplot as plt
from matplotlib import cm

__all__ = ('Dataset', 'common_name_mapper', 'Data')


class Dataset(pd.DataFrame):
	"""
	Dataset class for analysis. subclass of pandas.DataFrame. Used to manipulate meta data with reference to the real files that can be retrieved when necessary.
	----

	path: (str) a path to where the real data lives. Dataset will search for a file in path called 'meta_data', if such a file does not exist you will be prompted to create it. You can also provide meta_data directly
	meta_data: (pandas.DataFrame) meta_data. one column must contain a pointer (filename) to where each the real data is stored
	"""

	def __init__(self, path, meta_data = None):
		tmp_df = self._build_df(path, meta_data)
		super().__init__(tmp_df)
		self.path = path
		self.pointercolumn = 'filename'
		self.readfileby = lambda file: pd.read_csv(file)

	@property  
	def _is_empty(self):
		if len(self) == 0 and len(self.columns) == 0:
			return True
		else:
			return False

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

	def dataset_query(self, query_str):
		"""extension of pandas.DataFrame.query. dataset_query returns a dataset
		----
		query_str: (str) string of query. Example 'preset_voltage_v == 1'
		"""
		return Dataset(path = self.path, meta_data = self.query(query_str))

	def summarize(self):
		"""return a brief summary of the data in your Dataset. Returns Dict"""
		summary = dict()
		for column in self.columns:
			if column == 'filename':
				continue
			summary.update({column: set(self[column].values)})
		return summary

	def save(self):
		"""used to save current meta_data to file. This can be used, for example if you wish to delete some specific outlier data, by deleting references to such data in the dataset and the saving the dataset's meta_data using this function"""
		yn = input('you are about to replace whatever existing meta_data exists in path: {} with this Dataset. do you wish to proceed? (y/n)'.format(self.path))
		if yn.lower() == 'n':
			print('save aborted.')
			return
		else:
			print('saved.')
			self.to_pickle(self.path + 'meta_data')
		return

	def print_file_name(self):
		"""use this function if you wish to print an example file for help building a mapping function for generate_met_data()"""
		for fname in os.listdir(self.path):
			if fname == 'meta_data' or fname == '.ipynb_checkpoints':
				continue
			else:
				print(fname)
				break

	def get_grouped_data(self, by):
		"""returns a Dict of the real data grouped by argument by. Makes use of pandas.DataFrame.groupby
		----
		by: (array-like) which columns to group by. Example - to group across trial by should be all columns names excluding trial and filename (or more explicitly the pointer to real data column)
		"""
		warnings.showwarning('get_grouped_data is deprecated. use group() or get_data() instead', DeprecationWarning, '', 0,)

		pointercolumn = self.pointercolumn
		readfileby = self.readfileby
		groups = self.groupby(by=by).groups
		out = {}

		by = list(np.array([by]).flatten())
		
		for k, key in enumerate(groups):
			try:
				group_defn = {b:key[i] for i, b in enumerate(by)}
			except TypeError: #the case with only one element in by
				group_defn = {b:key for b in by}
			indices = groups[key]
			filenames = [self.at[ind, pointercolumn] for ind in indices]
			for l, filename in enumerate(filenames):
				try:
					tdf = readfileby(self.path + filename)
				except Exception as e:
					raise Exception('error reading data. ensure self.readfileby is correct. self.readfileby is currently set to {}.\nError is: {}'.format(self.readfileby.__name__, e))
				
				if l + k == 0:
					columns_set = set(tdf.columns) #to check if all have the same columns; agnostic to what's in the data, but must be consistent

				if set(tdf.columns) != columns_set:
					raise ValueError('not all data in this Dataset has the same columns!')

				if l == 0:
					internal_out = {col:tdf[col].values for col in columns_set}
				else:
					#in vstack, stack the newdata second.
					internal_out = {col: np.vstack((internal_out[col], tdf[col].values)) for col in columns_set}
			out.update({k:{'data':internal_out, 'definition':group_defn}})

		return Data(out) 

	def group(self, by):
		"""need docstring"""
		groups = self.groupby(by = by).groups
		for ijk, key in enumerate(groups):
			original_dataset_indices = groups[key]
			new_row = None
			for index in original_dataset_indices:
				original_row = self.loc[index] #this is a pandas series of a row from the original dataset
				#columns in this row
				if type(new_row) == type(None):
					new_row = {col:set([original_row[col]]) for col in original_row.index}
				else:
					for col in new_row:
						new_row[col].update(set([original_row[col]]))

			if ijk == 0:
				new_df = pd.DataFrame({key:[new_row[key]] for key in new_row})
			else:
				new_df = pd.concat((new_df, pd.DataFrame({key:[new_row[key]] for key in new_row})), ignore_index = True)
				
		return new_df           
	
	def get_data(self, groupby=None, labelby=None,):
		"""needs docstring"""
		pointercolumn = self.pointercolumn
		readfileby = self.readfileby
		
		if type(groupby) == type(None):
			data_to_retrieve = self.group(by = self.pointercolumn) #gives us a unique col for each
		else:
			data_to_retrieve = self.group(by = groupby)
		
		out = {}
		for counter, i in enumerate(data_to_retrieve.index): #for each row
			for k, datafile in enumerate(data_to_retrieve.at[i, self.pointercolumn]): #datafile in the set of datafiles in that row
				try:
					tdf = readfileby(self.path + datafile)
				except Exception as e:
					raise Exception('error reading data. ensure self.readfileby is correct. self.readfileby is currently set to {}.\nError is: {}'.format(self.readfileby.__name__, e))
				
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
			
			
		if type(labelby) == type(None):
			return Data(out)


		labelby = set(np.array([labelby]).flatten())

		for counter in out:
			#pop off the labels we don't want
			definition = out[counter]['definition']
			to_pop = set(definition.keys()) - labelby
			for key in to_pop:
				definition.pop(key)
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
				mean_data = {k:np.mean(data[k], axis = 0) for k in data}
				tmp_out[key].update({'data':mean_data})
			return Data(tmp_out)

		else:
			for key in self:
				data = self[key]['data']
				mean_data = {k:np.mean(data[k], axis = 0) for k in data}
				self[key].update({'data':mean_data})
			return Data(self)

	def apply(self, data_function, inplace = False):
		"""apply data_function to the data in each index. returns a data class
		----
		data_function: (function or array-like) f(dict) -> dict. if array-like, functions will be applied sequentially
		inplace: (bool) do the operation inplace
		"""
		data_functions = np.array([data_function]).flatten()
		tmp_out = self.to_dict().copy()

		for data_function in data_functions:
			for key in tmp_out.keys():
				internal_out = {
					'definition':tmp_out[key]['definition'],
					'data':data_function(tmp_out[key]['data'])
				}
				tmp_out.update({key:internal_out})

		if inplace:
			self.__init__(tmp_out)
			return
		return Data(tmp_out)

	def to_dict(self):
		"""returns a dict class with identical structure"""
		return {key: self[key] for key in self.keys()}

	def plot(self, x=None):
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




def common_name_mapper(fname):
	"""this is a common name mapping function: take for example a file of name 5um3_50e-9_1e-9_0x5V_500mv_10000ns_1
	spl is a split on '_'
	
	'identifier':spl[0],
	'pulsewidth_ns':float(spl[1])*1e9,
	'delay_ns':float(spl[2])*1e9,
	'high_voltage_v':float(spl[3].replace('V','').replace('x','.')),
	'preset_voltage_v':float(spl[4].replace('mv',''))/1000,
	'preset_pulsewidth_ns':float(spl[5].replace('ns','')),
	'filename':fname,
	'trial':int(spl[6])
	"""
	string = fname.replace('.csv','')
	spl = string.split('_')
	
	ordered_keys = ['identifier', 
					'pulsewidth_ns', 
					'delay_ns',
					''
				   ]
	out = dict({
		'identifier':spl[0],
		'pulsewidth_ns':float(spl[1])*1e9,
		'delay_ns':float(spl[2])*1e9,
		'high_voltage_v':float(spl[3].replace('V','').replace('x','.')),
		'preset_voltage_v':float(spl[4].replace('mv',''))/1000,
		'preset_pulsewidth_ns':float(spl[5].replace('ns','')),
		'filename':fname,
		'trial':int(spl[6])
	})
	return out