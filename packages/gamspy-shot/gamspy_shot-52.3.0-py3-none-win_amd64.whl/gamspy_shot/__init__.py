import os
from pathlib import Path
from .version import __version__
directory = str(Path(__file__).resolve().parent)

files = ['ipopt.dll', 'mkl_gams.dll', 'gurobi130.dll', 'pthreads.dll', 'shtcclib64.dll']

file_paths = [directory + os.sep + file for file in files]
verbatim = 'SHOT 1001 5 00010203040506070809 1 0 2 MINLP MIQCP\ngmsgennt.cmd\ngmsgennx.exe\nshtcclib64.dll sht 1 1'
