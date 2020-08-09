#!/usr/bin/python3
from __future__ import unicode_literals
import youtube_dl
import os
import sys
import json
from apiclient.discovery import build
from datetime import timedelta
from colored import fg, attr
import socket
import argparse
from tagger import Tag
import terminal as Term


close = False
final_filename =""
files_downloaded = []


def write_subs_list(subs):
    if(files_downloaded):
        print(Term.clearscreen(),end = "")
        print("Downloaded files:")
        for num, f in enumerate(files_downloaded):
            print(f"{count}. {f}.mp3")
    with open("/home/gireesh/.config/.youtube.config/subscription_list", "w") as f:
        f.write(json.dumps(subs))


# download  based on likes and dislike rate
def check_stats(yt_id, vd_id):
    vd_details = yt_id.videos().list(id=vd_id, part='statistics').execute()
    likes = int(vd_details['items'][0]['statistics']['likeCount'])
    dislikes = int(vd_details['items'][0]['statistics']['dislikeCount'])
    return True if likes*5/100 > dislikes else False


def check_time(time):
    # check for video length, so that to differentiate between songs and videos
    max_time = timedelta(minutes=6)
    min_time = timedelta(minutes=2, seconds=10)
    hours = 0
    minutes = 0
    seconds = 0
    time = time.lstrip("PT")
    if "H" in time:
        hours = int(time[:time.index("H")])
        time = time[time.index("H")+1:]
    if "M" in time:
        minutes = int(time[:time.index("M")])
        time = time[time.index("M")+1:]
    if "S" in time:
        seconds = int(time[:time.index("S")])
    delta_time = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    return delta_time < max_time and delta_time > min_time


def progress_show(opts):
    if opts["status"] == "downloading":
        total_bytes = int(opts["total_bytes"])
        downloaded_bytes = int(opts["downloaded_bytes"])
        download_progress = downloaded_bytes / total_bytes 
        pBarLen = 50
        pDone = "#" * int(download_progress * pBarLen)
        pLeft = "-" * (pBarLen - len(pDone))
        print(f'{Term.clearline()}{opts["tmpfilename"]}{Term.setCursorLine(40)}{int(opts["elapsed"])}/{int( opts["eta"])}ETA\t[{pDone}{pLeft}]\t{int(download_progress*100)}%',end="\r")
        global final_filename 
        final_filename = opts["filename"][:opts["filename"].rfind(".")] + ".mp3"
    elif opts["status"] == "finished":
        print("")

def download(link):
    download_option = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'nocheckcertificate': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
                }],
            'quiet': True,
            'progress_hooks': [progress_show]
            }
    # Download songs
    with youtube_dl.YoutubeDL(download_option) as dl:
        try:
            dl.download([link])
        except:
            with open("/home/gireesh/.config/.youtube.config/errored_links", "a") as f:
                f.write(link+"\n")


def download_channel(yt, channel_id, last_song, channel_num, total_channels):
    """ downloads all pending songs from a channel """
    global close
    channel = yt.channels().list(id=channel_id, part="contentDetails").execute()
    playlist = channel["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    download_list = []
    token = None                # page token
    page_end = False                  # last song check variable
    page = 0
    print(f" Getting musics list:", end="")
    while not page_end:
        lst = yt.playlistItems().list(playlistId=playlist, maxResults=10, pageToken=token, part="snippet").execute()
        for i in lst["items"]:
            Id = i["snippet"]["resourceId"]["videoId"]
            if last_song != Id:
                vd_detail = yt.videos().list(id=Id, part="contentDetails").execute()
                vd_time = vd_detail["items"][0]["contentDetails"]["duration"]
                # check if the video is song by guessing from the length
                if check_time(vd_time) and check_stats(yt, Id):
                    download_list.append(Id)
            else:
                page_end = True
                break
        token = lst.get("nextPageToken")
        if not token:
            break
        page += 1
    download_list.reverse()
    print("",end="\r")
    print("\n\n", end="")                   # two lines are needed to display information and are cleared later
    for count, song_link in enumerate(download_list):
        try:
            print(Term.mvCursorVerticle(2)+"\r", end=Term.clearEverythingAfter())
            print(f"%s\tDownloading {count+1} out of {len(download_list)} %s" % (fg(40), attr(0)))
            download(song_link)
            files_downloaded.append(Tag(final_filename))
        except KeyboardInterrupt:
            close = True
            return last_song
        except youtube_dl.utils.DownloadError:
            print("download error skipping this one")
            close = True
            return last_song
        except Exception as unkown_e:
            close = True
            print(unkown_e)
            return last_song
        last_song = i
    return last_song


def run_check():
    ''' check the required files  '''
    try:
        with open("/home/gireesh/.config/.youtube.config/subscription_list") as f:
            txt = f.read()
    except FileNotFoundError:
        print("Error: subscription list doesn't exist")
        if "n" == input("do you want me to create skeleton? [y]/n"):
            sys.exit(1)
        with open("/home/gireesh/.config/.youtube.config/subscription_list", "w") as f:
            f.write("")
    return txt

def youtube_auth():
    '''gets authentication keys from youtube'''
    api_key = os.environ.get("youtube_api")
    if api_key:
        return build("youtube", "v3", developerKey=api_key)
    else:
        print("Error: Couldn't get the api_keys!!!")
        sys.exit(1)


def add_subscription(yt, channel_id):
    """ adds channel_id to subscription_list """
    channel_id = channel_id.lstrip("https://").lstrip("www.").lstrip("youtube.com/channel/")
    channel = yt.channels().list(id=channel_id, part="contentDetails").execute()
    playlist = channel['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    lst = yt.playlistItems().list(playlistId=playlist, maxResults=10, pageToken=None, part="snippet").execute()
    last_song = lst['items'][0]['snippet']['resourceId']['videoId']
    
    title = yt.channels().list(id=channel_id, part="snippet").execute()['items'][0]['snippet']['title']
    print(f"Adding channel \"{title}\"")

    with open("/home/gireesh/.config/.youtube.config/subscription_list", "r") as f:
        subs = f.read()
    subs = json.loads(subs)
    subs[channel_id] = last_song
    with open("/home/gireesh/.config/.youtube.config/subscription_list", "w") as f:
        f.write(json.dumps(subs))


def main():
    txt = run_check()
    subs = json.loads(txt)
    global yt
    os.chdir("/storage/music/temp")
    channel_num = 1
    total_channels = len(subs)
    for i, j in subs.items():
        print(f"{Term.clearscreen()}%s{channel_num} out of {total_channels} %s" % (fg(11), attr(0)))
        while True:
            try:
                subs[i] = download_channel(yt, i, j, channel_num, total_channels)
            except socket.timeout:
                if input("socket time out!! Do you wanna continue? [y/N]") == "y":
                    continue
                print("socket timeout breaking")
                break
            else:
                break

        if close:
            print("breaked out")
            break
        channel_num += 1

    write_subs_list(subs)


if __name__ == "__main__":
    yt = youtube_auth()
    parser = argparse.ArgumentParser(description="Downloads songs from youtube based on channels")
    parser.add_argument('-d','--download',action='store_true', help='downloads songs from the youtube based on subscription list')
    parser.add_argument('-a','--add-channel', metavar='channel url', nargs='+', help='adds channel to your subscription_list')
    args = parser.parse_args()
    if args.add_channel:
        for channel in args.add_channel:
            add_subscription(yt,channel)
    elif args.download:
        main()

