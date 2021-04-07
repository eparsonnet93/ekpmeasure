__all__ = ('measure_field',)

def measure_field(gaussmeter):
    field = float(gaussmeter.query('RDGFIELD?').split('\r')[0])
    return field