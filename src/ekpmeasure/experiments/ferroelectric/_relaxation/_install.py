import os
from pathlib import Path

__all__ = ('install', )

def install(name='Relaxation.ipynb'):

	if name[-6] != '.ipynb':
		name += '.ipynb'

	lines = _copy()

	with open(os.path.join(os.getcwd(), name), 'wb') as f:
		f.writelines(lines)

	return

def _copy():
	_dir = Path(__file__).resolve().parent # get location of this file after wheel installation

	# get the most current version of App.ipynb and write to variable
	with open(os.path.join(_dir, '_notebook.ipynb'), 'rb') as f:
		lines = f.readlines()

	return lines