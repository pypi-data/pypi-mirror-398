import os
from pathlib import Path
from .version import __version__
directory = str(Path(__file__).resolve().parent)

files = ['ipopt.dll', 'mkl_gams.dll', 'optipopt.def', 'ipocclib64.dll']

file_paths = [directory + os.sep + file for file in files]
verbatim = 'IPOPT 11 5 00010203040506070809 1 0 2 LP RMIP NLP CNS DNLP RMINLP QCP RMIQCP\ngmsgennt.cmd\ngmsgennx.exe\nipocclib64.dll ipo 1 1'
