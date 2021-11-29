from mcculw import ul
from .control import apply_and_listen, waveforms_to_1d_array, waveform_1d_to_array
from mcculw.enums import ULRange, InfoType, AnalogInputMode
from mcculw.enums import ScanOptions, BoardInfo, TriggerEvent, TrigType, FunctionType
from mcculw.ul import ULError

import ctypes

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from warnings import warn
import os


class daqqer():
    """
    Class defining measurement computing USB-1208HS-4AO daq device
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

class run():
    
    def __init__(self, daq):
        """Class defining a run

        args:
            daq (daqqer): daqqer class for USB_1208HS_4AO

        """
        self.daq = daq.configure()
        self.board_num = daq.board_num
        self.ul_range = daq.ul_range
        return
    
    def load_waveform(self,wvfrm_vstack):
        """Load a waveform stack for the daq. Properly serialize a numpy.vstack of waveforms for usage in the daq.

        args:
            wvfrm_stack (numpy.vstack): Stack of waveforms 1d waveforms. The number of stacked waveforms should match the number of channels used (out_channel_end - out_channel_in) in .config().      
        """
        wf_1d, nzeros_front, nzeros_back = waveforms_to_1d_array(wvfrm_vstack)
        self.wf_1d = wf_1d
        self.nzeros_front = nzeros_front
        self.nzeros_back = nzeros_back
        self.input_wfm_df = pd.DataFrame({i:wvfrm_vstack[i,:] for i in range(wvfrm_vstack.shape[0])})
        
    def config(self, out_channel_start,out_channel_end,in_channel_start,in_channel_end,nave,quiet = False):
        """
        Configure run. All waveforms are serialized into 1d arrays, if you wish to output waveform A on channel 1 and waveform B on channel 2, you should set out_channel_start to 1 and out_channel_end to 2. Then you should load the waveform using .load_waveform() which will properly serialize a waveform stack. 

        args:
            out_channel_start (int): Specify which start channel to use when outputting the waveform. 
            out_channel_end (int): Specify which end channel to use when outputting waveform. 
            in_channel_start (int): Specify which start channel to use when listening and collecting incoming waveform.
            in_channel_end (int): Specify which end channel to use when listening and collecting incoming waveform.
        """
        self.out_channel_end = out_channel_end
        self.out_channel_start = out_channel_start
        self.in_channel_end = in_channel_end
        self.in_channel_start = in_channel_start
        self.nave = nave
        self.quiet = quiet
        
    def go(self, **kwargs):
        """Start the run."""
        to_average = []
        #stop old processes in case
        ul.stop_background(self.board_num, FunctionType.AOFUNCTION)
        ul.stop_background(self.board_num, FunctionType.AIFUNCTION)

        nchannels_out = self.out_channel_end - self.out_channel_start + 1
        nchannels_in = self.in_channel_end - self.in_channel_start + 1

        for i in range(self.nave):    
            returned = apply_and_listen(self.wf_1d, self.nzeros_front, self.nzeros_back, 
                                        in_channel_start=self.in_channel_start, in_channel_end=self.in_channel_end, 
                                        out_channel_start=self.out_channel_start, out_channel_end=self.out_channel_end,
                                        quiet = self.quiet, **kwargs)
            memhandle_in, memhandle_out, data_array_in, data_array_out, count_in, time = returned
            try:
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
            except Exception as e:
                #clear memory
                try:
                    ul.win_buf_free(memhandle_in)
                    ul.win_buf_free(memhandle_out)
                    raise e
                except:
                    raise e


        data = np.array(to_average)
        means = np.mean(data, axis = 0)
        out = waveform_1d_to_array(means, nchannels_in=nchannels_in)
        self.waveform_collected = out
        self.time = time
        return
    
    def plot(self,**kwargs):
        """Plot collected waveform (self.waveform_collected)"""
        if not hasattr(self, 'time'):
            raise AttributeError('no data has been collected, suggest self.go()')
            return
        fig, ax = plt.subplots(**kwargs)
        for i in range(self.waveform_collected.shape[0]):
            ax.plot(self.time*1e6, self.waveform_collected[i,:])

        ax.set_xlabel('time (us)')
        return fig, ax

    def get_df(self, quiet = False):
        """Create new self attribute 'data' which is a pandas.DataFrame of the collected data."""
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
        if not quiet:
            warn("You are getting the input wfm data (which is perfect), not measured current input to the coil")
        for i in self.input_wfm_df:
            data['AOUT_{}'.format(i)] = 10*(self.input_wfm_df[i]-2047)/2047

        for i, x in enumerate(self.waveform_collected):
            x_for_data = x[nzeros_front_for_time:-nzeros_back_for_time]
            data['AIN_{}'.format(i)] = x_for_data    

        self.data = data
        return

    def save(self, path, name):
        """Save waveform to file. Saves self.waveform_collected to file."""
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