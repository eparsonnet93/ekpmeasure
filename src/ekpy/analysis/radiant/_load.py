import pandas as pd
import numpy as np
import warnings

__all__ = ('load_radiant_loop_from_text_file','read_loop_txt', 'read_radiant_txt', 'generic_mapper')

def load_radiant_loop_from_text_file(file, measured_value='Charge', return_meta_data=False, delimiter=','):
	raise NameError('"load_radiant_loop_from_text_file" is deprecated. Please use "read_loop_txt"')

def read_loop_txt(file, measured_value='Charge', return_meta_data=False, delimiter=','):
	"""Load a radiant loop from a text file. Typically one would use 'Charge' for measured_value unless one accurately measured capacitor area and input correctly into the Radiant UI.

	args:
		file (str): Filename and path. 
		measured_value (str): 'Charge' or 'Polarization' or 'Current'. Current is returned in mA
		return_meta_data (bool): Return meta data (dict)
		delimiter (str): Delimiter for data file

	returns:
		(pandas.DataFrame, (dict)): Data, Optional: (meta data)


	"""
	raise NotImplementedError("'read_loop_txt' has been deprecated. use 'read_radiant_txt' instead.")
	warnings.showwarning("you may want to try using 'read_radiant_txt' instead. read_radiant_txt is capabable of handling more than just loop data (i.e. PUND etc.)", UserWarning, '', '')
	if measured_value.lower() not in set({'charge', 'polarization', 'current'}):
		raise ValueError('measured_value {} not supported. must be either "charge" or "polarization"'.format(measured_value))
		
		
	with open(file, 'rb') as f:
		lines = f.readlines()

	newlines = []

	for i, line in enumerate(lines):
		#radiant's file structure is the worst
		newlines.append(str(line.decode('windows-1252').replace('»', '').replace('«', '').replace(' ', '').replace('\r', '').replace('\n', '').replace('µ', 'u')))

	lines = newlines

	meta_data = dict()
	data = []
	for line in lines:
		spl = line.split(':,')
		if len(spl)>1: #often there is a comma before the actual data. why? who knows! this is the case where there exists such a comma
			meta_data.update({spl[0]:spl[1]})
			continue
		#now try the case with no comma:
		spl = line.split(':')
		if len(spl)>1: 
			meta_data.update({spl[0]:spl[1]})
			continue
		else:
			data.append(line)

	out = dict()
	i = 0 #counter for when we have established column names

	pointer_dict = dict() #holds which column index points to which column name
	for row in data:
		spl = row.split(delimiter)
		if len(spl)<=1: #there are some rows in here which are not data and they are therefor not comma sep
			continue

		if i == 0: #establish column names
			out.update({spl[a]:[] for a in range(len(spl))})
			pointer_dict.update({a:spl[a] for a in range(len(spl))})
			i+=1
			continue

		try:
			for ijk, a in enumerate(spl):
				out[pointer_dict[ijk]].append(float(a))
		except ValueError: #could not convert to float (i.e. nonnumeric data)
			continue
		
	out = pd.DataFrame(out)
	if len(out) == 0:
		raise ValueError('No data. Is your delimiter correct?')
	out.drop(columns = ['Point'], inplace = True)
	
	if measured_value.lower() == 'charge':
		try:
			out['MeasuredPolarization'] = out['MeasuredPolarization']*float(meta_data['SampleArea(cm2)'])*1e6 #to convert from uC to pC
		except KeyError:
			raise KeyError('no key "MeasuredPolarization", is this a current loop? use measured_value="current"')
		out.rename(columns = {'MeasuredPolarization':'MeasuredCharge(pC)'}, inplace = True)
	elif measured_value.lower() == 'polarization':
		out.rename(columns = {'MeasuredPolarization':'MeasuredPolarization(uC/cm2)'}, inplace = True)
	if return_meta_data:
		return out, meta_data
		
	return out

def generic_mapper(fname, path, delimiter='\t'):
	"""A basic mapper function for radiant datasets. Can include data of different types as well (e.g. hysteresis and current loops). Returns meta_data with keys ['filename', 'type', 'samplename', 'samplearea(cm2)', 'samplethickness(um)', 'volts', 'field']
	
	args:
		fname (str): Filename
		path (str): Path to file
		delimiter (str): Data delimiter
		
	examples:
		
		.. code-block:: python
		
			>>> analysis.generate_meta_data('./', generic_mapper, pass_path=True)
	"""
	out = {'filename':fname}
	_, meta_data = read_radiant_txt(path+fname, delimiter=delimiter, return_meta_data=True)
	keys = ['Type', 'SampleName', 'SampleArea(cm2)', 'SampleThickness(um)', 'Volts', 'Field', 'PulseWidth(ms)', 'PulseDelay(ms)']
	for key in keys:
		try:
			out.update({key:float(meta_data[key])})
		except ValueError:
			out.update({key:meta_data[key]})
		except KeyError:
			out.update({key:np.nan})
			
	# period is a weird one
	try:
		out.update({'Period(ms)':float(meta_data['{}Period(ms)'.format(meta_data['Type'].capitalize())])})
	except:
		pass
	return out

