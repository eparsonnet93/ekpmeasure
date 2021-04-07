# ekpmeasure

Repository of computer control code for various experiments as well as analysis code. 

---
## Installation:

```bash
pip install ekpmeasure
```
---

## Contents:

1. [Analysis Overview](#analysis)

2. [Dataset](#dataset)

3. [load_dataset](#load_dataset)
	
4. [Data](#data)

5. [Control Overview](#control)

6. [experiment](#experiment)

7. [n_param_scan](#n_param_scan)


## Analysis
### Dataset

The Dataset class can be used broadly as a means to manipulate meta data and quickly retrieve true data. It is datatype agnostic and allows for merging of datasets from different locations on disk. 

Often I find that I have large amounts of data in stored in different locations and it is difficult to group data and or compare across a set of experimental parameters by leveraging data from multiple locations. Often this ends up being a manual and arduous process. Take for example the following tree of data:
```bash
data
│
└───folder1
│   │   10V_100ns_1mv.csv
│   │   10V_10ns_1mv.csv
│   
└───folder2
    │   5V_100ns_1mv.csv
    │   10V_100ns_1mv.csv
    │   10V_50ns_2mv.csv
```
Further, for example purposes lets assume each file has the identical data namely:

```
raw_data
1
2
3
```

Each of the files (e.g. 5V_100ns_1mv.csv) is a data file, and the file name encodes the meta data. In this case the meta_data consists of three parameters (voltage, time, voltage). If I want to average all trials in data that correspond to (10V, 100ns, 1mv) I will need to retrieve data from folder1 and folder2  and then average the two together. If I wanted to compare all data that corresponds to 10V as the first parameter and 1mv as the second parameter with the second parameter  being the independent variable I would need to retrieve 
```bash
folder1/10V_100ns_1mv.csv
folder2/10V_100ns_1mv.csv
folder1/10V_10ns_1mv.csv
```

Dataset aims to simplify this process. Dataset is a subclass of [pandas.DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html). Dataset takes as parameters a path (where the true data is stored) and an initializer (meta_data) for example in the example above we might define two Datasets (one for each of folder1 and folder2) as 
```python
path = './data/folder1'
meta_data = pandas.DataFrame(
	{
		'param1':['10V', '10V'], 
		'param2':['100ns', '10ns'], 
		'param3':['1mv', '1mv'],
		'filename':['10V_100ns_1mv.csv', '10V_10ns_1mv.csv'],
	}
)
dset = Dataset(path, meta_data)
```
to assist in generating such meta_data you may wish to use the [dataset](#dataset-1) class which searches a folder for you and allows you to automatically create meta_data. Once a Dataset is created, you can retrieve the data easily:

```python
dset.get_data()
```

This returns a [Data](#data) class. As a brief example of how to use the Dataset class, consider one the problems stated above of wanting to compare all data that corresponds to 10V as the first parameter and 1mv as the second parameter with the second parameter. This is done in a straightforward way using Dataset (done here by using [dataset](#dataset-1):

```python
>>> import ekpmeasure.analysis as ekp

>>> path1 = './data/folder1/'
>>> path2 = './data/folder2/'

>>> dset1 = ekp.dataset(path1) #dataset NOT Dataset
>>> dset2 = ekp.dataset(path2)

>>> dset = ekp.merge((dset1, dset2))
>>> dset.query("param1 == '10V' and param3 == '1mv'")
>
  param1 param2 param3           filename
0    10V  100ns    1mv  10V_100ns_1mv.csv
1    10V   10ns    1mv   10V_10ns_1mv.csv
2    10V  100ns    1mv  10V_100ns_1mv.csv

>>> dset.query("param1 == '10V' and param3 == '1mv'").get_data()
>
{
	0: {'definition': {'param1': {'10V'}, 'param2': {'100ns'}, 'param3': {'1mv'}},
		'data': {'raw_data': array([[1, 2, 3],
	      [1, 2, 3]], dtype=int64)}},
	1: {'definition': {'param1': {'10V'}, 'param2': {'10ns'}, 'param3': {'1mv'}},
		'data': {'raw_data': array([1, 2, 3], dtype=int64)}}
}

```

#### load_dataset
One can load a Dataset from a path. This method earches a folder for a pickle file (.pkl) of name 'meta_data' or will inform the user that none exists. 

```python
load_dataset(path)
```
If no meta_data exists, one can use the generate_meta_data method. mapper is a function of a single filename that returns a dict of parameters for meta_data. For example, in the example

```python
def mapper(fname):
    spl = fname[:-4].split('_')
    
    out = {
        'param1':spl[0],
        'param2':spl[1],
        'param3':spl[2],
        'filename':fname
    }
    return out

>>> mapper('10V_100ns_1mv.csv')
>
{
	'param1':'10V', 
	'param2':'100ns', 
	'param3':'1mv',
	'filename':'10V_100ns_1mv.csv'
}
```

then one might use:

```python
generate_meta_data(path, mapper)
dset = load_dataset(path)
```

### Data
Subclass of Dict. The Data class holds real data. It allows for operations to be done on all data simultaneously by 

```python
>>> some_data = dset.get_data(groupby='param1')
>>> some_data
>
{
	0: {'definition': {'param1': {'10V'},
	   	'param2': {'100ns', '10ns', '50ns'},
	   	'param3': {'1mv', '2mv'}},
	  	'data': {'raw_data': array([[1, 2, 3],
	          [1, 2, 3],
	          [1, 2, 3],
	          [1, 2, 3]], dtype=int64)}},
	1: {'definition': {'param1': {'5V'}, 'param2': {'100ns'}, 'param3': {'1mv'}},
	  	'data': {'raw_data': array([1, 2, 3], dtype=int64)}}
}
```
```python
#some function will square the data

def some_function(data_dict):
	"""a function which operates on the data dict and returns a data dict"""
    out = dict()
    for key in data_dict:
        out.update({key:data_dict[key]**2})
    return out
```

```python
>>> some_data.apply(some_function)
>
{
	0: {'definition': {'param1': {'10V'},
   		'param2': {'100ns', '10ns', '50ns'},
   		'param3': {'1mv', '2mv'}},
  		'data': {'raw_data': array([[1, 4, 9],
          [1, 4, 9],
          [1, 4, 9],
          [1, 4, 9]], dtype=int64)}},
 	1: {'definition': {'param1': {'5V'}, 'param2': {'100ns'}, 'param3': {'1mv'}},
  		'data': {'raw_data': array([1, 4, 9], dtype=int64)}}}
```

## Control
Control is a repository of instrument control code in addition to experimental control (often making use of one or more instruments). Experimental data obtained by using the [experiment](#experiment) class will automatically generate meta_data for usage in analysis.

### experiment
The experiment base class serves to manage scans over desired parameters via the [n_param_scan](#n_param_scan) method and properly save + generate meta_data for usage in [analysis](#analysis)

#### n_param_scan

n_param_scan can be used to scan over a set of parameters in an experiment

```python
#set up the experiment class
exp = magnon.Magnon(lockin=lockin, current_source='current_source', run_function=magnon.nonlocal_run_function_lockin_only)
exp.config_path(path)
```

now you can configure your n_param_scan

```python
#parameters to scan over
kw_scan_params = {
    'frequency':['147hz',],
    'amplitude':['200mv', '500mv', '1000mv', '1500mv','2000mv'],
    'harmonic':[1]
}

#fixed params for each scan
fixed_params = {
    'lockin':lockin,
    'identifier':'D19',
    'angle':40,
    'channel_width':1,
    'channel_length':20,
    'bar_width':1.5,
    'nave':5,
    'delay':'default', 
    'time_constant':'1s',
    'sensitivity':'10uv/pa'
}

#order of keys for scan params
order = ['harmonic', 'frequency', 'amplitude']

exp.n_param_scan(kw_scan_params, fixed_params, order)
```
