import os
from pathlib import Path
from .version import __version__
directory = str(Path(__file__).resolve().parent)

files = ['libxprl.so.x9.8', 'libxprs.so.46', 'libscip.so', 'libipopt.so', 'libtbb.so.12', 'libgurobi.so', 'libmkl_gams.so', 'libmosek64.so.11.0', 'libiomp5.so', 'libscpcclib64.so']

file_paths = [directory + os.sep + file for file in files]
verbatim = 'SCIP 2001 5 SC 1 0 2 MIP NLP CNS DNLP RMINLP MINLP QCP MIQCP RMIQCP\ngmsgenus.run\ngmsgenux.out\nlibscpcclib64.so scp 1 1'
