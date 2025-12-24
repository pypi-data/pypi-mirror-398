"""
Discrete Fourier - Discrete Fourier functions
=============================================

Author: Ricardo Marcelo Alvarez
Date: 2025-12-19
"""

from os.path import dirname, basename, isfile, join
import glob
import sys
import importlib.metadata

from discrete_fourier.discrete_fourier import *

discrete_fourier = importlib.metadata.metadata('discrete_fourier')

__title__ = discrete_fourier['Name']
__summary__ = discrete_fourier['Summary']
__uri__ = discrete_fourier['Home-page']
__version__ = discrete_fourier['Version']
__author__ = discrete_fourier['Author']
__email__ = discrete_fourier['Author-email']
# __license__ = discrete_fourier['License']
__copyright__ = 'Copyright © 2025 Ricardo Marcelo Alvarez'

modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = []

if isinstance(sys.path,list):
    sys.path.append(dirname(__file__))

for f in modules:
    if isfile(f) and not f.endswith('__init__.py'):
        __all__.append(basename(f)[:-3])
