#!/usr/bin/python3
from difflib import SequenceMatcher
import numpy as np
import itertools
import os
import sys

similarity = lambda x: np.mean([SequenceMatcher(None, a,b).ratio() for a,b in itertools.combinations(x, 2)])

os.chdir("/media/gireesh/common_disk/music/temp/")

def match_find(max_match):
    l = os.listdir()
    stop_search = False
    removing_lst = []
    for _ in range(len(l)):
        i = l.pop()
        for j in l:
            if max_match < similarity([i,j]):
                if not stop_search:
                    print(f"{i}\n{j}\t{max_match}")
                    if input("do you wanna go above? [[Y]/n]\n") == "n":
                        stop_search = True
                        removing_lst.append((j,i))
                    else:
                        max_match= similarity([i,j])
                else:
                    removing_lst.append((j,i))

        else:
            continue
        break
    return removing_lst
if input("Do have value for aprox? [y/N]") =="y":
    max_match = float(input("enter the max_match value: "))
else:
    max_match = 0.5
lst = match_find(max_match)
print("removing following files\n file   :   match")
for i,j in lst:
    print(f"{j}  \n {i}\n")
if input(" Confirm remove? [y/[N]]") =="y":
    for i,j in lst:
        try:
            os.remove(i)
        except FileNotFoundError:
            continue
print("done")
sys.exit(0)
