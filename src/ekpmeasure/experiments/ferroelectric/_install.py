import os

__all__ = ('install', )

def install( _dir, name='App.ipynb',):

	if name[-6:] != '.ipynb':
		name += '.ipynb'

	print('Creating {}'.format(name))

	lines = _copy(_dir=_dir)

	with open(os.path.join(os.getcwd(), name), 'wb') as f:
		f.writelines(lines)

	return

def _copy(_dir):
	# get the most current version of App.ipynb and write to variable
	with open(os.path.join(_dir, '_notebook.ipynb'), 'rb') as f:
		lines = f.readlines()

	return lines