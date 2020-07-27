#!/usr/bin/python3
from difflib import SequenceMatcher
import numpy as np
import itertools
import os
import sys

similarity = lambda x: np.mean([SequenceMatcher(None, a,b).ratio() for a,b in itertools.combinations(x, 2)])

os.chdir("/storage/music/temp")
os.
