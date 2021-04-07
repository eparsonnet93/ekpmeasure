import pandas as pd
import numpy as np

__all__ = ('get_wf_from_scope',)

def get_wf_from_scope(scope, channel = 'ch1'):
    """returns pandas df of waveform displayed on scope"""
    scope.query("*idn?")
    #hardcoding channel 1 in 
    scope.write('dat:sou ' + channel)
    #get waveform
    wf = scope.query('curve?')
    scope.write("*wai")
    data = np.array([float(d) for d in wf[:-1].split(',')])

    ###convert to real time and voltage
    preamble = scope.query("wfmpre?")
    scope.write("*wai")

    #get time step on the scope
    scope_dt = float(preamble.split('"s";')[1].split(';')[0])

    #get voltage multiplier:
    vmult = float(preamble.split('"Volts";')[1].split(';')[0])

    #do the conversion
    v_data = vmult*data
    time = np.array([(i - 2500)*scope_dt*1e6 for i in range(len(v_data))]) #in uS
    out_data = pd.DataFrame({'time':time, 'v':v_data})
    return out_data