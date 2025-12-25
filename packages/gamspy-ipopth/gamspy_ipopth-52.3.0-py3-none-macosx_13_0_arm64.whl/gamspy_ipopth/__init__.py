import os
from pathlib import Path
from .version import __version__
directory = str(Path(__file__).resolve().parent)

files = ['libipopt.dylib', 'optipopt.def', 'libipocclib64.dylib']

file_paths = [directory + os.sep + file for file in files]
verbatim = 'IPOPTH 11 5 IP 1 0 2 LP RMIP NLP CNS DNLP RMINLP QCP RMIQCP\ngmsgenus.run optipopt.def\ngmsgenux.out\nlibipocclib64.dylib ipo 1 1'
