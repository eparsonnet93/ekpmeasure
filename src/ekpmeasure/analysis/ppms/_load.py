import pandas as pd
import numpy as np

__all__ = ('mapper',)


def mapper(fname, path):
    """
    Common name mapper for ppms data.

    args:
        fname (str): Filename.
        path (str): Path to file.
    """
    file = path + fname
    with open(file, 'rb') as f:
        lines = f.readlines()

    heading_index = np.nan

    for i, line in enumerate(lines):
        if line.decode("utf-8") == '\r\n':
            heading_index = i
    
    if np.isnan(heading_index):
        raise ValueError('unable to find heading!!!')

    meta_data = {'filename':fname}
    for line in lines[:heading_index]:
        line_string = line.decode("utf-8")
        if '###' in line_string: #case for settings break in header
            continue
        spl = line_string.replace('\n', '').replace('\r', '').replace('\t', '').split(': ')
        try:
            meta_data.update({spl[0]:float(spl[1])})
        except ValueError:
            meta_data.update({spl[0]:spl[1]})
        except IndexError:
            meta_data.update({spl[0]:np.nan})
            
    ### get field ###
    tdf = pd.read_csv(file, skiprows=heading_index, delimiter = '\t')
    field_value = np.round(np.mean(np.round(tdf['Field digital (T)'], 2)), 2)
    meta_data.update({'Field':field_value})
    
    temp = np.round(np.mean(np.round(tdf['T Sample (K)'], 0)), 0)
    meta_data.update({'Temperature Average':temp})
    
    return meta_data