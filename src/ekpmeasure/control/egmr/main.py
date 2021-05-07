from ..instruments import keithley6221 as k6221
from ..instruments import srs830 as srs 
from ..instruments import tektronix3252 as tek
from .. import core

import time
import numpy as np
import pandas as pd

__all__ = ('ready_for_pulse', 'pulse', 'EGMR', 'collect_lockin_data')

def ready_for_pulse(pulse_gen, voltage_pulse_amplitude, voltage_pulse_width, inverted = False):
    """need docstring"""
    if inverted:
        tek.set_function_to_pulse(pulse_gen)
        tek.set_polarity(pulse_gen, inverted = True)
        tek.set_low_voltage(pulse_gen, '-'+voltage_pulse_amplitude)
        tek.set_high_voltage(pulse_gen, '0v',)
        tek.set_pulsewidth(pulse_gen, voltage_pulse_width)
        tek.set_ncylces_for_burst_mode(pulse_gen, ncycles=1)
        tek.set_run_mode_to_burst(pulse_gen)
    else:
        tek.set_function_to_pulse(pulse_gen)
        tek.set_polarity(pulse_gen, )
        tek.set_low_voltage(pulse_gen, '0v')
        tek.set_high_voltage(pulse_gen, voltage_pulse_amplitude,)
        tek.set_pulsewidth(pulse_gen, voltage_pulse_width)
        tek.set_ncylces_for_burst_mode(pulse_gen, ncycles=1)
        tek.set_run_mode_to_burst(pulse_gen)
    return

def pulse(pulse_gen):
    tek.start_pulse_gen(pulse_gen,)
    tek.trigger(pulse_gen)
    tek.stop_pulse_gen(pulse_gen,)
    return

def collect_lockin_data(lockin, npoints, delay_between_points):
    """
    Collects npoints of data with delay specified from lockin. 
    
    args:
        lockin (pyvisa.resources.gpib.GPIBInstrument): srs830
        npoints (int): Number of points to collect
        delay_between_points (float): Sleep time (as timed by python)
        
    returns:
        (dict): Dict with keys 'R', 'theta'
    """
    rs, thetas = [], []
    
    for i in range(npoints):
        r, theta = srs.get_lockin_r_theta(lockin)
        time.sleep(delay_between_points)
        rs.append(r)
        thetas.append(theta)
        
    return {'R':np.array(rs), 'theta':np.array(thetas)}

def cycle(lockin, pulse_generator, voltage_pulse_amplitude, voltage_pulse_width, npoints_after_pulse, delay_between_points,):
    """need docstring"""
    #start by pulsing up
    ready_for_pulse(pulse_generator, voltage_pulse_amplitude, voltage_pulse_width, inverted = False)
    #pulse up
    pulse(pulse_generator)
    
    updata = collect_lockin_data(lockin, npoints_after_pulse, delay_between_points)
    
    #ready for down
    ready_for_pulse(pulse_generator, voltage_pulse_amplitude, voltage_pulse_width, inverted = True)
    #pulse down
    pulse(pulse_generator)
    
    downdata = collect_lockin_data(lockin, npoints_after_pulse, delay_between_points)
    
    out = {'R':np.concatenate((updata['R'], downdata['R'])), 'theta': np.concatenate((updata['theta'], downdata['theta']))}
    
    return out

def egmr(lockin, pulse_generator, voltage_pulse_amplitude, 
    voltage_pulse_width, ncycles, npoints_after_pulse, delay_between_points,):
    """need docstring"""

    #get initial baseline
    baseline = collect_lockin_data(lockin, npoints_after_pulse, delay_between_points)
    out = pd.DataFrame(baseline)

    for i in range(ncycles):
        tmpdata = pd.DataFrame(
            cycle(lockin, pulse_generator, voltage_pulse_amplitude, voltage_pulse_width, npoints_after_pulse, delay_between_points)
        )
        out = pd.concat((out, tmpdata), ignore_index=True)
    
    return out


def egmr_run_function(lockin, pulse_generator, current_source, voltage_pulse_amplitude, 
    voltage_pulse_width, current_frequency, current_amplitude, lockin_time_constant, 
    lockin_sensitivity, ncycles, npoints_after_pulse, delay_between_points, identifier = 'D', 
    magnetic_field = 0):
    """
    Run function for egmr experiment at a static applied magnetic field

    args:
        lockin (pyvisa.resources.gpib.GPIBInstrument): SRS830
        pulse_generator (pyvisa.resources.gpib.GPIBInstrument): Tektronix AFG 3252
        current_source (pyvisa.resources.gpib.GPIBInstrument): Keithley 6221
        voltage_pulse_amplitude (str): Amplitude of the pulse.
        voltage_pulse_width (str): Voltage pulsewidth
        current_frequency (str): Frequency of sense current
        current_amplitude (str): Amplitude of sense current
        lockin_time_constant (str): Time constant for srs
        lockin_sensitivity (str): Sensitivity for srs
        ncycles (int): A cycle is defined as one pulse up, one pulse down (total of two pulses). How many cycles
        npoints_after_pulse (int): Number of points to collect after pulsing one direction.
        delay_between_points (float): Delay between acquisition (timed by python). time.sleep() between asking for lockin data
        identifier (str): Identifier for device
        magnetic_field (float): Field in Oe from the Gaussmeter


    returns: 
        basename (str) 
        meta_data (dict) 
        data (pandas.dataframe)
    """
    meta_data = locals()
    meta_data.pop('lockin')
    meta_data.pop('pulse_generator')
    meta_data.pop('current_source')
    #set up the basename and meta_data
    basename = '{}_{}_{}_{}_{}_{}_{}_{}_{}'.format(
        identifier, voltage_pulse_amplitude, voltage_pulse_width, 
        current_amplitude, current_frequency, ncycles, npoints_after_pulse,
        delay_between_points, magnetic_field
        ).replace('.', 'x').lower()

    #initialize the current source
    k6221.restore(current_source)
    k6221.set_output_sin(current_source,current_frequency,current_amplitude)


    #configure run
    srs.initialize_lockin(lockin, 'external', 1, lockin_time_constant)

    #start the source 
    k6221.set_wave_on(current_source)

    #set_lockin_sensitivity. must come after the source on
    srs.set_sensitivity(lockin, lockin_sensitivity)

    #do the measurement
    out = egmr(
        lockin, pulse_generator, voltage_pulse_amplitude, 
        voltage_pulse_width, ncycles, npoints_after_pulse, delay_between_points,
    )

    return basename, meta_data, out

class EGMR(core.experiment):
    """need docstring"""

    def __init__(self, lockin, pulse_generator, current_source, run_function=egmr_run_function):
        super().__init__()
        self.run_function = run_function
        self.lockin = lockin
        self.current_source = current_source
        self.pulse_generator = pulse_generator
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

        #turn off pulse gen
        tek.stop_pulse_gen(self.pulse_generator, both = True)
        return