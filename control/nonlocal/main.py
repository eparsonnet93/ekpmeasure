import pyvisa
import pandas as pd
import numpy as np

from ..instruments.srs830 import get_lockin_r_theta

__all__ = ('trial', 'run', 'first_and_second_harm')

def trial(lockin, nave = 100, delay = .5):
    out = pd.DataFrame()
    rs, thetas = [],[]
    for i in range(nave):
        time.sleep(delay)
        r, theta = get_lockin_r_theta(lockin)
        rs.append(r)
        thetas.append(theta)
    return pd.DataFrame({'R':rs, 'theta':thetas})

def run(path, devicen, harmonic):
    data = trial(lockin, nave = 50, delay = 1)
    name = str(devicen) + '_Harm'+str(harmonic)
    if name in set(os.listdir(path)):
        yn = input('{} exists in {}. replace? (y/n)'.format(name, path))
    else:
        yn = 'y'
    
    if yn == 'y':
        data.to_csv(path+name, index = False)
    return data

def first_and_second_harm(path, device):
    yn = input('is harmonic at 1')
    out = run(path, device, 1)
    yn  = input('please switch harmonic to 2')
    plt.plot(out.R)
    run(path, device, 2)
    return 