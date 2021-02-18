import pandas as pd
import numpy as np

__all__ = ('load_radiant_loop_from_text_file',)

def load_radiant_loop_from_text_file(file, measured_value = 'Charge', return_meta_data = True):
    """load a radiant loop from a text file
    
    Returns: (pandas DataFrame) columns -> 'Time(ms)', 'DriveVoltage', 'MeasuredCharge(pC)' or 'Time(ms)', 'DriveVoltage', 'MeasuredPolarization(uC/c,2)'
    ----
    
    path: str
    return_meta_data: bool - True returns ((pandas dataframe) data, (dict) meta_data)  
        meta_data (dict) -> {SampleName:(str)... etc}
    measured_value: (str) either 'Charge' or 'Polarization' - typically one would use charge unless you have accurately measured capacitor area and input correctly into the radiant ui
    
    """
    
    if measured_value.lower() not in set({'charge', 'polarization'}):
        raise ValueError('measured_value {} not supported. must be either charge or polarization'.format(measured_value))
        
        
    with open(file, 'rb') as f:
        lines = f.readlines()

    newlines = []

    for i, line in enumerate(lines):
        #radiant's file structure is the worst
        newlines.append(str(line.decode('windows-1252').replace('»', '').replace('«', '').replace(' ', '').replace('\r', '').replace('\n', '').replace('µ', 'u')))

    lines = newlines

    meta_data = dict()
    data = []
    for line in lines:
        spl = line.split(':,')
        if len(spl)>1: #often there is a comma before the actual data. why? who knows! this is the case where there exists such a comma
            meta_data.update({spl[0]:spl[1]})
            continue
        #now try the case with no comma:
        spl = line.split(':')
        if len(spl)>1: 
            meta_data.update({spl[0]:spl[1]})
            continue
        else:
            data.append(line)

    out = dict()
    i = 0 #counter for when we have established column names

    pointer_dict = dict() #holds which column index points to which column name
    for row in data:
        spl = row.split(',')
        if len(spl)<=1: #there are some rows in here which are not data and they are therefor not comma sep
            continue

        if i == 0: #establish column names
            out.update({spl[a]:[] for a in range(len(spl))})
            pointer_dict.update({a:spl[a] for a in range(len(spl))})
            i+=1
            continue
        for ijk, a in enumerate(spl):
            out[pointer_dict[ijk]].append(float(a))

    out = pd.DataFrame(out)
    out.drop(columns = ['Point'], inplace = True)
    
    if measured_value.lower() == 'charge':
        out['MeasuredPolarization'] = out['MeasuredPolarization']*float(meta_data['SampleArea(cm2)'])*1e6 #to convert from uC to pC
        out.rename(columns = {'MeasuredPolarization':'MeasuredCharge(pC)'}, inplace = True)
    elif measured_value.lower() == 'polarization':
        out.rename(columns = {'MeasuredPolarization':'MeasuredPolarization(uC/cm2)'}, inplace = True)
        
    if return_meta_data:
        return out, meta_data
        
    return out