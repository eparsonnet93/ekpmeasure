from mcculw import ul
from mcculw.enums import ULRange, InfoType, AnalogInputMode
from mcculw.enums import ScanOptions, BoardInfo, TriggerEvent, TrigType, FunctionType
from mcculw.ul import ULError

import ctypes

import numpy as np

__all__ = ('waveforms_to_1d_array', 'waveform_1d_to_array', 'apply_and_listen')

def waveforms_to_1d_array(waveforms):
    """Serialize stack of 1d waveforms. Waveforms must have shape = (n_waveforms, 1d_wvf_len). Pads on front and back with zeros. 

    args:
        waveforms (numpy.ndarray): Typically a vstack of 1d waveforms, must have shape = (n_waveforms, 1d_wvf_len)

    returns:
        (serialized, nzeros_front, nzeros_back): serialized waveform, number of zeros in front, number of zeros in back 

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

def apply_and_listen(waveform_1d, nzeros_front, nzeros_back, 
                     in_channel_start = 0, in_channel_end = 0, 
                     out_channel_start = 0, out_channel_end = 0, 
                     rate = 1000000, board_number = 0, 
                     ul_range = ULRange.BIP10VOLTS, quiet = False):
    """
    Apply a waveform and listen to collect data. Simultaneous output and collection of data. 

    args:
        waveform_1d (numpy.array): Serialized waveform
        nzeros_front (int): Number of zeros padding front of waveform
        nzeros_back (int): Number of zeros padding back of waveform
        in_channel_start (int= 0): Specify which start channel to use when listening and collecting incoming waveform.
        in_channel_end (int= 0): Specify which end channel to use when listening and collecting incoming waveform.
        out_channel_start (int= 0): Specify which start channel to use when outputting the waveform. 
        out_channel_end (int = 0): Specify which end channel to use when outputting waveform. 
        rate (int = 1000000): Rate for daq
        board_number (int = 0): 
        ul_range (ULRange): Range for daq
        quiet (bool): Specify verbosity

    returns:
        (memhandle_in, memhandle_out, data_array_in, data_array_out, count_in, time)


    waveform_1d should be serialized into 1d for all channels
    
    output comes on channels continuous from out_channel_start to out_channel_end
    
    return: memhandle_in, memhandle_out, data_array_in, data_array_out, count_in
    """
    count_out = len(waveform_1d)
    nchannel_out = out_channel_end - out_channel_start + 1
    nchannel_in = in_channel_end - in_channel_start + 1
    
    rate = int(rate/nchannel_in)
    len_data_without_zeros = (len(waveform_1d) - nzeros_front - nzeros_back)
    period_of_wf = (int(len_data_without_zeros/nchannel_out)/rate)
    if not quiet:
    	print('period:',period_of_wf*1e6, 'us')
    
    trigger_rate = int((count_out - nzeros_front - nzeros_back)/nchannel_out)

    # Allocate the buffer and cast it to an unsigned short
    memhandle_out = ul.win_buf_alloc(count_out)
    data_array_out = ctypes.cast(memhandle_out, ctypes.POINTER(ctypes.c_ushort)) #data_array now points to the correct memory


    # Calculate and store the waveform in Windows buffer
    for i, y in enumerate(waveform_1d):
        data_array_out[i] = int(y)

    count_in = int(nchannel_in*count_out/(nchannel_out))

    memhandle_in = ul.win_buf_alloc(count_in)
    data_array_in = ctypes.cast(memhandle_in, ctypes.POINTER(ctypes.c_ushort))

    options = (None,)

    # Output the waveform
    #import pdb; pdb.set_trace()
    ul.a_in_scan(board_number, in_channel_start, in_channel_end, count_in, rate, ul_range, 
                 memhandle_in, ScanOptions.EXTTRIGGER | ScanOptions.BACKGROUND)
    ul.a_out_scan(board_number, out_channel_start, out_channel_end, count_out, rate, ul_range, 
                  memhandle_out, ScanOptions.EXTTRIGGER | ScanOptions.BACKGROUND)
    ul.pulse_out_start(0, 0, rate, 0.5)
    
    while ul.get_status(0, FunctionType.AOFUNCTION).status != 0: #poor mans foreground
        continue
        
    ul.pulse_out_stop(0,0)
    
    ul.stop_background(0, FunctionType.AOFUNCTION)
    ul.stop_background(0, FunctionType.AIFUNCTION)

    timestep = period_of_wf/len_data_without_zeros

    time = []

    for i in range(int(count_out/nchannel_out)):
    	shiftedi = i - nzeros_front
    	time.append(shiftedi*timestep)

    time = np.array(time)

    return memhandle_in, memhandle_out, data_array_in, data_array_out, count_in, time

def waveform_1d_to_array(waveform_1d, nchannels_in = 1):
    """    
    Return a de-serialized waveform stack

    args:
        waveform_1d (numpy.array): Serialized waveform
        nchannels_in (int = 1): Specify the number of channels from which the data was collected. 

    returns:
        (numpy.vstack): Waveform stack. 
    """
    out = np.zeros((int(nchannels_in), int(len(waveform_1d)/nchannels_in)))
    
    for k, pt in enumerate(waveform_1d):
        out[int(np.mod(k, nchannels_in)), int(k/nchannels_in)] = pt
    
    return out