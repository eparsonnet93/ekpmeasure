from mcculw import ul
from mcculw.enums import ULRange, InfoType, AnalogInputMode
from mcculw.enums import ScanOptions, BoardInfo, TriggerEvent, TrigType, FunctionType
from mcculw.ul import ULError

import ctypes

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from warnings import warn
import os

class DAQ():
    """
    class defining measurement computing USB-1208HS-4AO daq device
    """
    
    def __init__(self,):
        warn('ensure instacal is running')
        return
    
    def configure(self):
        if not hasattr(self, 'board_num'):
            #incase an old session is running:
            ul.release_daq_device(0)
            #initialization vals
            board_num = 0
            ul_range = ULRange.BIP5VOLTS
            ul.set_trigger(board_num, TrigType.TRIG_POS_EDGE, 2000, 2000)
            self.board_num = board_num
            self.ul_range = ul_range
        return

class RUN():
    
    def __init__(self, daq):
        self.daq = daq.configure()
        self.board_num = daq.board_num
        self.ul_range = daq.ul_range
        return
    
    def load_waveform(self,wvfrm_vstack):
        """load a waveform for daq
        ----
        
        wvfrm_stack: numpy.vstack        
        """
        wf_1d, nzeros_front, nzeros_back = waveforms_to_1d_array(wvfrm_vstack)
        self.wf_1d = wf_1d
        self.nzeros_front = nzeros_front
        self.nzeros_back = nzeros_back
        self.input_wfm_df = pd.DataFrame({i:wvfrm_vstack[i,:] for i in range(wvfrm_vstack.shape[0])})
        
    def config(self, out_channel_start,out_channel_end,in_channel_start,in_channel_end,nave,quiet = False):
        """configure run
        ----
        
        out_channel_start: int, specify which start channel to output waveform
        out_channel_end: int
        in_channel_start: int
        in_channel_end: int
        """
        self.out_channel_end = out_channel_end
        self.out_channel_start = out_channel_start
        self.in_channel_end = in_channel_end
        self.in_channel_start = in_channel_start
        self.nave = nave
        self.quiet = quiet
        
    def go(self):
        """start the run"""
        to_average = []
        #stop old processes in case
        ul.stop_background(self.board_num, FunctionType.AOFUNCTION)
        ul.stop_background(self.board_num, FunctionType.AIFUNCTION)

        nchannels_out = self.out_channel_end - self.out_channel_start + 1

        for i in range(self.nave):    
            returned = apply_and_listen(self.wf_1d, self.nzeros_front, self.nzeros_back, 
                                        in_channel_start=self.in_channel_start, in_channel_end=self.in_channel_end, 
                                        out_channel_start=self.out_channel_start, out_channel_end=self.out_channel_end,
                                        quiet = self.quiet)
            memhandle_in, memhandle_out, data_array_in, data_array_out, count_in, time = returned

            # Free the buffer and set the data_array to None
            ul.win_buf_free(memhandle_out)
            data_array_out = None

            #now that it is done convert from data_array back to numpy data:
            out = []
            for i in range(0, count_in):
                out.append(ul.to_eng_units(self.board_num, self.ul_range, data_array_in[i]))
            out = np.array(out)

            #clear memory
            ul.win_buf_free(memhandle_in)
            data_array_in = None

            #append data
            to_average.append(out)

        data = np.array(to_average)
        means = np.mean(data, axis = 0)
        out = waveform_1d_to_array(means, nchannels_in=nchannels_out)
        self.waveform_collected = out
        self.time = time
        return
    
    def plot(self,**kwargs):
        """plot waveform_collected"""
        if not hasattr(self, 'time'):
            raise AttributeError('no data has been collected, suggest self.go()')
            return
        fig, ax = plt.subplots(**kwargs)
        for i in range(self.waveform_collected.shape[0]):
            ax.plot(self.time*1e6, self.waveform_collected[i,:])

        ax.set_xlabel('time (us)')
        return fig, ax

    def get_df(self):
        """return pandas dataframe of waveform_collected"""
        if not hasattr(self, 'waveform_collected'):
            raise AttributeError('no data has been collected, suggest self.go()')

        nchannels_in = self.in_channel_end - self.in_channel_start + 1

        #for time so divide by how many channels in 
        nzeros_front_for_time = int(self.nzeros_front/nchannels_in)
        nzeros_back_for_time = int(self.nzeros_back/nchannels_in)

        time = self.time[nzeros_front_for_time:-nzeros_back_for_time]

        data = pd.DataFrame({
                'time':time,
            })
        warn("You are getting the input wfm data (which is perfect), not measured current input to the coil")
        for i in self.input_wfm_df:
            data['AOUT_{}'.format(i)] = 10*(self.input_wfm_df[i]-2047)/2047

        for i, x in enumerate(self.waveform_collected):
            x_for_data = x[nzeros_front_for_time:-nzeros_back_for_time]
            data['AIN_{}'.format(i)] = x_for_data    

        self.data = data
        return

    def save(self, path, name):
        """save waveform_collected too file"""
        if not hasattr(self, 'data'):
            self.get_df(self)
            
        #check if file name exists:
        file_set = set(os.listdir(path))
        if name in file_set:
            yn = input('file already exists. Overwrite? (y/n)')
            if yn == 'y':
                self.data.to_csv(path+name, index = False)
            else: 
                print('Ok. Skipping.')
        else:
            self.data.to_csv(path+name, index = False)
        return
    
    
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
    returns un- serialized waveform 
    """
    out = np.zeros((int(nchannels_in), int(len(waveform_1d)/nchannels_in)))
    
    for k, pt in enumerate(waveform_1d):
        out[int(np.mod(k, nchannels_in)), int(k/nchannels_in)] = pt
    
    return out