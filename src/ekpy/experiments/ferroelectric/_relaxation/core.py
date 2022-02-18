import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time
import os
from scipy.integrate import trapz, cumtrapz

from .... import control
from ....control.instruments.berkeleynucleonics765 import stop
from ....control import plotting
from ..switching import two_pulse_run_function

from ....universal import time_suffix_to_scientic_str, get_number_and_suffix



class Relaxation(control.experiment):
    
    def __init__(self, pg, scope, run_function = two_pulse_run_function):
        super().__init__()
        self.pg = pg
        self.scope = scope
        self.run_function = run_function
        
    def _plot(self, data, scan_params):
        if hasattr(self, 'fig'):
            pass
        else:
            fig = plt.figure(figsize = (12, 4))

            ax1 = fig.add_subplot(131)
            ax3 = ax1.twinx()
            ax2 = fig.add_subplot(1,3,(2,3))
            self.fig = fig
            self.ax1 = ax1
            self.ax2 = ax2
            self.ax3 = ax3
        
        
        number, suffix = get_number_and_suffix(scan_params['delay'])
        float_delay = float(str(number) + time_suffix_to_scientic_str(suffix))
        self.ax1.cla()
        self.ax3.cla()
        self.ax2.scatter(float_delay, trapz(data['p1'] - data['p2']), color = 'blue')
        self.ax2.set_xscale('log')
        
        start_index_p1 = data[data.p1>.02].index.values[0]
        start_index_p2 = data[data.p2>.02].index.values[0]
        difference = start_index_p1 - start_index_p2
        data['p2'] = data.p2.shift(difference)
        data = data.dropna()
        
        dp = data['p1'] - data['p2']
        self.ax1.plot(data['time'], dp, color = 'blue')
        to_plot = np.concatenate((np.array([0]), cumtrapz(dp, x = data['time'])))
        self.ax3.plot(data['time'], to_plot, color = 'red')
        self.ax3.set_yticks([])
        self.ax1.set_title('Delay: {}, Voltage: {}'.format(scan_params['delay'], scan_params['high_voltage']))
        plt.show(self.fig)
        plotting.update_plot(self.fig)
        
    def terminate(self, *args, **kwargs):
        stop(self.pg)