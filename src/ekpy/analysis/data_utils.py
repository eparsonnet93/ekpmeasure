import numpy as np

__all__ = ('get_vals_by_definition', 'vals_by_definition_to_2darray')

def get_vals_by_definition(data, definition_key, data_key):
	"""Returns a dict where key is definition_key value is data from each Data index.

	args:
		definition_key (str or key): Definition key whose value will correspond to the key for the returned dict.
		data_key (str or key): Data key whose value will correspond to the value for the returned dict.

	returns:
		out (dict): Values by definition dict.

	Examples:
		.. code-block:: python

			>>> data
			> {{0: {'definition': {'type': {'preset2pulse'},
			   'identifier': {'125um2'},
			   'pulsewidth_ns': {500.0},
			   'delay_ns': {100000000.0},
			   'high_voltage_v': {1.0},
			   'preset_voltage_v': {1.0},
			   'preset_pulsewidth_ns': {1000.0},
			   'diameter': {12.5},
			   'area': {122.7184630308513},
			   'trial': {0}},
			  'data': {'p1': array([-0.003, -0.003, -0.001, ..., -0.003, -0.003, -0.001]),
			   'time': array([0.0000e+00, 4.0000e-02, 8.0000e-02, ..., 1.9988e+02, 1.9992e+02,
					  1.9996e+02]),
			   'p2': array([-0.001, -0.003, -0.005, ..., -0.003,  0.001,  0.003])}},
			 1: {'definition': {'type': {'preset2pulse'},
			   'identifier': {'125um2'},
			   'pulsewidth_ns': {500.0},
			   'delay_ns': {100000000.0},
			   'high_voltage_v': {0.5},
			   'preset_voltage_v': {1.0},
			   'preset_pulsewidth_ns': {1000.0},
			   'diameter': {12.5},
			   'area': {122.7184630308513},
			   'trial': {0}},
			  'data': {'p1': array([0.0004, 0.0012, 0.0004, ..., 0.002 , 0.002 , 0.0004]),
			   'time': array([0.0000e+00, 4.0000e-02, 8.0000e-02, ..., 1.9988e+02, 1.9992e+02,
					  1.9996e+02]),
			   'p2': array([-0.0004, -0.0004,  0.0004, ...,  0.0012,  0.0012,  0.0004])}},}

			#retrieve 'p1' data keyed by high_voltage_v
			>>> analysis.get_vals_by_definition(data, 'high_voltage_v', 'p1')
			> {	1.0: [-0.003,-0.003, ... ],
				0.5: [0.0004, 0.0012, ...]}
		
	"""
	out = dict()
	for i in data:
		tdat = data[i]
		defn = tdat['definition']
		raw = tdat['data']
		if len(defn[definition_key]) != 1:
			raise ValueError("definition_key {} returned more than one value for data index {} with definition\n{}".format(definition_key, i, defn))
		
		out_key = list(defn[definition_key])[0]
		
		to_append = np.array(raw[data_key]).flatten()
		try:
			for app in to_append:
				out[out_key].append(app)
		except KeyError: #only will occur in out not in defn or raw dicts because already passed those
			out.update({out_key:[app for app in to_append]})
	return out

def vals_by_definition_to_2darray(vals_by_definition, converter='Default', ascending=True):
	"""Convert vals by definition to 2d array. Typically used for plotting and after .get_vals_by_definition().

	args:
		vals_by_definition (dict, vbd): vals by definition dict. See .get_vals_by_definition()
		converter (function): Function to which each value for each key from vals_by_definition is passed. Default is convert to float. 
			```
			converter = lambda x: float(x)
			```
		ascending (bool): Return X in ascending or descending order

	returns:
		(numpy.array (2D)): X, Y

	Examples:
		.. code-block:: python

			>>> vbd
			> { 1.0 : [1,2,3],
				0.5 : [2,1,1]}

			>>> X, Y = analysis.vals_by_definition_to_2darray(vbd)
			>>> X
			> [1.0, 1.0, 1.0, 0.5, 0.5, 0.5]

			>>> Y
			> [1, 2, 3, 2, 1, 1]

	"""
	if type(converter) == str:
		if converter == 'Default':
			converter = lambda x: float(x)

	if not hasattr(converter, '__call__'):
		raise TypeError('Converter must be a function. Got type {}'.format(type(converter)))

	xout, yout = np.array([]), np.array([])
	vbdef = vals_by_definition
	for key in vbdef:
		y = vbdef[key]
		x = [converter(key) for i in y]
		xout = np.concatenate((xout, x))
		yout = np.concatenate((yout, y))

	indexer = list(np.argsort(xout))
	if ascending:
		xout = xout[indexer]
		yout = yout[indexer]
	else:
		xout = xout[indexer[::-1]]
		yout = yout[indexer[::-1]]
		
	return np.vstack((xout, yout))