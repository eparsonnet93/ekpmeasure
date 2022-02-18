#Si5580 Stepper motor drivers

__all__ = ('initialize', 'move_x_degrees')


def initialize(motor):
    """Intialize stepper motor driver.
    
    args:
        motor (pyvisa.instrument): Si5580 Step Motor Driver
    """
    motor.write('PM2')
    motor.write('VE.05')
    motor.write('AC10')
    return 

def convert_deg_to_step(deg):
    """Convert degrees to steps.
    
    args:
        deg (float or int): Degrees to convert
        
    returns:
        steps (int)
    """
    step = (40000)*deg/(360)
    return int(step)

def move_x_degrees(motor, deg):
    """Move some number of degrees.
    
    args:
        motor (pyvisa.instrument): Si5580 Step Motor Driver
        deg (float or int): Degrees to convert  
    """
    steps = convert_deg_to_step(deg)
    motor.write('DI{}'.format(steps))
    motor.write('FL')
    return 