import os
from pathlib import Path
from .version import __version__
directory = str(Path(__file__).resolve().parent)

import shutil
import gamspy_arm_perf
import gamspy_gurobi
for file in gamspy_arm_perf.files:
	if not os.path.exists(os.path.join(directory, file)):
		shutil.copy(os.path.join(gamspy_arm_perf.directory, file), os.path.join(directory, file))
for file in gamspy_gurobi.files:
	if not os.path.exists(os.path.join(directory, file)):
		shutil.copy(os.path.join(gamspy_gurobi.directory, file), os.path.join(directory, file))
files = ['libxprl.so.x9.8', 'libxprs.so.46', 'libscip.so', 'libipopt.so', 'libtbb_debug.so.12', 'libgurobi.so', 'libarmpl_gams.so', 'libmosek64.so.11.0', 'libscpcclib64.so']

file_paths = [directory + os.sep + file for file in files]
verbatim = 'SCIP 2001 5 SC 1 0 2 MIP NLP CNS DNLP RMINLP MINLP QCP MIQCP RMIQCP\ngmsgenus.run\ngmsgenux.out\nlibscpcclib64.so scp 1 1'
