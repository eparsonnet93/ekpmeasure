import warnings
warnings.showwarning("ekpmeasure is deprecated. Please use ekpy instead.", DeprecationWarning, '', '')

import sys
sys.path.append('../')


from ekpy._version import __version__
import ekpy.analysis as analysis
import ekpy.control as control
import ekpy.experiments as experiments

__all__ = ('__version__', 'analysis', 'control', 'experiments')