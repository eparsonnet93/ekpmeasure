# Example of how to run MOKE experiment. This was written before I had standardized experimental control code

This operates on a USB_1208HS_4AO daq. 

```python
#imports
from runner import run, daqqer
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

#initialize daq class
#only run this line one time!!
daq = daqqer()
```

```python
#definewaveforms:
#2047 is 0, max amp is +-2047
out_count = 200000

maxvoltage_real = 30

eng_amp = maxvoltage_real/5 #voltage in engineering units. max is 10V

int_amp = int(2047*eng_amp/10)

#sine
wfa = [int_amp * (np.sin(2*6.2832 * i / (out_count))) + 2047 for i in range(out_count)]
wfb = [2047 * (np.sin(6.2832 * 1 * i / (out_count))) + 2047 for i in range(out_count)]

for wf in [wfa, wfb]:
    plt.plot(wf)
```

```python
#configure a run (named r1)
r1 = run(daq)
r1.config(out_channel_start=0, out_channel_end=1, in_channel_start=0, in_channel_end=1,nave=1)

wvfrm_vstack = np.vstack((wfa, wfa))
r1.load_waveform(wvfrm_vstack)

#other settings. quiet and number of averages to do
r1.quiet = True
r1.nave = 10
```

```python
#run the experiment
r1.go()
#retrieve the data (pandas.DataFrame)
r1.get_df()
#plot the data
r1.data.plot(x = 'AOUT_0', y = 'AIN_0')
```