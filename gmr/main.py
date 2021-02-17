import pandas as pd
import numpy as np


from ..instruments.lakeshore647 import ramp_powersupply_to_current
from ..instruments.lakeshore475 import measure_field
from ..instruments.srs830 import get_lockin_r_theta

__all__ = ('measure_field_and_lockin', 'gmr', 'cyclic_gmr')

def measure_field_and_lockin(gaussmeter, lockin, navg=10):
    """returns dict and std of field and resistance at the time called"""
    fields, rs, thetas = [], [], []
    
    for i in range(navg):
        field = measure_field(gaussmeter)
        r, theta = get_lockin_r_theta(lockin)
        time.sleep(.2)
        fields.append(field)
        rs.append(r)
        thetas.append(theta)
    
    
    return dict({'H_mean':np.mean(fields), 'H_std': np.std(fields), 'R_mean':np.mean(rs), 'R_std': np.std(rs), 'Theta_mean':np.mean(rs), 'Theta_std':np.std(thetas)})

def gmr(path, start_current, end_current, steps=100, ramp_rate=.05, avg=5, save = True):
    #go to start
    ramp_powersupply_to_current(magnet_power_supply, start_current, .3)
    
    #initialize return
    out = pd.DataFrame({'H_mean':np.zeros(steps), 
                        'H_std':np.zeros(steps),
                        'R_mean':np.zeros(steps), 
                        'R_std':np.zeros(steps), 
                        'Theta_mean':np.zeros(steps), 
                        'Theta_std':np.zeros(steps)
                       })
    
    currents = np.linspace(start_current, end_current, steps)
    for i, current in enumerate(currents):
        ramp_powersupply_to_current(magnet_power_supply, current, ramp_rate) #go to new current
        measurement = measure_field_and_lockin(gaussmeter, lockin, navg=avg)
        out.at[i, 'H_mean'] = measurement['H_mean']
        out.at[i, 'H_std'] = measurement['H_std']
        out.at[i, 'R_mean'] = measurement['R_mean']
        out.at[i, 'R_std'] = measurement['R_std']
        out.at[i, 'Theta_mean'] = measurement['Theta_mean']
        out.at[i, 'Theta_std'] = measurement['Theta_std']
       
    if save:
        name = None
        try: 
            existing_fnames = os.listdir(path)
            existing_fnames = list(set(existing_fnames) - set(['.ipynb_checkpoints']))
            try:
                fnames = [float(name[:-3]) for name in existing_fnames]
            except ValueError:
                name = input('non-numeric names exist in the folder you are saving to, input a file name:')
            try:
                highest = max(fnames)
            except ValueError:
                highest = 0
                
            if name == None:
                new = str(int(highest+1))
                while len(new)<4:
                    new='0'+new
                name = new

            out.to_csv(path + name + '.csv')
            print('saving file. name:{}, path: {}'.format(new+'.csv', path))
        except:
            print("error saving file, check path name")

        finally:
            out.plot(x = 'H_mean', y = 'R_mean')
            return out
    else:
        #out.plot(x = 'H_mean', y = 'R_mean')
        return out
    
def cyclic_gmr(path, low_current, high_current, steps=100, ramp_rate=.05, avg=5, ramp_up_first = True, save = True):
    if ramp_up_first:
        start_current = low_current
        end_current = high_current
    else:
        start_current = high_current
        end_current = low_current
    
    first_data = gmr(path, start_current, end_current, steps=steps, ramp_rate=ramp_rate, avg=avg, save = False)
    second_data = gmr(path, end_current, start_current, steps=steps, ramp_rate=ramp_rate, avg=avg, save = False)
    out = pd.concat((first_data, second_data))
    
    if save:
        name = None
        try: 
            existing_fnames = os.listdir(path)
            existing_fnames = list(set(existing_fnames) - set(['.ipynb_checkpoints']))
            try:
                fnames = [float(name[:-3]) for name in existing_fnames]
            except ValueError:
                name = input('non-numeric names exist in the folder you are saving to, input a file name:')
            try:
                highest = max(fnames)
            except ValueError:
                highest = 0
                
            if name == None:
                new = str(int(highest+1))
                while len(new)<4:
                    new='0'+new
                name = new

            out.to_csv(path + name + '.csv')
            print('saving file. name:{}, path: {}'.format(new+'.csv', path))
        except:
            print("error saving file, check path name")

        finally:
            out.plot(x = 'H_mean', y = 'R_mean')
            return out
    else:
        #out.plot(x = 'H_mean', y = 'R_mean')
        return out