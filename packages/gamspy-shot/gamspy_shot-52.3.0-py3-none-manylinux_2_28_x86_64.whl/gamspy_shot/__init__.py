import os
from pathlib import Path
from .version import __version__
directory = str(Path(__file__).resolve().parent)

files = ['libipopt.so', 'libmkl_gams.so', 'libgurobi.so', 'libiomp5.so', 'libshtcclib64.so']

file_paths = [directory + os.sep + file for file in files]
verbatim = 'SHOT 1001 5 00010203040506070809 1 0 2 MINLP MIQCP\ngmsgenus.run\ngmsgenux.out\nlibshtcclib64.so sht 1 1'
