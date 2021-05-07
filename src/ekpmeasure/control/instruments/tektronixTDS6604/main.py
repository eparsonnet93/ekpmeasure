import numpy as np
import pandas as pd

__all__ = ('initialize_scope','get_waveform')

def initialize_scope(inst, aquisition_number_pts = 5000, channel = 'Ch3', force_init = False, **kwargs):
    """
    Initialize scope to return waveform.

    args:
        inst (pyvisa.resources.gpib.GPIBInstrument): Tektronix TDS6604
        aquisition_number_pts (int): Number of acquisition points.
        channel (str): Channel to acquire waveform from
        force_init (bool): Force initialization despite not being in an acquisition state.



    """
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