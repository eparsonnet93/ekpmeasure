import numpy as np

__all__ = ('common_name_mapper',)


def common_name_mapper(fname):
	"""Common name mapper used in our experiment. 

	args:
		fname (str): Filename
	 
	Example:
	```
	>>>fname = '5um3_50e-9_1e-9_0x5V_500mv_10000ns_1'
	>>> common_name_mapper(fname)
	> {
		'identifier':5um3,
		'pulsewidth_ns':50,
		'delay_ns':1,
		'high_voltage_v':0.5,
		'preset_voltage_v':0.5,
		'preset_pulsewidth_ns':10000,
		'filename':'5um3_50e-9_1e-9_0x5V_500mv_10000ns_1',
		'trial':1
	}
	```
	"""
	string = fname.replace('.csv','')
	spl = string.split('_')
	
	area_diameter_dict = {
		'{}um'.format(np.round(5 + d*4.5, 1)).replace('0','').replace('.',''):
			(np.pi*((np.round(5 + d*4.5, 1))/2)**2, np.round(5 + d*4.5, 1)) for d in range(9)
	}

	area_diameter_dict.update(
		{
			'125um':(np.pi*(12.5/2)**2, 12.5),
			'25um':(np.pi*(25/2)**2, 25),
			'50um':(np.pi*(50/2)**2, 50),
		}
	)

	area_diameter_dict.update({
			'8um': (np.pi*(8/2)**2, 8),
			'4um': (np.pi*(4/2)**2, 4),
			'6um': (np.pi*(6/2)**2, 6),
		}
	)

	area, diameter = area_diameter_dict[spl[0].split('um')[0] + 'um']

	out = dict({
		'identifier':spl[0],
		'area': area,
		'diameter': diameter,
		'pulsewidth_ns':float(spl[1])*1e9,
		'delay_ns':float(spl[2])*1e9,
		'high_voltage_v':float(spl[3].replace('V','').replace('x','.')),
		'preset_voltage_v':float(spl[4].replace('mv',''))/1000,
		'preset_pulsewidth_ns':float(spl[5].replace('ns','')),
		'filename':fname,
		'trial':int(spl[6])
	})
	return out