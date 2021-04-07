from mcculw import ul
from mcculw.enums import ULRange, InfoType, AnalogInputMode
from mcculw.enums import ScanOptions, BoardInfo, TriggerEvent, TrigType, FunctionType
from mcculw.ul import ULError

import numpy as np
import pandas as pd

from warnings import warn
import ctypes

__all__ = ('DAQ','apply_and_listen')

class DAQ():
    """
    class defining measurement computing USB-1208HS-4AO daq device
    """
    def __init__(self,board_num=0):
        warn('ensure instacal is running')
        self.board_num = board_num
        return
    
    def configure(self):
        if not hasattr(self, 'board_num'):
            #incase an old session is running:
            ul.release_daq_device(0)
            #initialization vals
            ul_range = ULRange.BIP5VOLTS
            ul.set_trigger(board_num, TrigType.TRIG_POS_EDGE, 2000, 2000)
            self.ul_range = ul_range
        return

def apply_and_listen(waveform_1d, nzeros_front, nzeros_back, 
                     in_channel_start = 0, in_channel_end = 0, 
                     out_channel_start = 0, out_channel_end = 0, 
                     rate = 1000000, board_number = 0, 
                     ul_range = ULRange.BIP10VOLTS, quiet = False):
    """waveform_1d should be serialized into 1d for all channels
    
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
    ul.a_in_scan(board_number, in_channel_start, in_channel_end, count_in, rate, ul_range, 
                 memhandle_in, ScanOptions.EXTTRIGGER | ScanOptions.BACKGROUND)
    ul.a_out_scan(board_number, out_channel_start, out_channel_end, count_out, rate, ul_range, 
                  memhandle_out, ScanOptions.EXTTRIGGER | ScanOptions.BACKGROUND)
    ul.pulse_out_start(0, 0, rate, 0.5)
    
    while ul.get_status(0, FunctionType.AOFUNCTION).status != 0: #poor mans foreground
        continue
        
    ul.pulse_out_stop(0,0)
    
    ul.stop_background(0, FunctionType.AOFUNCTION) #todo 0 board_num? check documentation
    ul.stop_background(0, FunctionType.AIFUNCTION) #todo 

    timestep = period_of_wf/len_data_without_zeros

    time = []

    for i in range(int(count_out/nchannel_out)):
        shiftedi = i - nzeros_front
        time.append(shiftedi*timestep)

    time = np.array(time)

    return memhandle_in, memhandle_out, data_array_in, data_array_out, count_in, time