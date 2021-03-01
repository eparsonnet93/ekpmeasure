

# ekpmeasure

Repository of computer control code for various experiments as well as analysis code. 

---

## Contents:

> 1. [Analysis Overview](#analysis)
	>>a. [Dataset](#dataset)
		>>>i. [dataset](#dataset-1)
	
>>b. [Data](#data)

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
to assist in generating such meta_data you may wish to use the [dataset](####dataset) class which searches a folder for you and allows you to automatically create meta_data. Once a Dataset is created, you can retrieve the data easily:

```python
dset.get_data()
```

This returns a [Data](###Data) class. As a brief example of how to use the Dataset class, consider one the problems stated above of wanting to compare all data that corresponds to 10V as the first parameter and 1mv as the second parameter with the second parameter. This is done in a straightforward way using Dataset:

```python
import ekpmeasure.analysis as ekp

path1 = './data/folder1/'
path2 = './data/folder2/'

dset1 = ekp.dataset(path1) #dataset NOT Dataset
dset2 = ekp.dataset(path2)

dset = ekp.merge((dset1, dset2))
dset.query("param1 == '10V' and param3 == '1mv'").get_data()
```

#### dataset
Subclass of Dataset which does not require initializer argument. Searches a folder for a pickle file (.pkl) of name 'meta_data' and will assist in creating such a file if none exists. This can be done by

```python
dataset.generate_meta_data(mapper)
```
mapper is a function of a single filename that returns a dict of parameters . For example, in the example above mapper might return

```python
mapper('10V_100ns_1mv.csv' = {
	'param1':'10V', 
	'param2':'100ns', 
	'param3':'1mv',
	'filename':'10V_100ns_1mv.csv'
}
```

### Data
Subclass of Dict. The Data class holds real data. It allows for operations to be done on all data simultaneously by 

```python
some_data = dset.get_data(groupby='param1')
>>> 
{
	0:	{
		{'definition': 
			{'param1':
				{'10V'}
			 'param2':
				 {'100ns', '50ns', '10ns'}
			 'param3':
				 {'1mv', '2mv'}
			}
		{'data':
			{
				'real_data_column':numpy.vstack( the real data )
				...
			}
		}
	}
	...
}

def some_function(data_dict):
	"""a function which operates on a data_dict (from Data[0]['data']) and returns a dict which will replace the original data_dict"""
	return out

some_data.apply( some_function )
>>>
{
	0:	{
		{'definition': 
			{'param1':
				{'10V'}
			 'param2':
				 {'100ns', '50ns', '10ns'}
			 'param3':
				 {'1mv', '2mv'}
			}
		{'data':
			{
				'manipulated_data_col1':numpy.vstack( the manipulated data )
				...
			}
		}
	}
	...
}
```