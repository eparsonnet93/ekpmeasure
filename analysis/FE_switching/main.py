import os 
import pandas as pd
import numpy as np
try:
	from IPython.display import display
except ModuleNotFoundError:
	pass

import matplotlib.pyplot as plt
from matplotlib import cm

__all__ = ('dataset', 'common_name_mapper', 'grouped_dataset')



class dataset():
	"""use this class to quickly access data in a dataset"""
	
	def __init__(self, path, meta_data=None):
		self.path = path
		if type(meta_data) == type(None):
			try:
				self.meta_data = pd.read_pickle(path+'meta_data')
			except FileNotFoundError:
				print('no meta_data exists in path {}. you may wish to generate it using the function .generate_meta_data'.format(path))
		else: 
			assert type(meta_data) == type(pd.DataFrame()), "provided meta_data is not of type pandas.dataframe but rather type: {}".format(type(meta_data))
			self.meta_data = meta_data

			
	def __repr__(self):
		if hasattr(self, 'meta_data'):
			try:
				display(self.meta_data)
				return ''
			except NameError:
				return self.meta_data.__repr__()
		else:
			return pd.DataFrame().__repr__()
	
	def __str__(self):
		try:
			return self.meta_data.__str__()
		except AttributeError:
			return pd.DataFrame().__str__()
		
	def query(self, query_str):
		"""pandas query operation"""
		return dataset(self.path, meta_data = self.meta_data.query(query_str))
			
	def generate_meta_data(self, mapper):
		"""
		generate meta_data from a dataset
		returns meta_data (pd.dataframe)
		----
		
		mapper: (function: filename (str) -> dict) operates on a single file name in order to get the columns (dict key) and values (dict value) for meta_data of that file 
		"""
		if hasattr(self, 'meta_data'):
			yn = input('this dataset already has meta_data, do you wish to recreate it? (y/n)')
			if yn.lower() == 'n':
				return
		for file in os.listdir(self.path):
			try:
				meta_data = pd.DataFrame(mapper(file), index = [0])
			except Exception as e:
				print('unable to process file: {} \n Error: {}'.format(file, e))
				continue
			try:
				existing_meta_data = pd.concat([existing_meta_data, meta_data], ignore_index = True)
			except NameError:
				existing_meta_data = meta_data.copy()
		
		existing_meta_data.to_pickle(self.path+'meta_data')
		self.meta_data = existing_meta_data
		return

	def summarize(self):
		"""return a brief summary of the data in your dataset"""
		summary = dict()
		for column in self.meta_data.columns:
			if column == 'filename':
				continue
			summary.update({column: set(self.meta_data[column].values)})
		print(summary)
		return

	def sort_values(self, **kwargs):
		"""uses pandas sort_values function"""
		return dataset(self.path, meta_data = self.meta_data.sort_values(**kwargs))

	def plot_vs_time(self, plot_type, filename_column = 'filename', **kwargs):
		"""plot_type must be p1, p2, dp

		only basic plotting is supported. more complex functions should be implemented elsewhere
		"""

		if plot_type.lower() not in set({'p1', 'p2', 'dp'}):
			raise ValueError('only plot_types of p1, p2, or dp are supported. attempting to use {}'.format(plot_type))

		data_type = lambda x, df: (df.p1 - df.p2).values if x == 'dp' else df[x].values 

		fig, ax = plt.subplots(**kwargs)
		colors = [cm.magma(x) for x in np.linspace(0,1,len(self.meta_data))]
		for color, file in zip(colors, self.meta_data[filename_column].values):
			tdf = pd.read_csv(self.path + file)
			tdata = data_type(plot_type, tdf)
			ax.plot(tdf.time, tdata, color = color)
			
		return fig, ax


class grouped_dataset(dataset):
	
	def __init__(self, path, meta_data = None):
		"""groups without reference to filename or trial, i.e. you are able to get groups with common everything else except trial and filename"""
		super().__init__(path, meta_data)
		self.by = list(set(self.meta_data.columns) - set({'trial', 'filename'}))
		self.run_grouping()
		
	def run_grouping(self):
		groups = self.meta_data.groupby(by=self.by).groups #dict where key is the set of columns which were grouped on and value is list of indices of meta_data

		#the index of groupdf holds the index for which group to calculate the average on
		groupdf = pd.DataFrame({col:np.array(list(groups.keys()))[:,ijk] for ijk, col in enumerate(self.by)})
		groupdf['group_index'] = [i for i in range(len(groupdf))]
		self.groupdf = groupdf
		self.groups = groups
		
	def __repr__(self):
		if hasattr(self, 'groupdf'):
			try:
				display(self.groupdf)
				return ''
			except NameError:
				return self.groupdf.__repr__()
		else:
			return pd.DataFrame().__repr__()

	def __str__(self):
		try:
			return self.groupdf.__str__()
		except AttributeError:
			return pd.DataFrame().__str__()
		
	def get_data_for_group_index(self, index):
		"""returns a dict
		----
		index: (iter) some indices to return data for
		"""
		out = {}
		group_indices = list(index)
		groups = self.groups
		
		group_keys = list(groups.keys())
		group_keys_tmp = []
		for x in group_indices:
			group_keys_tmp.append(group_keys[x])
			
		group_keys = group_keys_tmp
		
		mdat = self.meta_data
		for ind, key in zip(group_indices, group_keys):
			#import pdb; pdb.set_trace()
			n = len(groups[key])
			out.update({
				ind:{'time':np.vstack([pd.read_csv(self.path + mdat.at[groups[key][i], 'filename']).time.values for i in range(n)]),
					 'p1':np.vstack([pd.read_csv(self.path + mdat.at[groups[key][i], 'filename']).p1.values for i in range(n)]),
					 'p2':np.vstack([pd.read_csv(self.path + mdat.at[groups[key][i], 'filename']).p2.values for i in range(n)]),
					 'group_key':key
					}
			})
		return self.grouped_data(out)
	
	class grouped_data(dict):
		
		def __init__(self, data_dict):
			super().__init__(data_dict)
			self.data_dict = data_dict
		
		def mean(self):
			"""takes the mean on time, p1, and p2 for each key in self.data_dict
			
			returns dict
			"""
			out = dict()
			for key in self.data_dict:
				out.update({
					key:{
						'time':np.mean(self.data_dict[key]['time'], axis = 0),
						'p1':np.mean(self.data_dict[key]['p1'], axis = 0),
						'p2':np.mean(self.data_dict[key]['p2'], axis = 0),
						'group_key':self.data_dict[key]['group_key']
					}
				})
			return out


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