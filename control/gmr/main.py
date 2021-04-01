import pandas as pd
import numpy as np
import time


from ..instruments.lakeshore647 import ramp_powersupply_to_current
from ..instruments.lakeshore475 import measure_field
from ..instruments import keithley6221 as k6221
from ..instruments import srs830 as srs 
from .. import core


__all__ = ('measure_field_and_lockin', 'gmr', 'cyclic_gmr', 'GMR')

def measure_field_and_lockin(gaussmeter, lockin, navg=10):
    """returns dict and std of field and resistance at the time called"""
    fields, rs, thetas = [], [], []
    
    for i in range(navg):
        field = measure_field(gaussmeter)
        r, theta = srs.get_lockin_r_theta(lockin)
        time.sleep(.2)
        fields.append(field)
        rs.append(r)
        thetas.append(theta)
    
    
    return dict({'H_mean':np.mean(fields), 'H_std': np.std(fields), 'R_mean':np.mean(rs), 'R_std': np.std(rs), 'Theta_mean':np.mean(rs), 'Theta_std':np.std(thetas)})

def gmr(magnet_power_supply, gaussmeter, lockin, start_current, end_current, steps=100, ramp_rate=.05, avg=5,):
    
    #go to start
    ramp_powersupply_to_current(magnet_power_supply, start_current, .3)
    
    #initialize return
    out = pd.DataFrame({'H_mean':np.zeros(steps), 
                        'H_std':np.zeros(steps),
                        'R_mean':np.zeros(steps), 
                        'R_std':np.zeros(steps), 
                        'Theta_mean':np.zeros(steps), 
                        'Theta_std':np.zeros(steps)
                       })
    
    currents = np.linspace(start_current, end_current, steps)
    for i, current in enumerate(currents):
        ramp_powersupply_to_current(magnet_power_supply, current, ramp_rate) #go to new current
        measurement = measure_field_and_lockin(gaussmeter, lockin, navg=avg)
        out.at[i, 'H_mean'] = measurement['H_mean']
        out.at[i, 'H_std'] = measurement['H_std']
        out.at[i, 'R_mean'] = measurement['R_mean']
        out.at[i, 'R_std'] = measurement['R_std']
        out.at[i, 'Theta_mean'] = measurement['Theta_mean']
        out.at[i, 'Theta_std'] = measurement['Theta_std']
    
    return out
    
def cyclic_gmr(magnet_power_supply, gaussmeter, lockin, low_current, high_current, steps=100, ramp_rate=.05, avg=5, ramp_up_first = True):
    if ramp_up_first:
        start_current = low_current
        end_current = high_current
    else:
        start_current = high_current
        end_current = low_current
    
    first_data = gmr(magnet_power_supply, gaussmeter, lockin, start_current, end_current, steps=steps, ramp_rate=ramp_rate, avg=avg)
    second_data = gmr(magnet_power_supply, gaussmeter, lockin, end_current, start_current, steps=steps, ramp_rate=ramp_rate, avg=avg)
    out = pd.concat((first_data, second_data))
    return out

def gmr_cyclic_run_function(lockin, current_source, gaussmeter, magnet_power_supply, 
    frequency, amplitude, low_current, high_current, steps=100, ramp_rate=.05, 
    ramp_up_first = True, identifier='D', nave=10, delay='default', time_constant='default', 
    sensitivity='default'):
    """
    run function for gmr experiment.

    can be used with control.core.trial()

    returns: basename (str), meta_data (dict), data (pandas.dataframe)
    ----
    lockin: (pyvisa.resources.gpib.GPIBInstrument)
    current_source: (pyvisa.resources.gpib.GPIBInstrument)
    gaussmeter: (pyvisa.resources.gpib.GPIBInstrument)
    magnet_power_supply: (pyvisa.resources.gpib.GPIBInstrument)
    frequency: (str) e.g. 1khz
    amplitude in amps: (str) e.g. 100ua
    identifer: (str) e.g. D1
    nave: (int) how many averages to do
    delay: (float) delay time between averages default is 3xdelay 
    time_constant: (str) default will be 10 x 1/frequency (or cieling nearest allowed lockin timeconstant)
    sensitivity: (str) default will autogain the lockin
    """
    #set up the basename and meta_data
    basename = '{}_{}_{}_{}_{}_{}'.format(
        identifier, frequency, amplitude, low_current, high_current, nave
        ).replace('.', 'x').lower()
    
    #set up the lockin time constant
    if time_constant == 'default':
        time_constant = srs.get_time_constant_from_frequency(frequency, multiplier = 10) #by default

    #get the sleep time 10*time_constant
    if delay == 'default':
        sleep_time = 3*srs.get_time_constant_float(time_constant)
    else:
        sleep_time = delay

    basename += '_{}_{}'.format(time_constant, sleep_time)

    meta_data = {
        'frequency':frequency,
        'amplitude':amplitude,
        'nave':nave,
        'low_current':low_current,
        'high_current':high_current,
        'delay':sleep_time,
        'time_constant':time_constant,
        'ramp_rate':ramp_rate,
        'ramp_up_first':ramp_up_first,
        'identifier':identifier
    }

    #initialize the current source
    k6221.restore(current_source)
    k6221.set_output_sin(current_source,frequency,amplitude)


    #configure run
    srs.initialize_lockin(lockin, 'external', 1, time_constant, frequency = frequency, amplitude = amplitude)

    #start the source (either current or lockin)
    k6221.set_wave_on(current_source)

    #set_lockin_sensitivity. must come after the source on
    srs.set_lockin_sensitivity(lockin, sensitivity, sleep_time)

    #do the measurement
    out = cyclic_gmr(
        magnet_power_supply, gaussmeter, lockin, low_current, high_current, steps=steps, 
        ramp_rate=ramp_rate, avg=nave, ramp_up_first = ramp_up_first
        )

    meta_data.update({'sensitivity': srs.get_sensitivity(lockin)})
    return basename, meta_data, out

class GMR(core.experiment):
    """need docstring"""

    def __init__(self, lockin, current_source, gaussmeter, magnet_power_supply, run_function=gmr_cyclic_run_function):
        super().__init__()
        self.run_function = run_function
        self.lockin = lockin
        self.current_source = current_source
        self.gaussmeter = gaussmeter
        self.magnet_power_supply = magnet_power_supply
        return

    def checks(self, params):
        """initialization checks"""
        pass

    def terminate(self):
        #turn off current source
        k6221.set_wave_off(self.current_source)

        #set lockin idle
        srs.set_reference_source(self.lockin, 'external')
        srs.set_internal_amplitude(self.lockin, '5mv')

        #ramp power supply to zero
        ramp_powersupply_to_current(self.magnet_power_supply, 0, .3)
        return