import numpy as np
import pandas as pd

__all__ = ('initialize_scope','get_waveform')

def initialize_scope(inst, aquisition_number_pts = 5000, channel = 'Ch3', force_yes = False):
    """
    gets the scope ready to return waveform
    """
    if force_yes == False:
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
    must be run after initialize_scope
    returns waveform on the screen (as pandas dataframe): takes time = ~100ms
    time is returned in ns
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