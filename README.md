# Welcome to EKPy 


[![Documentation Status](https://readthedocs.org/projects/ekpmeasure/badge/?version=latest)](http://ekpmeasure.readthedocs.io/?badge=latest)
[![PyPI version fury.io](https://badge.fury.io/py/ekpy.svg)](https://pypi.org/project/ekpy/)
[![PyPI license](https://img.shields.io/pypi/l/ekpy.svg)](https://pypi.org/project/ekpy/)
[![PyPi Downloads](http://pepy.tech/badge/ekpmeasure)](http://pepy.tech/project/ekpmeasure)
[![PyPi Downloads](http://pepy.tech/badge/ekpy)](http://pepy.tech/project/ekpy)

[![N|Scheme](https://github.com/eparsonnet93/ekpmeasure/blob/main/imgs/prl2.png)](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.125.067601)

A repository of analysis and computer control code for various experiments. Image above is an example of data **collected** and **analyzed** using this package.

- [Overview](#overview)
- [Installation](#installation)
- [Development](#development)
- [Important Links](#important-links)
- [Change Log](#change-log)
- [Support](#support)
- [Cite this code](#citation)
- [Cited by](#cited-by)

# Overview

EKPy (formerly ekpmeasure) is a set of control and analysis code designed to help streamline experiments. The basic idea is that in experimental work we often take data from many different sources, store it in different places, have varying degrees meta data associated with the data (even for a single type of data) and somehow(!) we are supposed to make sense of it all. We like to compare across trials, days, experimental conditions, etc. and it is very difficult to keep track of what data is where, and quickly access it when we need it. Often I find that folks end up copying and pasting raw data between excel spreadsheets and if you're not careful you will quickly lose track of which data came from where. This package's goal is to make this all easier. 

You may not find the experimental control code as helpful as it is relatively specific to my research in condensed matter physics (though electrical engineers or similar may find it very useful) but the analysis code is for everyone. 

At the heart of the analysis is the [Dataset](https://ekpmeasure.readthedocs.io/en/latest/ekpmeasure.analysis.html#ekpmeasure.analysis.core.Dataset) class which is a means of manipulating *meta data alone* in order to locate which actual data you want to analyze. [Datasets](https://ekpmeasure.readthedocs.io/en/latest/ekpmeasure.analysis.html#ekpmeasure.analysis.core.Dataset) don't care about what the real data looks like, and they keep track of where different data is stored so it is easy to select which data you want to look at - only then do you retrieve the data. The real data is returned in a [Data](https://ekpmeasure.readthedocs.io/en/latest/ekpmeasure.analysis.html#ekpmeasure.analysis.core.Data) class which allows you to group by parameters, perform calculations and much more.  

I am always improving this repository and if you have suggestions, I appreciate any feedback and or issues (<https://github.com/eparsonnet93/ekpmeasure/issues>)

See [examples](https://github.com/eparsonnet93/ekpmeasure/tree/main/examples) for more. 



---
# Installation:

If you plan to use EKPy to control your experiments. You will need to install [NI-VISA](https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html#442805) first. 

Find the latest build [here](https://pypi.org/project/ekpy/).

```bash
pip install ekpy
```

or to upgrade to the latest version

```bash
pip install -U ekpy
```

You can also access `.whl` or `.tar.gz` files in the `dist/` directory directly for installation. 

For installation issues, please see [Issue Tracker](https://github.com/eparsonnet93/ekpmeasure/issues)

There are also specific [experiments](https://github.com/eparsonnet93/ekpmeasure/tree/main/src/ekpmeasure/experiments) that can be installed following installation of `ekpy`. Please see the accompanying readme (*e.g.*, [here](https://github.com/eparsonnet93/ekpmeasure/blob/main/src/ekpmeasure/experiments/ferroelectric/_fastPUND/README.md)) for such cases. 

---
# Development

We welcome new contributors of all experience levels. Please reach out directly (e.parsonnet@berkeley.edu) to inqure about getting involved. 

## Important Links

* Official source code repo: https://github.com/eparsonnet93/ekpmeasure
* Issue tracker: https://github.com/eparsonnet93/ekpmeasure/issues

# Change log

### Version 0.1.13

- Can now group Data. `data.groupby`
- Can now remove nans from data. `data.dropna`
- Improvements to file management in control, saving, and more appropriate trial incrementing in `control.experiment`4
- Functions used in `data.apply` should no longer require the use of iterable data arrays. Please raise an issue if one occurs.

### Version 0.1.12

- Added functionality to `analysis.radiant`
- Speed increase for `data.get_data()`
- Minor bugs and other fixes

### Version 0.1.11

- `experiment.print_run_function_args` is gone. It has been replaced with `experiment.show_run_function_help`
- Added a header of meta data to the default save function for `control.experiment` and started the process of doing away with meta_data `.pkl` files in favor of `.csv` (why did I ever think that was a good idea?)

#### Version 0.1.10

- minor bug fixes and documentation updates

#### Version 0.1.9

- minor bug fixes

#### Version 0.1.8

**2/18/22**
- bug fixes from 0.1.7 and changed install name to `ekpy`. 

#### Version 0.1.6

**1/23/22**
- added `Data.to_DataFrame()` which allows one to convert `Data` to `pandas.DataFrame`. Each index of `Data` will be a single row in the resulting DataFrame. 


#### Version 0.1.5

**1/12/22**
- `merge_Datas` was replaced. The older version is now `concat_Datas` as it was really just concatenation, not merging. Merging now has real meaning, to merge a set of similar data objects on a specified definition key. Please report errors as they arise.

- similary `merge_Datasets` is deprecated. One must use `concat_Datasets`. 


#### Version 0.1.4

**12/2/21**
- Added experiments module with `ferroelectric` experiments. This contains both relaxation (`_relaxation`) and switching (`_switching`) experiments. These consist of self contained jupyter notebooks that can be installed by `python -m ekpy.experiments.ferroelectric.<experiment_name>`. For more see the experiment specific README for [relaxation](https://github.com/eparsonnet93/ekpmeasure/tree/main/src/ekpmeasure/experiments/ferroelectric/_relaxation) or [switching](https://github.com/eparsonnet93/ekpmeasure/tree/main/src/ekpmeasure/experiments/ferroelectric/_switching)
- Bug fix on `Data.sort`

**11/16/21**
- `Data.apply` now allows for dropping data. This can be executed by having the function in `.apply` return `'None'`.
- `data_array_builder.build` now allows one to fix lengths on 1D data by appending nans to make all data arrays the same length.
- `analysis.plotting.add_legend_element` now allows kwarg fontsize

**11/19/21**
- `Data` can now be saved. Use `data.to_ekpdat`.
	- Can be loaded as `analysis.read_ekpdat`

#### Version 0.1.3

**11/11/21**
- Minor fixes for deprecations in `control.misc`

#### Version 0.1.2

**11/7/21**
- Speed improvements to `Dataset.remove_nonexistent_files`
- `Data` objects can now be sorted by a definition parameter

#### Version 0.1.1

**11/2/21**

- Updates to plotting during experimental control. Now one can simply override the `control.experiment` method `_plot` to define how plotting will take place. Here is a brief example of such an override:
```python
from ekpy.control import plotting
from ekpy.control import experiment
import matplotlib.pyplot as plt

class exp(experiment):

	...

	def _plot(self, data, scan_params):
		if hasattr(self, 'fig') and hasattr(self, 'ax'):
			pass
		else:
			fig, ax = plt.subplots()
			self.fig = fig
			self.ax = ax
			
		self.ax.scatter(scan_params['frequency'], np.mean(data['R']), color = 'blue')
		plt.show(self.fig)
		plotting.update_plot(self.fig)

	...
```

#### Version 0.1.0

**10/24/21**

- Dataset class is no longer subclass of `pandas.DataFrame`. This is to limit usage of unsupported functions. 
- Data class updates including sorting and collapsing. 
- One can access data or definition directly as an attribute now `Data.definition`, for example. One can also access pieces of information such as the real data corresponding to `p1` as `Data.p1` or definition keys, *e.g.* `high_voltage` as `Data.high_voltage`
- Experiment class now saves a backup `.csv` meta data file in addition to the pickle file in order to help with errors related to different pandas versions on various machines. 

# Support 

Code related issues (e.g. bugs, feature requests) can be created in the
[issue tracker](https://github.com/eparsonnet93/ekpmeasure/issues)

Maintainer: Eric Parsonnet

# Citation 

Please cite this work following the [CITATION.cff](https://github.com/eparsonnet93/ekpmeasure/blob/main/CITATION.cff) (see [here](https://academia.stackexchange.com/questions/14010/how-do-you-cite-a-github-repository) for more details on how to cite.)

# Cited By

1. E. Parsonnet, L. Caretta, V. Nagarajan, H. Zhang, H. Taghinejad, P. Behera, X. Huang, P. Kavle, A. Fernandez, D. Nikonov, H. Li, I. Young, J. Analytis, and R. Ramesh, *Non-Volatile Electric Field Control of Thermal Magnons in the Absence of an Applied Magnetic Field*, Arxiv (2022).