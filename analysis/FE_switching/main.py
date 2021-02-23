import os 
import pandas as pd

__all__ = ('dataset', 'common_name_mapper')

class dataset():
	"""use this class to quickly access data in a dataset"""
	
	def __init__(self, path):
		self.path = path
		try:
			self.meta_data = pd.read_pickle(path+'meta_data')
		except FileNotFoundError:
			print('no meta_data exists in path {}. you may wish to generate it using the function .generate_meta_data'.format(path))
			
	def __repr__(self):
		try:
			return self.meta_data.__repr__()
		except:
			return pd.DataFrame().__repr__()
		
	def __str__(self):
		try:
			return self.meta_data.__str__()
		except:
			return pd.DataFrame().__str__()
		
	def query(self, query_str):
		return self.meta_data.query(query_str)
			
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

def common_name_mapper(fname):
	"""this is a common name mapping function:
	spl is a split on '_'
	
	'identifier':spl[0],
	'pulsewidth_ns':float(spl[1])*1e9,
	'delay_ns':float(spl[2])*1e9,
	'high_voltage_v':float(spl[3].replace('V','').replace('x','.')),
	'preset_voltage_v':float(spl[4].replace('mv',''))/1000,
	'preset_pulsewidth_ns':float(spl[5].replace('ns','')),
	'filename':fname
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