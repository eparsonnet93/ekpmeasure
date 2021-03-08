import visa
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time
import os

rm = visa.ResourceManager()
rm.list_resources()

lockin = rm.open_resource('GPIB0::11::INSTR')
lockin.write("*rst")
lockin.query("*IDN?")

def trial(lockin, nave = 100, delay = .5):
    out = pd.DataFrame()
    rs, thetas = [],[]
    for i in range(nave):
        time.sleep(delay)
        r, theta = lockin.query("SNAP? 3,4").split('\n')[0].split(',')
        r, theta = float(r), float(theta)
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

path = './hr345/020221/'

first_and_second_harm(path, 'D0')

out = run(path, 'D32', 1)
###########################

ax = out.plot(y = 'R')
ax1 = ax.twinx()
out.plot(y = 'theta', ax = ax1, color = 'red')