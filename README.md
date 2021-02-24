# ekpmeasure
Repository of computer control code for various experiments as well as some analysis code for importing data from various tools into python


## Example usage of FE_switching analysis:
---
```python
from ekpmeasure.analysis.FE_switching import dataset, grouped_dataset
import matplotlib.pyplot as plt

path = './test/'
dset = dataset(path)
dset.query("high_voltage_v == .5")
```

![alt text](./src/dataset.PNG?raw=true)

```python
meta_data = dset.query("high_voltage_v == .5 and delay_ns < 25").meta_data
data = grouped_dataset(path, meta_data = meta_data)
data
```

```python
desired_index = 0
samples = data.get_data_for_group_index([desired_index])
samples[desired_index]
```

```python
mean_samples = samples.mean()
for key in mean_samples:
    internal_dict = mean_samples[key]
    plt.plot(internal_dict['time'], internal_dict['p1'])
```

---

### To-do 2/23/21
- add ferroelectric switching experimental analysis + operational control for tds6604 (higher speed scope)
- add requirements.txt 
- add install instructions  