def read_radiant_txt(file, measured_charge=True, return_meta_data=False, delimiter='\t'):
	"""Load a radiant data file (typically as generated from quicklook functions). Supported data types are pund, hysteresis, simplepulse, currentloop. If retrieving a hysteresis file, one would typically use 'True' for measured_charge unless one accurately measured capacitor area and input correctly into the Radiant UI.

	args:
		file (str): Filename and path. 
		measured_hysteresis_value (bool): *For hysteresis files only*, wheter to return hysteresis data in charge, not polarization
		return_meta_data (bool): Return meta data (dict)
		delimiter (str): Delimiter for data file

	returns:
		(pandas.DataFrame, (dict)): Data, Optional: (meta data)
	"""
	supported_types = {'pund', 'hysteresis', 'simplepulse', 'currentloop', 'advancedpiezo'}

	lines = _get_lines(file)
	# find where the data starts
	try:
		where_data = lines.index('Data')
	except ValueError:
		raise ValueError('Unable to find any data i.e. "Data" in file "{}". Please confirm you are using the correct file'.format(file))

	meta_datalines = lines[:where_data]
	datalines = lines[where_data+1:]
	
	data_file_type = meta_datalines.pop(0).lower()
	if data_file_type not in supported_types:
		raise ValueError('Data type "{}" not yet supported. Must be of type {}'.format(data_file_type, supported_types))

	# sometimes radiant puts multiple lines that claim to be the start of Data, sometimes its called "data", sometimes "valid data"
	to_remove = []
	for index, line in enumerate(datalines):
		if 'Data' in line:
			to_remove.append(index)

	# now we have isolated the actual data
	try:
		datalines = datalines[max(to_remove)+1:]
	except ValueError:
		pass

	# build the meta data
	meta_data = {'Type':data_file_type}
	for line in meta_datalines:
		if ':{}{}'.format(delimiter, delimiter) in line: # as is the case sometimes, but not always!!
			spl = line.split(':{}{}'.format(delimiter, delimiter))
		elif ':{}'.format(delimiter) in line: # as is the case sometimes, but not always!!
			spl = line.split(':{}'.format(delimiter))
		elif ':' in line:
			spl = line.split(':')
		else:
			continue
		meta_data.update({spl[0]:spl[1]})


	# build the data
	if data_file_type == 'hysteresis':
		data = _hystersis_parser(datalines, delimiter=delimiter)
		if measured_charge:
			try:
				data['MeasuredPolarization'] = data['MeasuredPolarization']*float(meta_data['SampleArea(cm2)'])*1e6 #to convert from uC to pC
			except KeyError:
				raise KeyError('no key "MeasuredPolarization", is this a current loop? use measured_value="current"')
			data.rename(columns = {'MeasuredPolarization':'MeasuredCharge(pC)'}, inplace = True)
		else:
			data.rename(columns = {'MeasuredPolarization':'MeasuredPolarization(uC/cm2)'}, inplace = True)
	elif data_file_type == 'currentloop':
		data = _hystersis_parser(datalines, delimiter=delimiter)
	elif data_file_type == 'advancedpiezo':
		data = _hystersis_parser(datalines, delimiter=delimiter)
	elif data_file_type == 'pund':
		data = _pund_parser(datalines, delimiter=delimiter)
	elif data_file_type == 'simplepulse':
		data = _pund_parser(datalines, delimiter=delimiter)
	else:
		raise ValueError('data file type "{}" not supported.'.format(data_file_type))
		
	if return_meta_data:
		return data, meta_data
		
	return data

def _get_lines(file):
	# do a bunch of crap to make their data readable
	with open(file, 'rb') as f:
		lines = f.readlines()

	newlines = []

	for i, line in enumerate(lines):
		#radiant's file structure is the worst
		newlines.append(str(line.decode('windows-1252').replace(
			'»', ''
		).replace(
			'«', ''
		).replace(
			' ', ''
		).replace(
			'\r', ''
		).replace(
			'\n', ''
		).replace(
			'µ', 'u'
		).replace(
			'â', ''
		).replace('Â', '')
						   ))

	lines = newlines
	
	# loop to remove blank lines
	remove = True
	while remove:
		try:
			lines.remove('')
		except ValueError:
			remove = False
			
	return lines


def _hystersis_parser(datalines, delimiter='\t'):
	# get column headers
	colnames = datalines.pop(0).split(delimiter) 

	if not len(colnames)>1:
		raise ValueError('Unable to determine data column names. Is your delimter correct? It is currently set to "{}"'.format(delimiter))

	data = {col:[] for col in colnames}
	for ijk, line in enumerate(datalines):       
		try:
			spl = line.split(delimiter)
			if len(spl) != len(colnames):
				continue
			for col, val in zip(colnames, spl):
				data[col].append(float(val.replace(',', '')))

		except Exception as err:
			if ijk == len(datalines)-1:
				continue
			else: 
				raise err

	data = pd.DataFrame(data)
	return data

def _pund_parser(datalines, delimiter='\t'):
	data = {}
	for ijk, line in enumerate(datalines):
		try:
			spl = line.split(':')
			if len(spl)!= 2:
				continue
			data.update({spl[0]:[float(spl[1].replace(',', ''))]})
		except Exception as err:
			if ijk == len(datalines)-1:
				continue
			else: 
				raise err
	return pd.DataFrame(data)