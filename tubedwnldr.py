import os
import re
import sys
import socks
import socket
import random
import requests
import youtube_dl
import av
import subprocess   #pip install imageio-ffmpeg
import imageio_ffmpeg as ffmpeg
import signal
from bs4 import BeautifulSoup
import time
import scrapetube

def handler(signum, frame):
    raise Exception()

def download_proxy_list(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    table = soup.find('table')
    list_proxies = []
    for row in table.find_all('tr'):
        columns = row.find_all('td')
        if columns:
            ip = columns[0].get_text()
            port = columns[1].get_text()
            list_proxies.append(f"{ip}:{port}")
    return list_proxies

def set_proxy(proxy_list):
    selected_proxy = random.choice(proxy_list)
    ip = (selected_proxy.split(':'))[0]
    port = (selected_proxy.split(':'))[1]
    return [ip, port]

def measure_proxy_speed(server_info):
    url = 'http://httpbin.org/get'
    proxies = {'http': f'http://{server_info[0]}:{server_info[1]}'}
    start = time.time()
    try:
        r = requests.head(url, proxies=proxies, timeout=1)
        r.raise_for_status()  # Raises stored HTTPError, if one occurred.
    except requests.RequestException:
        return 0  # Proxy failed
    latency = time.time() - start
    return latency  # Returns time in seconds


def clean_title(title):
    return re.sub(r'[^\w\s]', '', title).replace(' ', '_')

def download_video_audio_without_server(url, path):

    if not os.path.exists(path):
        os.makedirs(path)

    ydl_opts_video = {
        'format': 'bestvideo',
        'nocheckcertificate': True,
    }

    ydl_opts_audio = {
        'format': 'bestaudio',
        'nocheckcertificate': True,
    }

    # First, extract information
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(10)
    with youtube_dl.YoutubeDL(ydl_opts_video) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        raw_title = info_dict.get('title', None)
        title = clean_title(raw_title)
        filename_video = ydl.prepare_filename(info_dict)
    signal.alarm(0)

    with youtube_dl.YoutubeDL(ydl_opts_audio) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        filename_audio = ydl.prepare_filename(info_dict)

    video_format_and_extension = os.path.splitext(filename_video)[1][1:]
    audio_format_and_extension = os.path.splitext(filename_audio)[1][1:]

    # Then, download with the cleaned title
    ydl_opts_video.update({
        'outtmpl': os.path.join(path, f'{title}.video.%(ext)s'),
    })
    ydl_opts_audio.update({
        'outtmpl': os.path.join(path, f'{title}.audio.%(ext)s'),
    })

    with youtube_dl.YoutubeDL(ydl_opts_video) as ydl:
        ydl.download([url])
    with youtube_dl.YoutubeDL(ydl_opts_audio) as ydl:
        ydl.download([url])

    return [title, video_format_and_extension, audio_format_and_extension]


def download_video_audio(server_info, url, path):

    if not os.path.exists(path):
        os.makedirs(path)

    ydl_opts_video = {
        'format': 'bestvideo',
        'nocheckcertificate': True,
        'proxy': f'http://{server_info[0]}:{server_info[1]}',
    }

    ydl_opts_audio = {
        'format': 'bestaudio',
        'nocheckcertificate': True,
        'proxy': f'http://{server_info[0]}:{server_info[1]}',
    }

    # First, extract information
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(10)
    with youtube_dl.YoutubeDL(ydl_opts_video) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        raw_title = info_dict.get('title', None)
        title = clean_title(raw_title)
        filename_video = ydl.prepare_filename(info_dict)
    signal.alarm(0)
    time.sleep(2)
    with youtube_dl.YoutubeDL(ydl_opts_audio) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        filename_audio = ydl.prepare_filename(info_dict)
    time.sleep(2)
    video_format_and_extension = os.path.splitext(filename_video)[1][1:]
    audio_format_and_extension = os.path.splitext(filename_audio)[1][1:]

    # Then, download with the cleaned title
    ydl_opts_video.update({
        'outtmpl': os.path.join(path, f'{title}.video.%(ext)s'),
    })
    ydl_opts_audio.update({
        'outtmpl': os.path.join(path, f'{title}.audio.%(ext)s'),
    })

    with youtube_dl.YoutubeDL(ydl_opts_video) as ydl:
        ydl.download([url])
    time.sleep(2)
    with youtube_dl.YoutubeDL(ydl_opts_audio) as ydl:
        ydl.download([url])

    return [title, video_format_and_extension, audio_format_and_extension]


def merge_audio_video(title, video_type, audio_type, path):
    video_path = os.path.join(path, title + '.video.' + video_type)
    audio_path = os.path.join(path, title + '.audio.' + audio_type)
    output_path = os.path.join(path, f"{title}_final.mp4")

    # Use ffmpeg to merge video and audio
    command = f'{ffmpeg.get_ffmpeg_exe()} -i "{video_path}" -i "{audio_path}" -c:v copy -c:a aac "{output_path}"'
    subprocess.run(command, shell=True, check=True)

    # Remove the original video and audio files
    os.remove(video_path)
    os.remove(audio_path)

def process_video(youtube_url, proxy_list):
    while True:
        try:
            latency = measure_proxy_speed(server_info)
            if (latency == 0):
                raise Exception
            elif (latency >= 2):
                raise Exception

            listNames = download_video_audio(server_info, youtube_url, r'/Users/seg/Documents/tubedwnlds')
            title = listNames[0]
            video_type = listNames[1]
            audio_type = listNames[2]
            merge_audio_video(title, video_type, audio_type, r'/Users/seg/Documents/tubedwnlds')

            break  # Break the loop if the download is successful
        except Exception as e:  # Catch the exception if an IP blockage is detected
            server_info = set_proxy(proxy_list)
            print("Switching proxy and retrying...")

def get_video_urls(channelID):
    videos = scrapetube.get_channel(channelID)
    url_start = "https://www.youtube.com/watch?v="
    list = []
    for video in videos:
        list.append(url_start + str(video['videoId']))
    return list

def get_playlist_urls(playlistID):
    videos = scrapetube.get_playlist(playlistID)
    url_start = "https://www.youtube.com/watch?v="
    list = []
    for video in videos:
        list.append(url_start + str(video['videoId']))
    return list

def main():
    isChannel = input("Is this a channel download?")
    if (isChannel == "y" or isChannel =="Y"):
        channelID = input("What is the channel id?")
        urls = get_video_urls(channelID)
    else:
        isPlaylist = input("Is this a playlist download?")
        if (isPlaylist == "y" or isPlaylist =="Y"):
            playlistId = input("What is the playlist id?")
            urls = get_playlist_urls(playlistId)
        else:
            urls_string = input("Enter the YouTube URL (SPACE BETWEEN DIFFERENT URL):")
            urls = urls_string.split()
    server_boolean = True
    while (server_boolean == True):
        proxy_string = input("Do you want to use proxy? (y/n)")
        if (proxy_string=="y" or proxy_string=="Y"):
            github_proxy_list_url = 'http://free-proxy-list.net/'
            for youtube_url in urls:
                proxy_list = download_proxy_list(github_proxy_list_url)
                process_video(youtube_url, proxy_list)
            server_boolean = False
        elif (proxy_string=="n" or proxy_string=="N"):
            for youtube_url in urls:
                listNames = download_video_audio_without_server(youtube_url, r'/Users/seg/Documents/tubedwnlds')
                title = listNames[0]
                video_type = listNames[1]
                audio_type = listNames[2]
                merge_audio_video(title, video_type, audio_type, r'/Users/seg/Documents/tubedwnlds')
            server_boolean = False
        else:
            server_boolean = True;

if __name__ == "__main__":
    main()
