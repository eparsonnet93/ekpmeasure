import numpy as np

__all__ = ('get_vals_by_definition', 'vals_by_definition_to_2darray',)

def get_vals_by_definition(data, definition_key, data_key):
	"""returns a dict where key is definition_key and data_key specifies what data to return. For example one might want all data['R'] vs definition['amplitude'].
	----
	needs docstring
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

def vals_by_definition_to_2darray(vals_by_definition, converter = lambda x: float(x)):
	"""needs docstring. takes a dict {key:[some data]} and returns a 2d array [[key],[some_data]]. This can be used as a prestep for curve_fitting or for plotting, for example
	
	converter converts key to float"""
	xout, yout = np.array([]), np.array([])
	vbdef = vals_by_definition
	for key in vbdef:
		y = vbdef[key]
		x = [converter(key) for i in y]
		xout = np.concatenate((xout, x))
		yout = np.concatenate((yout, y))
		
	return np.vstack((xout, yout))