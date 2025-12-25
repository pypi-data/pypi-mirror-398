import os
from pathlib import Path
from .version import __version__
directory = str(Path(__file__).resolve().parent)

files = ['libipopt.dylib', 'libiomp5.dylib', 'libmkl_gams.dylib', 'optipopt.def', 'libipocclib64.dylib']

file_paths = [directory + os.sep + file for file in files]
verbatim = 'IPOPT 11 5 00010203040506070809 1 0 2 LP RMIP NLP CNS DNLP RMINLP QCP RMIQCP\ngmsgenus.run\ngmsgenux.out\nlibipocclib64.dylib ipo 1 1'
