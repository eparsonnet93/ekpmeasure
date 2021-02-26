import os 
import pandas as pd
import numpy as np

__all__ = ('dataset', 'common_name_mapper')



class dataset(pd.DataFrame):
	"""
	dataset class for analysis. subclass of pandas.DataFrame. Used to manipulate meta data with reference to the real files that can be retrieved when necessary.
	----

	path: (str) a path to where the real data lives. dataset will search for a file in path called 'meta_data', if such a file does not exist you will be prompted to create it. You can also provide meta_data directly
	meta_data: (pandas.DataFrame) meta_data. one column must contain a pointer (filename) to where each the real data is stored
	"""
	
	def __init__(self, path, meta_data = None):
		tmp_df = self._build_df(path, meta_data)
		super().__init__(tmp_df)
		self._path = path
		
	@property
	def path(self):
		return self._path
	
	def _build_df(self, path, meta_data):
		if type(meta_data) == type(None):
			try:
				return pd.read_pickle(path + 'meta_data')
			except FileNotFoundError:
				print('meta_data does not exist in path {} you may want to create it with .generate_meta_data()'.format(path))
				return pd.DataFrame()
		else:
			return meta_data
	
	@property  
	def _is_empty(self):
		if len(self) == 0 and len(self.columns) == 0:
			return True
		else:
			return False

	def dataset_query(self, query_str):
		"""extension of pandas.DataFrame.query. dataset_query returns a dataset
		----
		query_str: (str) string of query. Example 'preset_voltage_v == 1'

		"""
		return dataset(path = self.path, meta_data = self.query(query_str))
		
	def generate_meta_data(self, mapper):
		"""
		generate meta_data from a dataset
		----

		mapper: (function: filename (str) -> dict) operates on a single file name in order to get the columns (dict key) and values (dict value) for meta_data of that file 
		"""
		if not self._is_empty:
			yn = input('this dataset already has meta_data, do you wish to recreate it? (y/n)')
			if yn.lower() == 'n':
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

		existing_meta_data.to_pickle(self.path+'meta_data')
		self.__init__(path = self.path, meta_data = existing_meta_data)
		return
	
	def summarize(self):
		"""return a brief summary of the data in your dataset. Returns Dict"""
		summary = dict()
		for column in self.columns:
			if column == 'filename':
				continue
			summary.update({column: set(self[column].values)})
		return summary
	
	def get_grouped_data(self, by):
		"""returns a Dict of the real data grouped by argument by. Makes use of pandas.DataFrame.groupby
		----
		by: (array-like) which columns to group by. Example - to group across trial by should be all columns names excluding trial and filename (or more explicitly the pointer to real data column)
		"""
		groups = self.groupby(by=by).groups
		out = {}

		for k, key in enumerate(groups):
			group_defn = {b:key[i] for i, b in enumerate(by)}
			indices = groups[key]
			filenames = [self.at[ind, 'filename'] for ind in indices]
			for l, filename in enumerate(filenames):
				tdf = pd.read_csv(self.path + filename)
				if l + k == 0:
					columns_set = set(tdf.columns) #to check if all have the same columns; agnostic to what's in the data, but must be consistent
				
				if set(tdf.columns) != columns_set:
					raise ValueError('not all data in this dataset has the same columns!')

				if l == 0:
					internal_out = {col:tdf[col].values for col in columns_set}
				else:
					internal_out = {col: np.vstack((internal_out[col], tdf[col].values)) for col in columns_set}
			out.update({k:{'data':internal_out, 'defn':group_defn}})
			
		return grouped_data(out)

	def save(self):
		"""used to save current meta_data to file. This can be used, for example if you wish to delete some specific outlier data, by deleting references to such data in the dataset and the saving the dataset's meta_data using this function"""
		yn = input('you are about to replace whatever existing meta_data exists in path: {} with this dataset. do you wish to proceed? (y/n)'.format(self.path))
		if yn.lower() == 'n':
			print('save aborted.')
			return
		else:
			print('saved.')
			self.to_pickle(self.path + 'meta_data')

	

class grouped_data(dict):
	"""subclass of dict
	
	used for grouped real data. dict structure is as follows: 
	{index:
		{
		'data':np.array(the real data), 
		'defn':dict(describing which data is contained)
		}
	}
	"""
	
	def __init__(self, initializer):
		super().__init__(initializer)
		
	def mean(self, inplace = False):
		if not inplace:
			tmp_out = {}
			for key in self:
				tmp_out.update({key:self[key].copy()})
				data = self[key]['data']
				mean_data = {k:np.mean(data[k], axis = 0) for k in data}
				tmp_out[key].update({'data':mean_data})
			return grouped_data(tmp_out)
			
		else:
			for key in self:
				data = self[key]['data']
				mean_data = {k:np.mean(data[k], axis = 0) for k in data}
				self[key].update({'data':mean_data})
			return grouped_data(self)


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