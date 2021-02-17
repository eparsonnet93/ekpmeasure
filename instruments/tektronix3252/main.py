__all__ = ('start_pulse_gen', 'stop_pulse_gen', 'set_high_voltage_and_pulse_width', 'set_ch2_high_voltage_and_pulse_width')

def start_pulse_gen(pulse_gen, both = False):
    if both:
        pulse_gen.write('OUTPut1:STATe ON')
        pulse_gen.write('OUTPut2:STATe ON')
    else:
        pulse_gen.write('OUTPut1:STATe ON')
    return

def stop_pulse_gen(pulse_gen, both = False):
    if both:
        pulse_gen.write('OUTPut1:STATe OFF')
        pulse_gen.write('OUTPut2:STATe OFF')
    else:
        pulse_gen.write('OUTPut1:STATe OFF')
    return

def set_high_voltage_and_pulse_width(pulse_gen, high_v, pw):
    """pw and high_v should be strings like '1ms'"""
    stop_pulse_gen(pulse_gen)
    pulse_gen.write('SOURce1:PULSe:WIDTh {}'.format(pw))
    pulse_gen.write('SOURce1:VOLTage:LEVel:IMMediate:HIGH {}'.format(high_v))
    return

def set_ch2_high_voltage_and_pulse_width(pulse_gen, high_v, pw):
    """
    this will be inverted
    pw and high_v should be strings like '1ms'"""
    stop_pulse_gen(pulse_gen)
    pulse_gen.write('SOURce2:PULSe:WIDTh {}'.format(pw))
    pulse_gen.write('SOURce2:VOLTage:LEVel:IMMediate:LOW -{}'.format(high_v))
    return