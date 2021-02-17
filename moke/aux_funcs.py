import numpy as np
import pandas as pd

__all__ = ('waveforms_to_1d_array', 'waveform_1d_to_array')


def waveforms_to_1d_array(waveforms):
    """waveforms must be ndarray of shape (n_waveforms, count)
    
    returns 1d serialized waveform and how many zeros are on the front and back
    """
    out = []
    
    #pad with zeros at the beginning (one zero per channel)
    for j in range(waveforms.shape[0]):
        out.append(2047) 
    
    for i in range(waveforms.shape[1]):
        for j in range(waveforms.shape[0]):
            out.append(waveforms[j, i])
    
    #pad with zeros at the end (10 per channel)
    for j in range(waveforms.shape[0]):
        for k in range(10):
            out.append(2047) 
        
    out = np.array(out)
    nzeros_front = waveforms.shape[0]
    nzeros_back = waveforms.shape[0]*10
    return out, nzeros_front, nzeros_back

def waveform_1d_to_array(waveform_1d, nchannels_in = 1):
    """    
    returns un- serialized waveform 
    """
    out = np.zeros((int(nchannels_in), int(len(waveform_1d)/nchannels_in)))
    
    for k, pt in enumerate(waveform_1d):
        out[int(np.mod(k, nchannels_in)), int(k/nchannels_in)] = pt
    
    return out