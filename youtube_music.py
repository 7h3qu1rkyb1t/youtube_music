#!/usr/bin/python3
from __future__ import unicode_literals
import youtube_dl
import os
from sys import argv
from threading import Thread


import pyperclip
import time



#Download data and config
def download(link):
    download_option = {
            'format':'bestaudio/best',
            'outtmpl':'%(title)s.%(ext)s',
            'nocheckcertificate': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
                }]
            }

#Download songs

    with youtube_dl.YoutubeDL(download_option) as dl:
        dl.download([link])
    print("\n\n Download done waiting...\n\n")

os.chdir("/media/gireesh/common_disk/music/temp")
os.system('mitmdump -v -p 9009 | stdbuf -o 0 grep -i -A 8 "POST https://www.youtube.com/service_ajax?name=likeEndpoint" |stdbuf -o 0 grep referer >urls &')     #starting mitmdump proxy server

while True:
    fr=open("urls","r")
    fw = open("urls","w")
    while True:
        fw.flush()          #refreshin test file
        f=fr.read()         #reading every new line
        if f:
            clip=f.strip()[9:]      #extracting link

            var=True
        #os.system("youtube-dl -x --audio-format mp3 "+clip) #Download using youtube-dl executable

            while var:
                try:                                  
                    print("\n\nDownload started....\n\n")
                    t=Thread(target=download, args=(clip,))
                    t.start()
                except:
                    time.sleep(1)       #if failed then retry
                    continue
                var=False
        

        time.sleep(2)



