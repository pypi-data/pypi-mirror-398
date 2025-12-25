import os
from pathlib import Path
from .version import __version__
directory = str(Path(__file__).resolve().parent)

import shutil
import gamspy_arm_perf
for file in gamspy_arm_perf.files:
	if not os.path.exists(os.path.join(directory, file)):
		shutil.copy(os.path.join(gamspy_arm_perf.directory, file), os.path.join(directory, file))
files = ['libipopt.so', 'libarmpl_gams.so', 'libgurobi.so', 'libshtcclib64.so']

file_paths = [directory + os.sep + file for file in files]
verbatim = 'SHOT 1001 5 00010203040506070809 1 0 2 MINLP MIQCP\ngmsgenus.run\ngmsgenux.out\nlibshtcclib64.so sht 1 1'
