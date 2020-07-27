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
import eyed3
import argparse


close = False
special_chars = ["(", "["]  # Used to strip unnecessory song info in the filename.


def write(subs):
    with open("/home/gireesh/.config/.youtube.config/subscription_list", "w") as f:
        f.write(json.dumps(subs))


# donwload based on likes and dislike rate
def check_stats(yt_id, vd_id):
    vd_details = yt_id.videos().list(id=vd_id, part='statistics').execute()
    likes = int(vd_details['items'][0]['statistics']['likeCount'])
    dislikes = int(vd_details['items'][0]['statistics']['dislikeCount'])
    return True if likes*5/100 > dislikes else False


# check for video length, so that to differentiate between songs and videos
def check_time(time):
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


def download(link):
    download_option = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'nocheckcertificate': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
                }]
            }

# Download songs
    with youtube_dl.YoutubeDL(download_option) as dl:
        try:
            dl.download([link])
        except:
            with open("/home/gireesh/.config/.youtube.config/errored_links", "a") as f:
                f.write(link+"\n")


def download_channel(yt, channel_id, last_song, channel_num, total_channels):
    global close
    channel = yt.channels().list(id=channel_id, part="contentDetails").execute()
    playlist = channel["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    download_list = []
    token = None                # page token
    var = True                  # last song check variable
    page = 0
    while var:
        print(f" Getting musics list\nat page number {page} \n\n")
        lst = yt.playlistItems().list(playlistId=playlist, maxResults=10, pageToken=token, part="snippet").execute()
        for count, i in enumerate(lst["items"]):
            Id = i["snippet"]["resourceId"]["videoId"]
            print(count, Id)
            if last_song != Id:
                vd_detail = yt.videos().list(id=Id, part="contentDetails").execute()
                vd_time = vd_detail["items"][0]["contentDetails"]["duration"]
                # check if the video is song by guessing from the length
                if check_time(vd_time) and check_stats(yt, Id):
                    download_list.append(Id)
                else:
                    print(f"skipping  {i['snippet']['title']}\n duration: {vd_time}")
            else:
                var = False
                break
        token = lst.get("nextPageToken")
        if not token:
            break
        page += 1
    download_list.reverse()
    # os.system("clear")
    for count, i in enumerate(download_list):
        try:
            print(f"%s Downloading music from channel number {channel_num} out of {total_channels} %s" % (fg(11), attr(0)))
            print(f"%s song number {count+1} out of {len(download_list)} %s" % (fg(40), attr(0)))
            old_set_of_songs = set(os.listdir())
            download(i)
            latest_song = (set(os.listdir()) - old_set_of_songs)
            if latest_song:
                print(f"renaming file {latest_song}")
                add_title(latest_song.pop())
        except KeyboardInterrupt:
            close = True
            return last_song
        except youtube_dl.utils.DownloadError:
            print("download error skipping this one")
        except Exception as unkown_e:
            close = True
            print(unkown_e)
            return last_song
        # os.system("clear")
        last_song = i
    return last_song


def add_title(song):
    # This function changes songs title so it is better to use this at the end
    song_tag = eyed3.load(song)
    file_name = song_tag.path

    # Get only the file name
    while ("/" in file_name):
        file_name = file_name[file_name.index("/")+1:]
    title = file_name.rstrip(".mp3")

    for char in special_chars:
        if char in title:
            title = title[:title.index(char)]
    song_tag.tag.title = title
    song_tag.tag.save()
    try:
        # if song name isn't changed os error will occur
        song_tag.rename(title)
    except OSError:
        pass


def run_check():
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
    api_key = os.environ.get("youtube_api")
    if api_key:
        return build("youtube", "v3", developerKey=api_key)
    else:
        print("Error: Couldn't get the api_keys!!!")
        sys.exit(1)


def add_subscription(yt, channel_id):
    channel_id = channel_id.lstrip("https://").lstrip("www.").lstrip("youtube.com/channel/")
    channel = yt.channels().list(id=channel_id, part="contentDetails").execute()
    playlist = channel['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    lst = yt.playlistItems().list(playlistId=playlist, maxResults=10, pageToken=None, part="snippet").execute()
    last_song = lst['items'][0]['snippet']['resourceId']['videoId']
    
    title = yt.channels().list(id=cid, part="snippet").execute()['items'][0]['snippet']['title']
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

    print("download started")
    channel_num = 1
    total_channels = len(subs)
    for i, j in subs.items():
        print(f"%s Downloading music from channel number {channel_num} out of {total_channels} %s" % (fg(11), attr(0)))
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

    write(subs)


if __name__ == "__main__":
    yt = youtube_auth()
    parser = argparse.ArgumentParser(description="Downloads songs from youtube based on channels")
    parser.add_argument('-d','--download',action='store_true', help='downloads songs from the youtube based on subscription list')
    parser.add_argument('-a','--add-channel', metavar='channel url', nargs='+', help='adds channel to your subscription_list')
    args = parser.parse_args()
    if args.add_channel:
        for channel in args.add_channel:
            add_subscription(yt,channel)
    elif args.d:
        main()

