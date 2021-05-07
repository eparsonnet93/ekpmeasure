__all__ = ('measure_field',)

def measure_field(gaussmeter):
	"""Measure the field.

	args:
		gaussmeter (pyvisa.resources.gbib.GPIBInstrument): Lakeshore 475


	"""
	field = float(gaussmeter.query('RDGFIELD?').split('\r')[0])
	return field