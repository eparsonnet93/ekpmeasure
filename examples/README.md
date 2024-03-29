# Examples

The [user guide](#user-guide) below offers a general overview, though more up to date (and more succinct) examples can be found:

- [Overview](https://github.com/eparsonnet93/ekpmeasure/blob/main/examples/Overview.ipynb) 
- [Data class](https://github.com/eparsonnet93/ekpmeasure/blob/main/examples/Data.ipynb)

Videos:

- [Overview](https://youtu.be/LcwbgeVzw3I)

### User Guide

Here, we will walk through a brief example of how the analysis power of `ekpy`. Scientists often have large amounts of data, stored in different locations and with varying degrees of available meta data. ekpy makes it easier to access all of this data. Once created, you can easily load a [Dataset](https://ekpmeasure.readthedocs.io/en/latest/ekpmeasure.analysis.html#ekpmeasure.analysis.core.Dataset)

Say we have some data stored in `./path/to/data/` which is a bunch of `.csv` files. We can open one of them (called `filename.csv`) up using `pandas.read_csv` and see what's inside:

```python
import pandas as pd
import numpy as np

path = './path/to/data/'
filename = 'filename.csv'

>>> df = pd.read_csv(path + filename)
>>> df.head()
```


<img src="https://github.com/eparsonnet93/ekpmeasure/blob/main/imgs/raw_df.png" width="900">

This data file has some meta data associated with it. Let's assume for this example that `filename.csv` corresponds to the following meta data:

```bash

{
	'voltage_applied':'10.0V',
	'pulsewidth':'100ms'
}

```

*i.e.* the file we have here is for a specific type of stimulus, namely an applied voltage of 10V and a pulsewidth of 100ms (doesn't matter what that actually means, it could be any type of meta data). Let's plot this specific data file. Here I want to plot `Polarization(uC/cm2)_x` and `Polarization(uC/cm2)_y` vs `DRIVEVoltage_x`. 

```python
df.plot(x = 'DRIVEVoltage_x', y = ['Polarization(uC/cm2)_x','Polarization(uC/cm2)_y'])
```


<img src="https://github.com/eparsonnet93/ekpmeasure/blob/main/imgs/raw_plot.png" width="600">

Clearly there is a difference between `'Polarization(uC/cm2)_x'` and `'Polarization(uC/cm2)_y'`, and for this particular case, we are interested in **quantifying that difference** between them. An easy way to do this is by looking at each of their values around `'DRIVEVoltage_x = 0'`, and finding the difference. We will do this in two steps, first find the average of each around zero

```python
def find_avg_P_loop1_loop2(dataframe, center_voltage = 0, window = .1):
	"""
	Find the average of `Polarization(uC/cm2)_x` and `Polarization(uC/cm2)_y` for data corresponding to `center_voltage - window <= DRIVEVoltage_x <= center_voltage + window`

	args:
		dataframe (pandas.DataFrame): DataFrame with columns `Polarization(uC/cm2)_x`, `Polarization(uC/cm2)_y` and `DRIVEVoltage_x`
		center_voltage (float): Center voltage to find average around
		window (float): Window around center voltage to average

	returns:
		(pandas.DataFrame): Average around center_voltage for loop1 and loop2. Columns: 'p1' and 'p2'

	"""

	p1, p2 = dataframe['Polarization(uC/cm2)_x'], dataframe['Polarization(uC/cm2)_y']
	drivevoltage = dataframe['DRIVEVoltage_x']

	#find indices of where the window (center_voltage \pm window) is:
	indexer = (drivevoltage<=center_voltage+window)&(drivevoltage>=center_voltage-window)
	out = {
		'p1': [np.mean(p1[indexer])],
		'p2': [np.mean(p2[indexer])]
	}
	return pd.DataFrame(out)
```

Next we need a function that calculates the difference.

```python
def difference(dataframe):
	"""
	Calculate the absolute value of the difference between dataframe columns `p1` and `p2`.

	args:
		dataframe (pandas.DataFrame): DataFrame with columns `p1` and `p2`

	returns:
		(pandas.DataFrame): Difference between p1 and p2. Columns: `difference`
	"""
	return pd.DataFrame({'difference':abs(dataframe.p1 - dataframe.p2).values})
```

Now we are ready to return to our data and plot our **important metric** called difference. Doing it for the one file is easy:

```python
>>> avgdf = find_avg_P_loop1_loop2(df)
>>> dif = difference(avgdf)
>>> print(dif)
>    difference
0    1.431387
```

Great! Now this was for **one datafile** corresponding to an applied voltage of 10V and a pulsewidth of 100ms. What if I want to this for all of my data which corresponds to a pulsewidth of 100ms, but for all values of applied voltages? Now I need to track down the filenames associated with each of these types of data, sort them by applied voltage and then do the calculations I just did - then return that all in some sort of managable object. The problem is even worse if the meta data is stored *in the file* so you need to open each file in order to see what type it is. **And** what if you have data in multiple folders all over your computer - it gets very hard to manage all this. This is where `ekpy` comes in. Let's assume you have already generated the meta data (this can be done, by using `ekpy` to generate the data see [experiment Class](#https://ekpmeasure.readthedocs.io/en/latest/ekpmeasure.control.html#ekpmeasure.control.core.experiment), or by generating if from existing data see [generate_meta_data](https://ekpmeasure.readthedocs.io/en/latest/ekpmeasure.analysis.html#ekpmeasure.analysis.load.generate_meta_data)) and stored it in `./path/to/data`. We can load all of the associated meta data easily:

```python
from ekpy import analysis

>>> dset = analysis.load_Dataset('./path/to/data/')
>>> dset
```

<img src="https://github.com/eparsonnet93/ekpmeasure/blob/main/imgs/dset1.png" width="900">


`dset` holds all of the meta data. If we want to look at our same file as the example above, we can access it by querying our dataset: (`'pump_amp'` is what we called `'voltage_applied'` and `'pump_pw'` is what we called `'pulsewidth`)

```python
>>> dset.query('pump_amp == "10.0V" and pump_pw == "100ms"')
```
<img src="https://github.com/eparsonnet93/ekpmeasure/blob/main/imgs/querydset1.png" width="900">


This makes it easy to get find data based on the meta data. For example, let's find all of the data associated with **just** the pulsewidth `'pump_pw'` of 100ms.

```python
>>> dset.query('pump_pw == "100ms"')
```

<img src="https://github.com/eparsonnet93/ekpmeasure/blob/main/imgs/querydset2.PNG" width="900">


You can see that for this one pulsewidth, we have *many* applied voltages (`'pump_amp'`). We will return to this in a moment. Let's stick with our query `'pump_amp == "10.0V" and pump_pw == "100ms"'` and see how we can retrieve the real data (see [get_data](#https://ekpmeasure.readthedocs.io/en/latest/ekpmeasure.analysis.html#ekpmeasure.analysis.core.Dataset.get_data)). Recall from above that the raw data has three important columns `'Polarization(uC/cm2)_x'`, `'Polarization(uC/cm2)_y'`,  and `'DRIVEVoltage_x'`

```python
>>> tmpdset = dset.query('pump_amp == "10.0V" and pump_pw == "100ms"')
>>> data = tmpdset.get_data() #retrieve the data
#plot the data
>>> data.plot(x = 'DRIVEVoltage_x', y = ['Polarization(uC/cm2)_x', 'Polarization(uC/cm2)_y'])
```

<img src="https://github.com/eparsonnet93/ekpmeasure/blob/main/imgs/dsetplot1.png" width="600">


Same as before! But now, we can **plot all of the data** corresponding to a pulsewidth of 100ms, with just a very simple modification. 

```python
>>> tmpdset = dset.query('pump_pw == "100ms"')
>>> data = tmpdset.get_data() #retrieve the data
#plot the data
>>> data.plot(x = 'DRIVEVoltage_x', y = ['Polarization(uC/cm2)_x', 'Polarization(uC/cm2)_y'])
```

<img src="https://github.com/eparsonnet93/ekpmeasure/blob/main/imgs/dsetplot2.PNG" width="600">


and done, this is all of the data for 100ms where the color corresponds to the applied voltage (`'pump_amp'`, ranging from 5V to 10V). No more sifting through csv's to find what you're looking for! Let's keep going. Remember, we are interested in the difference between averages around zero voltage for each datafile. We can create a workflow for this using [`Data.apply`](#https://ekpmeasure.readthedocs.io/en/latest/ekpmeasure.analysis.html#ekpmeasure.analysis.core.Data.apply). To understand how this works, let's take a deeper look at what our `data` object really is:


```python
>>> type(data)
> ekpy.analysis.core.Data
```

This [`ekpy.analysis.core.Data`](#https://ekpmeasure.readthedocs.io/en/latest/ekpmeasure.analysis.html#ekpmeasure.analysis.core.Data) is integer indexed and holds the raw data as well as a definition (describing the meta data) for each index. Let's take a look:

```python
>>> tmpdset = dset.query('pump_amp == "10.0V" and pump_pw == "100ms"')
>>> data = tmpdset.get_data() #retrieve the data
>>> data
> {0: {'definition': {'pump_amp': {'10.0V'},
   'pump_pw': {'100ms'},
   'preset_amp': {'9V'},
   'preset_pw': {'1ms'},
   'trial': {0}},
  'data': {'Time(ms)_x': array([0.000e+00, 2.000e-03, 3.000e-03, ..., 1.999e+00, 2.000e+00,
          2.001e+00]),
   'DRIVEVoltage_x': array([-0.002747,  0.013809,  0.027161, ..., -0.029373, -0.01564 ,
          -0.00145 ]),
   'Polarization(uC/cm2)_x': array([-0.41523 , -0.410556, -0.41523 , ..., -0.840587, -0.779822,
          -0.786054]),
   'Time(ms)_y': array([0.000e+00, 2.000e-03, 3.000e-03, ..., 1.999e+00, 2.000e+00,
          2.001e+00]),
   'DRIVEVoltage_y': array([-0.002289,  0.01358 ,  0.027771, ..., -0.028152, -0.014114,
          -0.000992]),
   'Polarization(uC/cm2)_y': array([1.130391, 1.138181, 1.13974 , ..., 0.622455, 0.676988, 0.689453])}}}
```

We have the index (0), for which we have the 'definition' and the 'data'. 'Definition' describes the meta data associated with that index (here it matches our query, of course) and 'data' is a Dict which holds the raw data. Let's now take a look at how to calculate the difference, as before. We will do this using [`Data.apply`](#https://ekpmeasure.readthedocs.io/en/latest/ekpmeasure.analysis.html#ekpmeasure.analysis.core.Data.apply). [`Data.apply`](#https://ekpmeasure.readthedocs.io/en/latest/ekpmeasure.analysis.html#ekpmeasure.analysis.core.Data.apply) takes a function and passes that function the 'data' key for each index in a [`ekpmeasure.analysis.core.Data`](#https://ekpmeasure.readthedocs.io/en/latest/ekpmeasure.analysis.html#ekpmeasure.analysis.core.Data) object. For example, in our current case, since `data` has only one index (0) it will pass the raw data. To make this clear, I will define a function that takes a data_dict as argument, then send use it in `data.apply`

```python
def print_data(data_dict):
	"""Print the data that we are passed and return it"""
	print(data_dict)
	return data_dict

>>> _ = data.apply(print_data)
> {
	'Time(ms)_x': array([0.000e+00, 2.000e-03, 3.000e-03, ..., 1.999e+00, 2.000e+00,
	       2.001e+00]), 
	'DRIVEVoltage_x': array([-0.002747,  0.013809,  0.027161, ..., -0.029373, -0.01564 ,
	       -0.00145 ]), 
	'Polarization(uC/cm2)_x': array([-0.41523 , -0.410556, -0.41523 , ..., -0.840587, -0.779822,
	       -0.786054]), 
	'Time(ms)_y': array([0.000e+00, 2.000e-03, 3.000e-03, ..., 1.999e+00, 2.000e+00,
	       2.001e+00]), 
	'DRIVEVoltage_y': array([-0.002289,  0.01358 ,  0.027771, ..., -0.028152, -0.014114,
	       -0.000992]), 
	'Polarization(uC/cm2)_y': array([1.130391, 1.138181, 1.13974 , ..., 0.622455, 0.676988, 0.689453])
}
```

this is precisely the data stored in the 'data' key on index 0 above. Now let's do something more interesting. I will use our function `find_avg_P_loop1_loop2` from before with a few key changes to make it ready for usage in `Data.apply`. You'll notice now, I am operating on `Dict` not `pandas.DataFrame`, but otherwise everything is the same. 

```python
def find_avg_P_loop1_loop2(data_dict, center_voltage = 0, window = .1):
	"""
	Find the average of `Polarization(uC/cm2)_x` and `Polarization(uC/cm2)_y` for data corresponding to `center_voltage - window <= DRIVEVoltage_x <= center_voltage + window`

	args:
		data_dict (Dict): Dict with keys `Polarization(uC/cm2)_x`, `Polarization(uC/cm2)_y` and `DRIVEVoltage_x`
		center_voltage (float): Center voltage to find average around
		window (float): Window around center voltage to average

	returns:
		(Dict): Average around center_voltage for loop1 and loop2. Keys: 'p1' and 'p2'

	"""

	p1, p2 = data_dict['Polarization(uC/cm2)_x'], data_dict['Polarization(uC/cm2)_y']
	drivevoltage = data_dict['DRIVEVoltage_x']

	#find indices of where the window (center_voltage \pm window) is:
	indexer = (drivevoltage<=center_voltage+window)&(drivevoltage>=center_voltage-window)
	out = {
		'p1': np.array([np.mean(p1[indexer])]),
		'p2': np.array([np.mean(p2[indexer])])
	}
	return out
```

let's try it out on our data.

```python
>>> data.apply(find_avg_P_loop1_loop2)
> {0: {'definition': {'pump_amp': {'10.0V'},
   'pump_pw': {'100ms'},
   'preset_amp': {'9V'},
   'preset_pw': {'1ms'},
   'trial': {0}},
  'data': {'p1': array([-0.62944063]), 'p2': array([0.80194658])}}}
```

Exactly the same as before. Let's finish this out and get our difference. We will need to redefine our `difference` function as well to operate on dicts.

```python
def difference(data_dict):
	"""
	Calculate the absolute value of the difference between dataframe columns `p1` and `p2`.

	args:
		dataframe (Dict): Dict with keys `p1` and `p2`

	returns:
		(Dict): Difference between p1 and p2. Keys: `difference`
	"""
	return {'difference':abs(data_dict['p1'] - data_dict['p2'])}
```
and run it:

```python
>>> data.apply(find_avg_P_loop1_loop2).apply(difference)
> {0: {'definition': {'pump_amp': {'10.0V'},
   'pump_pw': {'100ms'},
   'preset_amp': {'9V'},
   'preset_pw': {'1ms'},
   'trial': {0}},
  'data': {'difference': array([1.43138722])}}}
```

which matches our result from before. Now, the fun part. Let's do it on all of the data corresponding to a pulsewidth of 100ms for any applied voltage. All we have to do is define our definition of the `data` object. 

```python
>>> tmpdset = dset.query('pump_pw == "100ms"')
>>> data = tmpdset.get_data() #retrieve the data
>>> diff_data = data.apply(find_avg_P_loop1_loop2).apply(difference)
```

Now, `diff_data` holds all of our differences for all of the data corresponding to a pulsewidth of 100ms. Equally importantly it is labeled by its complete meta data. Let's say we now want to plot our calculated difference (a *real data* variable) vs pump_amp (a *meta data* variable). This can be done by [`analysis.get_vals_by_definition`](#https://ekpmeasure.readthedocs.io/en/latest/ekpmeasure.analysis.html#ekpmeasure.analysis.data_utils.get_vals_by_definition) (***Remember we can just use `.plot()` to plot real data vs real data***)

```python
vbd = analysis.get_vals_by_definition(diff_data, definition_key='pump_amp', data_key='difference')
```

`vbd` is a Dict with (key, value) pairing (voltage applied, calculated difference for that datafile). To parse such a dict, and turn it into plottable arrays, we can use [`analysis.vals_by_definition_to_2darray`](#https://ekpmeasure.readthedocs.io/en/latest/ekpmeasure.analysis.html#ekpmeasure.analysis.data_utils.vals_by_definition_to_2darray)

```python
import matplotlib.pyplot as plt
# we need to tell it how to convert the string for pump_amp (like "10.0V") into a float, by using the kwarg 'converter'
>>> X, Y = analysis.vals_by_definition_to_2darray(vbd, converter = lambda x: float(x.replace('V', '')))
>>> plt.scatter(X, Y, color = 'blue')
```

<img src="https://github.com/eparsonnet93/ekpmeasure/blob/main/imgs/finalplot1.png" width="600">


And there you have it, we now analyzed all of the data corresponding to 100ms! As a final example in this introduction, let's now plot all of the data. We want difference vs applied voltage colored by pulsewidth. The following code will create it: 

```python
from matplotlib import cm
from ekpy.universal import get_number_and_suffix, time_suffix_to_scientic_str

# sort the pulsewidths in the dataset
def sorter(pw):
	number, suffix = get_number_and_suffix(pw)
	return float(str(number) + time_suffix_to_scientic_str(suffix))

# group, average over trials, sort by 'pump_pw'
data = dset.get_data(groupby='pump_pw').mean().sort(by='pump_pw', key=sorter)

# generate a color map for each pulsewidth
cmap = cm.plasma
colors = [cmap(x) for x in np.linspace(0,1,len(pws))]

# set up a plot
fig, ax = plt.subplots()

for tmpdata, color in zip(data, colors):
	# calculate 
	diff_data = tmpdata.apply(find_avg_P_loop1_loop2).apply(difference)

	# want to plot versus 'pump_amp', a definition key
	vbd = analysis.get_vals_by_definition(diff_data, definition_key='pump_amp', data_key='difference')
	X, Y = analysis.vals_by_definition_to_2darray(vbd, converter = lambda x: float(x.replace('V', '')))
	
	ax.scatter(X, Y, color = color)
```

![finalplot2](https://github.com/eparsonnet93/ekpmeasure/blob/main/imgs/finalplot2.PNG)

Hopefully this has given you a brief introduction to how to use EKPy. Happy analyzing!

For more see [here.](https://ekpmeasure.readthedocs.io/en/latest/start.html)