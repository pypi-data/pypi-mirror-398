#!/usr/bin/env python3
"""IR downloader"""

# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025 NexusSfan <nexussfan@duck.com>

import argparse
import json
import re
import sys
import requests
from yt_dlp import YoutubeDL
from bs4 import BeautifulSoup
from tqdm import tqdm

__import__("lxml")  # check for lxml

__version__ = "1.1.0"
FULL_TITLE = f"sarzaminget {__version__} (NexusSfan <nexussfan@duck.com>)"
CURL_AGENT = f"curl/0.0.0, for {FULL_TITLE}"
headers = {"User-Agent": FULL_TITLE}
curl_headers = {"User-Agent": CURL_AGENT}


def arguments():
    parser = argparse.ArgumentParser(prog="sarzaminget", description="IR Downloader")
    parser.add_argument("link", help="SarzaminDownload link")
    parser.add_argument("-V", "--verbose", help="Verbose mode", action="store_true")
    parser.add_argument(
        "-v", "--version", help="version", action="version", version=FULL_TITLE
    )
    return parser.parse_args()


args = arguments()
verbose = args.verbose


def log(printed):
    if verbose:
        print(printed)


def get_links_sarzamindownload(url):
    log(f"Loading {url}")
    site = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(site.text, features="lxml")
    log("Checking for links")
    all_links = soup.find_all("a")
    sarzamin_links = []
    title_for_links = []
    for some_links in all_links:
        if some_links.attrs.get("href"):
            if "wikishare.ir" in some_links.attrs["href"]:
                title_string_list = [
                    title_string
                    for title_string in some_links.contents
                    if isinstance(title_string, str)
                ]
                title_string = title_string_list[0]
                log(f"Found link {some_links.attrs['href']} with title {title_string}")
                sarzamin_links.append(some_links.attrs["href"])
                title_for_links.append(title_string)
    return sarzamin_links, title_for_links


def get_links_soft98(url):
    log(f"Loading {url}")
    site = requests.get(
        url, headers=curl_headers, timeout=10
    )  # in order to bypass the captcha, use fake curl useragent
    soup = BeautifulSoup(site.text, features="lxml")
    log("Checking for links")
    links_html = soup.find("dl")
    all_links = json.loads(links_html.attrs["data-json"])
    all_titles = [title.a for title in soup.find_all("dd", class_="dbdlli")]
    soft98_links = []
    title_for_links = []
    for key, value in all_links.items():
        linkno = int(key.replace("alink", ""))
        if "soft98.ir" in value["bddlh"]:
            linkfinal = f"{value['bddls']}://{value['bddlh']}{value['bddlp']}"
            log(f"Found link {linkfinal} with title {all_titles[linkno - 1].string}")
            soft98_links.append(linkfinal)
            title_for_links.append(all_titles[linkno - 1].string)
    return soft98_links, title_for_links


def get_links_p30download(url):
    p30_links = []
    title_for_links = []
    linksgotten = False
    log(f"Loading {url}")
    site = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(site.text, features="lxml")
    log("Getting link source")
    if not linksgotten:
        scripts = soup.find_all("script")
        for script in scripts:
            string = "".join(script.contents)
            if "function get_dlbox()" in string:
                network_link = string.split("$.get('")[1].split("'")[0]
                extra_header = headers
                extra_header["Referer"] = url
                links = requests.get(
                    f"https:{network_link}", headers=extra_header, timeout=10
                )
                linksoup = BeautifulSoup(links.text, features="lxml")
                for linkget in linksoup.find_all(
                    "a", target="_blank", rel="nofollow noreferrer"
                ):
                    linkfinal = linkget.attrs["href"]
                    titlefinal = "".join(
                        [content.string for content in linkget.contents]
                    )
                    log(f"Found link {linkfinal} with title {titlefinal}")
                    p30_links.append(linkfinal)
                    title_for_links.append(titlefinal)
                linksgotten = True
    if not linksgotten:
        a_hrefs = soup.find_all("a", rel="nofollow", target="_blank")
        for a_href in a_hrefs:
            link_href = a_href.attrs["href"]
            if "sharezilla.ir" in link_href:
                title_string = "".join(
                    [title_string.string for title_string in a_href.contents]
                )
                log(f"Found link {link_href} with title {title_string}")
                p30_links.append(link_href)
                title_for_links.append(title_string)
            linksgotten = True
    return p30_links, title_for_links


def download_todl(links_to_dl, titles_to_dl):
    for linkno, link in enumerate(links_to_dl):
        print(f"Downloading {titles_to_dl[linkno]}...")
        r = requests.get(
            link, stream=True, allow_redirects=True, headers=headers
        )  # pylint: disable=missing-timeout
        total_size = int(r.headers.get("Content-Length", 0))
        block_size = 1024
        raw_url = link.split("?")[0]
        with tqdm(total=total_size, unit="B", unit_scale=True) as progress_bar:
            with open(raw_url.split("/")[-1], "wb") as file:
                for data in r.iter_content(block_size):
                    progress_bar.update(len(data))
                    file.write(data)


def downloader(url, links_func):
    links, titles = links_func(url)
    if len(links) > 1:
        print("There are multiple links")
        for linknumber, link in enumerate(links):
            print(f"#{linknumber} - {titles[linknumber]} - {link}")
        print("Please select which one you want to download")
        print("(seperated by commas, no spaces please)")
        to_dl = [int(i) for i in input().split(",")]
    elif len(links) == 0:
        print("No links found!")
        sys.exit(1)
    else:
        to_dl = [0]
    links_to_dl = [links[l] for l in to_dl]
    titles_to_dl = [titles[l] for l in to_dl]
    download_todl(links_to_dl, titles_to_dl)


if __name__ == "__main__":
    if re.match(r"^https?:\/\/(?:www\.)?sarzamindownload\.com\/.*", args.link):
        downloader(args.link, get_links_sarzamindownload)
    if re.match(r"^https?:\/\/(?:www\.)?soft98\.ir\/.*", args.link):
        downloader(args.link, get_links_soft98)
    if re.match(r"^https?:\/\/(?:www\.)?aparat\.com\/.*", args.link):
        with YoutubeDL() as ydl:
            ydl.download(args.link)
    if re.match(r"^https?:\/\/(?:www\.)?p30download\.ir\/.*", args.link):
        downloader(args.link, get_links_p30download)
