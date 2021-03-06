import pandas as pd
import numpy as np
import time
import itertools

from .misc import get_save_name

__all__ = ('trial','experiment')

class experiment():
    
    def __init__(self):
        return
    
    def config(self, run_function, path):
        self.run_function = run_function
        self.path = path
    
    def n_param_scan(self, kw_scan_params, fixed_params, scan_param_order):
        """need docstring! scan_param_order: the first param will be scanned first (others are fixed)
        
        kw_scan_params: (dict) with key and array like params to scan over
        fixed_params: (dict) fixed params to be passed to trial each time
        """
        if not hasattr(self, 'run_function'):
            raise AttributeError('run_function not yet defined.')
        if not hasattr(self, 'path'):
            raise AttributeError('no save path defined.')
            
        if set(scan_param_order) != set(kw_scan_params.keys()):
            raise KeyError('kw_scan_params do not have the same keys as scan_param_order')
            
        for key in kw_scan_params:
            params = kw_scan_params[key]
            if hasattr(params, '__getitem__') and type(params) != str:
                pass
            else:
                raise TypeError('kw_scan_param: {} must be array-like of params. it is not.'.format(key))
                
        iterable_param_list = list(
            itertools.product(
                *(kw_scan_params[key] for key in scan_param_order[::-1])
            )
        )
        
        for params in iterable_param_list:
            kwargs = fixed_params
            for i, key in enumerate(scan_param_order[::-1]):
                kwargs.update({key:params[i]})
            
            trial(self.run_function, kwargs, self.path)
            time.sleep(1)
        return 


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