import time

__all__ = ('ramp_powersupply_to_current',)

def ramp_powersupply_to_current(magnet_power_supply, final_current, ramp_rate):
    """ramp power supply to specified current"""
    if ramp_rate > .5: #to ensure we don't ramp too quickly
        raise ValueError('ramp_rate must be <= .5')
    
    ramp_stat = magnet_power_supply.query('ramp?').split('\r')[0]
    ramp_segment, init_ramp_cur, fin_ramp_cur, ramp_rate, e1, e2 = ramp_stat.split(',')

    #check to make sure it is holding:
    if magnet_power_supply.query('rmp?').split('\r')[0] != '0':
        raise ValueError('power supply is not holding')

    #set up new ramp state:
    new_ramp_stat = '{},{},{},{},{},{}'.format(ramp_segment, init_ramp_cur, final_current,ramp_rate,'00','00:00:00:00')
        
    magnet_power_supply.write(new_ramp_stat)
    time.sleep(.1) #let the powersupply respond
    magnet_power_supply.write('rmp 1')
    time.sleep(.1)
    
    ramping_state = int(magnet_power_supply.query('rmp?').split('\r')[0])
    while ramping_state != 0:
        time.sleep(.5)
        ramping_state = int(magnet_power_supply.query('rmp?').split('\r')[0])
    
    return
