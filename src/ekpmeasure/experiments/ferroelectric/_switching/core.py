from ....control import core
from ....control.instruments.berkeleynucleonics765 import stop
from ..switching import preset_run_function
import pandas as pd
import numpy as np
import os 

import warnings 

import time

__all__ = ('FE',)


class FE(core.experiment):
	"""Experiment class for running pulsed Ferroelectric switching experiments like those shown `here <https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.125.067601>`_ 

	args:
		pg (pyvisa.resources.gpib.GPIBInstrument): Berkeley Nucleonics 765
		scope (pyvisa.resources.gpib.GPIBInstrument): Tektronix TDS620B or Tektronix TDS6604
		scopetype (str): Specify scope. Only Tektronix TDS620B (``'620B'``) or Tektronix TDS6604 (``'6604'``) are supported
		run_function (function): Run function.

	returns:
		(FE): Experiment

	"""

	def __init__(self, pg, scope, scopetype = '6604',run_function = preset_run_function):
		super().__init__()
		if scopetype != '6604' and scopetype != '620B':
			raise ValueError('must specify scope type as either 6604 or 620B (corresponding to the correct scope you are using)')

		self.run_function = preset_run_function
		self.pg = pg
		self.scope = scope
		self.scopetype = scopetype
		return

	def checks(self, params):
		"""Checks during initialization."""
		if self.pg != params['pg']:
			try:
				raise ValueError('pg provided in initialization ({}) does not match that provided as an argument for run_function ({})'.format(self.pg, params['pg']))

			except KeyError:
				raise ValueError('pg provided in initialization ({}) does not match that provided as an argument for run_function ({})'.format(self.pg, None))

		
		if self.scope != params['scope']:
			try:
				raise ValueError('scope provided in initialization ({}) does not match that provided as an argument for run_function ({})'.format(self.scope, params['scope']))

			except KeyError:
				raise ValueError('scope provided in initialization ({}) does not match that provided as an argument for run_function ({})'.format(self.scope, None))
		try:
			if self.scopetype != params['scopetype']:
				try:
					raise ValueError('scopetype provided in initialization ({}) does not match that provided as an argument for run_function ({})'.format(self.scopetype, params['scopetype']))

				except KeyError:
					raise ValueError('scopetype provided in initialization ({}) does not match that provided as an argument for run_function ({})'.format(self.scopetype, None))
		except KeyError:
			if self.scopetype != '6604':
				raise ValueError('check scopetype. If you think this is done correctly, please specify explicitly scopetype in params.')
		
	def terminate(self):
		"""Termination."""
		stop(self.pg)
		return
