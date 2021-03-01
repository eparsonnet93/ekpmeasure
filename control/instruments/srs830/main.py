__all__ = ('get_lockin_r_theta',)

def get_lockin_r_theta(lockin):
    r, theta = lockin.query('SNAP? 3,4').split('\n')[0].split(',')
    r, theta = float(r), float(theta)
    return r, theta