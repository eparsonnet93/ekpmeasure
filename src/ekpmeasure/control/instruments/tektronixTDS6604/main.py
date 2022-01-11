import numpy as np
import pandas as pd
from ....universal import get_number_and_suffix, time_to_sci_mapper, voltage_amp_mapper

__all__ = ('initialize_scope','get_waveform', 'set_acquire_stopafter', 'set_triggerA_level',
    'set_triggerA_mode', 'set_acquire_state', 'set_horizontal_resolution','initialize_for_data_transfer',
    'set_data_source', 'set_horizontal_scale')

trigger_modes = {'auto', 'norm'}
acquire_stop_after = {'runst', 'seq'}
channels = {'Ch1','Ch2','Ch3','Ch4','Math1', 'Math2'}

horizontal_scales = {
    '50ps':'50e-12',
    '62.5ps':'62.5e-12',
    '100ps':'100e-12',
    '125ps':'125e-12',
    '200ps':'200e-12',
    '250ps':'250e-12',
    '500ps':'500e-12',
    '1ns':'1e-9',
    '1.25ps':'1.25e-9',
    '2.5ns':'2.5e-9',
    '5ns':'5e-9',
    '10ns':'10e-9',
    '20ns':'20e-9',
    '40ns':'40e-9',
    '80ns':'80e-9',
    '200ns':'200e-9',
    '400ns':'400e-9',
    '1us':'1e-6',
    '2us':'2e-6',
    '4us':'4e-6',
    '10us':'10e-6',
    '20us':'20e-6',
    '40us':'40e-6',
    '100us':'100e-6',
    '200us':'200e-6',
    '400us':'400e-6',
    '1ms':'1e-3'
}

def set_horizontal_scale(inst, scale:str):
    scale = scale.lower()
    if scale not in set(horizontal_scales.keys()):
        raise ValueError('Scale"{}" not allowed, must be in {}'.format(scale, sorted(set(horizontal_scales.keys()))))

    inst.write('horizontal:scale {}'.format(horizontal_scales[scale]))
    return

def set_triggerA_level(inst, level:str):
    """example 500mv"""

    n, s = get_number_and_suffix(level)
    level = str(n) + voltage_amp_mapper[s]
    inst.write('trigger:A:level {}'.format(level))
    return

def set_acquire_stopafter(inst, _type: str):
    """seq or runst"""
    if _type.lower() not in acquire_stop_after:
        raise ValueError('Type {} not allowed, must be {}'.format(_type, acquire_stop_after))

    inst.write('acquire:stopafter {}'.format(_type.lower()))

def set_triggerA_mode(inst, mode: str):
    if mode.lower() not in trigger_modes:
        raise ValueError('Mode {} not allowed, must be {}'.format(mode, trigger_modes))

    inst.write('trigger:A:mode {}'.format(mode.lower()))

def set_acquire_state(inst, state: int):
    """Set acquisistion state, 0 or 1

    args:
        inst (pyvisa.resources.gpib.GPIBInstrument): Tektronix TDS6604
        state (int): 1 (acquire) 0 (static)

    """
    if state not in {0,1}:
        raise ValueError('State must be 1 or 0')

    inst.write('acquire:state {}'.format(state))

def set_horizontal_resolution(inst, number_pts: int = 5000):
    """Set horizontal resolution.

    args:
        inst (pyvisa.resources.gpib.GPIBInstrument): Tektronix TDS6604
        number_pts (int): Number of acquisition points.
    """
    inst.write('hor:reso {}'.format(number_pts))
    inst.write('dat:star 1')
    inst.write('dat:stop {}'.format(number_pts))
    return

def set_data_source(inst, channel: str = 'Ch3'):
    """Set the channel for recording waveform"""
    if channel not in channels:
        raise ValueError('Channel "{}" not allowed, must be in {}'.format(channels))
    inst.write('dat:sou ' + channel)
    return



def initialize_for_data_transfer(inst):
    """
    Set data encoding to ascii and byte count to 1

    args:
        inst (pyvisa.resources.gpib.GPIBInstrument): Tektronix TDS6604
    """
    inst.write('dat:enc asci')
    inst.write('wfmo:byt_n 1')
    return

def initialize_scope(inst, aquisition_number_pts=5000, channel='Ch3', force_init=False, **kwargs):
    """
    Initialize scope to return waveform.

    args:
        inst (pyvisa.resources.gpib.GPIBInstrument): Tektronix TDS6604
        aquisition_number_pts (int): Number of acquisition points.
        channel (str): Channel to acquire waveform from
        force_init (bool): Force initialization despite not being in an acquisition state.



    """
    # TODO: DEPRECATE

    #backwards compatible with some older versions
    if 'force_yes' in set(kwargs.keys()):
        force_init = kwargs['force_yes']

    if force_init == False:
        if inst.query('acq:state?') != '1\n':
            yn = input('scope is not in acquisistion state. Continue? (y/n)')
            if yn == 'n':
                raise ValueError('scope not in acquisition state')
            else:
                print('ok, continuing.')
    if channel not in set({'Ch1','Ch2','Ch3','Ch4','Math1', 'Math2'}):
        raise ValueError('channel ' + str(channel) + ' not supported')
    inst.write('dat:sou ' + channel)
    inst.write('dat:enc asci')
    inst.write('wfmo:byt_n 1')
    number_of_points = aquisition_number_pts
    inst.write('hor:reso '+str(number_of_points))
    inst.write('dat:star 1')
    inst.write('dat:stop '+str(number_of_points))
    return


def get_waveform(inst,):
    """
    Get displayed waveform. This must be run after .initialize_scope(), where one specifies acquisition and channel parameters.

    args:
        inst (pyvisa.resources.gpib.GPIBInstrument): Tektronix TDS6604

    returns:
        (pandas.DataFrame): Displayed waveform with keys 'time' in ns and 'v' in Volts.



    """
    #get waveform
    ymult = inst.query('wfmoutpre:ymult?')
    yoff = inst.query('wfmoutpre:yoff?')
    xinc = inst.query('wfmoutpre:xinc?')
    wf = inst.query('curve?')
    data = np.array([float(d) for d in wf[:-1].split(',')])
    m = float(ymult[:-1])
    data = data - float(yoff[:-1])
    data = data*m
    df = pd.DataFrame({'v':data})
    dt = float(xinc[:-1])
    df['time'] = [i*dt*1e9 for i in range(len(df))]
    return df