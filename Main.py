import yt_dlp
import subprocess
import threading
import PIL.Image
import os
import pystray
import webbrowser
import json
import tkinter as tk
from tkinter import simpledialog

# Load tray icon
Image = PIL.Image.open("Radio.ico")

# Load stream list from JSON
with open('StreamList.json', 'r') as f:
    StreamList = json.load(f)

# Global variables
audio_proc = None
youtube_url = "none"
current_stream_name = "Nothing Playing"
append_lock = threading.Lock()

def setup(PlayURL, stream_name):
    global audio_proc, youtube_url, current_stream_name
    youtube_url = PlayURL
    current_stream_name = stream_name

    def get_stream_url(youtube_url):
        ydl_opts = {'format': 'best', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return info['url']

    stream_url = get_stream_url(youtube_url)
    audio_proc = None

    def play_audio(url):
        global audio_proc
        audio_proc = subprocess.Popen([
            "ffplay", "-nodisp", "-loglevel", "quiet",
            "-fflags", "nobuffer", url,
        ], creationflags=subprocess.CREATE_NO_WINDOW)

    threading.Thread(target=play_audio, args=(stream_url,), daemon=True).start()

def Stop(icon=None, item=None):
    global audio_proc, youtube_url, current_stream_name
    try:
        if audio_proc:
            audio_proc.kill()
        youtube_url = "none"
        current_stream_name = "Nothing Playing"
        update_menu()
    except Exception as e:
        print("No Stream Loaded:", e)

def Quit(icon, item):
    Stop()
    os._exit(0)

def Append(icon, item):
    if not append_lock.acquire(blocking=False):
        return

    def dialog_thread():
        global StreamList
        root = None
        try:
            root = tk.Tk()
            root.withdraw()

            name = simpledialog.askstring("Add Stream", "Enter stream name:", parent=root)
            if not name:
                return

            url = simpledialog.askstring("Add Stream", "Enter stream URL:", parent=root)
            if not url:
                return

            StreamList.append([name, url])
            with open('StreamList.json', 'w') as f:
                json.dump(StreamList, f, indent=4)

            print("Updated StreamList:", StreamList)
        finally:
            if root is not None:
                root.destroy()
            update_menu()
            append_lock.release()

    threading.Thread(target=dialog_thread, daemon=True).start()

def play_stream(icon, item, url, name):
    Stop()
    setup(url, name)
    update_menu()

def webpage():
    if youtube_url != "none":
        webbrowser.open(youtube_url)

def create_callback(url, name):
    def callback(icon, item):
        play_stream(icon, item, url, name)
    return callback

def update_menu():
    global icon
    menu_items = [pystray.MenuItem(name, create_callback(url, name)) for name, url in StreamList]
    menu_items.append(pystray.MenuItem("", None))
    menu_items.append(pystray.MenuItem(f"Now Playing: {current_stream_name}", webpage))
    menu_items.append(pystray.MenuItem("Add YouTube Stream/Video", Append))
    menu_items.append(pystray.MenuItem("Stop Listening", Stop))
    menu_items.append(pystray.MenuItem("QUIT", Quit))

    icon.menu = pystray.Menu(*menu_items)
    icon.update_menu()

# Setting up Menu
temp_items = [pystray.MenuItem(name, create_callback(url, name)) for name, url in StreamList]
temp_items.append(pystray.MenuItem("", None))
temp_items.append(pystray.MenuItem("Nothing Playing", webpage))
temp_items.append(pystray.MenuItem("Add YouTube Stream/Video", Append))
temp_items.append(pystray.MenuItem("Stop Listening", Stop))
temp_items.append(pystray.MenuItem("QUIT", Quit))

icon = pystray.Icon("None", Image, menu=pystray.Menu(*temp_items))
icon.run()
