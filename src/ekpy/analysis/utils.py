import pandas as pd
import numpy as np

import warnings

from .core import Dataset, Data
from .core import _convert_ITP_to_path_to_index

__all__ = ('merge_Datasets', 'merge_Datas', 'concat_Datas', 'concat_Datasets')

def concat_Datas(datas):
	"""Concatenate data.

	args:
		datas (iter of Data): Iterable of Data objects to merge.

	returns:
		(Data): Concatenated data.

	"""

	if not hasattr(datas, '__iter__'):
		raise TypeError('datas is not iterable.')

	for i, data in enumerate(datas):
		if i == 0:
			out = data.to_dict().copy()
			continue
		tmp = data.to_dict()
		current_len = len(out)
		for index in tmp:
			out.update({current_len+index:tmp[index]})

	return Data(out)

def merge_Datas(tpl, by:str):
	"""Merge tpl of Data on definition key (by). 
	
	args:
		tpl (array-like): Array-like of Data objects
		by (str): Definition key to merge on
		
	returns:
		(Data): Merged Data. 
		
	example:
	
		.. code-block:: python
		
			>> data1 = Data({
				0 : {
					'definition': {'param1':{'eric'}, 'param2':{'merge_on'}},
					'data':{'data1':[0,1,2]}
				}
			})

			>> data2 = Data({
				0 : {
					'definition': {'param1':{'othername'}, 'param2':{'merge_on'}},
					'data':{'data1':[3,4,5]}
				}
			})
			
			>> merge_Datas((data1, data2), by='param2')
			> {0: {  'data': {'data1_0': [0, 1, 2], 'data1_1': [3, 4, 5]},
					 'definition': {'param1_0': {'eric'},
									'param1_1': {'othername'},
									'param2': {'merge_on'}}}}
									
			>> data3 = Data({
				0 : {
					'definition': {'param1':{'eric'}, 'param2':{'this will be its own index'}},
					'data':{'data1':[0,1,2]}
				}
			})
			> {0: {'data': {'data1_0': [0, 1, 2], 'data1_1': [3, 4, 5]},
				 'definition': {'param1_0': {'eric'},
								'param1_1': {'othername'},
								'param2': {'merge_on'}}},
			 1: {'data': {'data1_0': [0, 1, 2]},
				 'definition': {'param1_0': {'eric'},
								'param2': {'this will be its own index'}}}}
	
	"""
	by_options = concat_Datas(tpl).summary[by]
	
	out_dict = dict()
	
	for i, b in enumerate(by_options):
		
		definition_dicts = []
		data_dicts = []
		
		for dat in tpl:
			tdat = dat.contains({'{}'.format(by):[b]})
			if len(tdat)==0:
				continue
			if len(tdat)>1:
				raise ValueError("At least one Data has more than one index corresponding to condition: data.contains({{'{}':[{}]}}). Try grouping before matching?".format(by, b))
			definition_dicts.append(tdat.definition)
			data_dicts.append(tdat.data)
			
		defn = _merge_datadefinition_dicts(definition_dicts, by=by)
		data_dict = _merge_datadefinition_dicts(data_dicts, by=by)
		out_dict.update({i:{'definition':defn, 'data':data_dict}})
		
	return Data(out_dict)

def merge_Datasets(datasets):
	raise NameError('merge_Datasets was deprecated following version 0.1.4. Use "concat_Datasets" instead! (It has the exact some functionality)')

def concat_Datasets(datasets):
	"""Concatenate datasets.

	args:
		datasets (iter of Dataset): Iterable of Dataset objects to merge.

	returns:
		(Dataset): Concatenated dataset.

	"""
	
	if not hasattr(datasets, '__iter__'):
		raise TypeError('datasets is not iterable.')

	readfileby = datasets[0].readfileby
	for dset in datasets[1:]:
		if dset.readfileby != readfileby:
			raise ValueError('not all datasets have the same function for readfileby. Ensure they agree and try again.')
		
	columns = datasets[0].columns
	for dset in datasets[1:]:
		if len(columns) != len(dset.meta_data.columns):
			raise ValueError('supplied datasets do not all have the same columns!')
		if (columns != dset.meta_data.columns).all():
			raise ValueError('supplied datasets do not all have the same columns!')
	
	for i, dset in enumerate(datasets):
		if i == 0:
			new_path = dset.index_to_path
			new_df = pd.DataFrame(dset.meta_data)
		else:
			new_path = pd.concat((new_path, dset.index_to_path), ignore_index = True)
			new_df = pd.concat((new_df, pd.DataFrame(dset.meta_data)), ignore_index = True)
			
	path = _convert_ITP_to_path_to_index(new_path)
	
	return Dataset(path,new_df,readfileby=readfileby)