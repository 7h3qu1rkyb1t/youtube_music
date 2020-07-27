#!/usr/bin/python3
import os
os.chdir("/storage/music/temp")
bad_words = ["(Official Video)","(Official Audio)","(Official Music Video)", "[OFFICIAL VIDEO]","(Lyrics)","Lyric Video","[Official Lyric Video]", "[Official Music Video]"]
for i in os.listdir():
    for j in bad_words:
        if j in i:
            os.rename(i,i.replace(j,""))
            break
print("done renaming")
