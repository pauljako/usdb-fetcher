#!/usr/bin/env python3

from urllib.request import urlretrieve
import re
import sys
import os
import bs4
import requests

URL = "https://usdb.animux.de"
HEADERS = {"User-Agent": "Mozilla/5.0"}

BASE_FOLDER = os.path.realpath(os.path.expanduser(os.getenv("USDB_BASE_FOLDER", ".")))


def login(user_id, password) -> str | None:
    """Logs the User in and returns a session id"""
    response = requests.post(
        URL,
        headers=HEADERS,
        data={"user": user_id, "pass": password, "login": "Login"},
    )
    valid = (
        bs4.BeautifulSoup(response.text, "html.parser").find(
            string=re.compile("Login or Password invalid, please try again.")
        )
        is None
    )
    if not valid:
        return None

    cookies = requests.utils.dict_from_cookiejar(response.cookies)
    if "PHPSESSID" in cookies:
        return cookies["PHPSESSID"]

    return None


def get_song(session_id: str, song_id: str):
    response = requests.post(
        URL + f"?link=gettxt&id={song_id}",
        headers=HEADERS,
        cookies={"PHPSESSID": session_id},
        data={"wd": "1"},
    )

    soup = bs4.BeautifulSoup(response.text, "html.parser")

    output_name = soup.find("h1").string
    output_folder = os.path.join(BASE_FOLDER, output_name)
    os.makedirs(output_folder)

    original_lyrics = soup.find("textarea", attrs={"name": "txt"}).string
    lyrics = ""

    for line in original_lyrics.splitlines():
        if (
            line.startswith("#VIDEO")
            or line.startswith("#MP3")
            or line.startswith("#COVER")
        ):
            continue

        lyrics += f"{line}\n"

    with open(os.path.join(output_folder, f"{output_name}.txt"), "wt") as f:
        f.write(lyrics)

    urlretrieve(
        URL + f"/data/cover/{song_id}.jpg",
        os.path.join(output_folder, f"{output_name}.jpg"),
    )
    
    response = requests.get(
        URL + f"?link=detail&id={song_id}",
        headers=HEADERS,
        cookies={"PHPSESSID": session_id},
    )

    print(response.text)

    soup = bs4.BeautifulSoup(response.text, "html.parser")

    yt_link = soup.find("iframe")["src"]

    if os.system(f"yt-dlp -o '{output_folder}/video.webm' '{yt_link}'") != 0:
        return

    os.system(f"ffmpeg -i '{output_folder}/video.webm' -vcodec h264 -acodec aac '{output_folder}/{output_name}.mp4'")
    os.system(f"ffmpeg -i '{output_folder}/video.webm' -vn -acodec mp3 '{output_folder}/{output_name}.mp3'")


def search_titles(session_id: str, search_term: str) -> dict[str, str] | None:
    response = requests.post(
        URL + "?link=list",
        headers=HEADERS,
        cookies={"PHPSESSID": session_id},
        data={"title": search_term},
    )
    if not response.ok:
        return None

    soup = bs4.BeautifulSoup(response.text, "html.parser")
    table_results = soup.find_all("tr", onmouseover="this.className='list_hover'")

    results = {}

    for song in table_results:

        song_id = song["data-songid"]
        print(song_id)

        columns = song.find_all("td")
        print(columns)

        if len(columns) != 11:
            continue

        title_field = columns[1].find("a")
        title = title_field.get_text(strip=True)

        results[song_id] = title

    return results


def main():
    session_id = login(input("Enter Username: "), input("Enter Password: "))
    if session_id is None:
        sys.exit(1)

    titles = search_titles(session_id, input("Enter search term: "))
    if titles is None or len(titles) <= 0:
        sys.exit(1)

    titlenum = 1
    for titleid in list(titles.keys()):
        title = titles[titleid]
        print(f"[{titlenum}] {title} (ID: {titleid})")
        titlenum += 1

    selection = int(input("Enter a selection: "))

    get_song(session_id, list(titles.keys())[selection - 1])
