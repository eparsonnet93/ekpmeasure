import pandas as pd
import numpy as np

from .misc import get_save_name

__all__ = ('trial',)


def trial(run_function, run_function_args, path):
	"""
	A trial  for an experiment. This will save to path with a unique name
	currently supported run_functions are (run_preset_then_2pusle_TDS620B, nonlocal_run_function,) more to come

	any run_function which returns ((str) base_name, (dict) meta_data, (pandas.dataframe) data) should work, but only those indicated above are known to work
	----
	run_function: (function) which function you wish to run i.e. nonlocal_run_function 
	run_function_args: (dict) arguments for run_function
	path: (str) where to save
	"""
	base_name, meta_data, df = run_function(**run_function_args)
	try:
		save_name = get_save_name(base_name, path)
		trial = int(save_name.split('_')[-1].replace('.csv',''))
	except Exception as e:
		save_name = input('there was an error generating a save name: {}\n please enter a unique name'.format(e))
		trial = np.nan


	meta_data.update({'trial':trial, 'filename':save_name})

	assert type(df) == type(pd.DataFrame()), 'run_function {} does not return a pandas.DataFrame as its third return argument, it must'.format(run_function.__name__)

	df.to_csv(path+save_name, index=False)

	#update the meta_data file in this directory
	meta_data = pd.DataFrame(meta_data, index = [0])
	try:
		existing_meta_data = pd.read_pickle(path+'meta_data')
		if set(meta_data.columns) != set(existing_meta_data.columns):
			raise ValueError('the columns of meta_data do not match the existing columns of the data in this path ({}). Please ensure you are producing data of the same type, or move to a new path. Please note, your data was saved with file complete filename: {}, but it was not added to meta_data'.format(path, path+save_name))
		out = pd.concat([existing_meta_data, meta_data], ignore_index = True)
	except FileNotFoundError:
		out = meta_data.copy()

	out.to_pickle(path + 'meta_data')

	return