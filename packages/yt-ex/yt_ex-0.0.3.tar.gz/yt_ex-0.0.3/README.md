# yt-ex (YouTube Extractors)

## Introduction

This repository contains scripts that, given a query, retrieve various information (such as
video IDs, playlist IDs, etc.) extracted from data provided by Google's private InnerTube API.

## Usage

Currently only one script is available, yt-ex, which allows you to get all the music associated
with a particular name provided as input directly to stdout.

```sh
yt-ex "Tom Waits"
...
Frankie's Starter For Album 2025 OLAK5uy_lNXnmaMKjo1H2dvYPT6YXWYNal6x5XkDc
Get Behind The Mule (Spiritual) Single 2024 OLAK5uy_l7xNyRHN3U6aKb-arDmshPmAXRfEnGgws
Under The Bridge Album 2024 OLAK5uy_kFBYeured7dNTE84zdrtb1UZ924diVxBE
Hope That I Don't Fall In Love With You Album 2023 OLAK5uy_k7_dwDdUHQffhtVzraKJBU7-PGz3M36OQ
...
```

Below is an example of using yt-ex in combination with "yt-dlp", an open-source project that
allows you to download content from various platforms, including YouTube.

```sh
yt-ex "Tom Waits" | awk '{print $NF}' | yt-dlp -o "~/yt-dlp/%(uploader)s/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s" --embed-metadata --embed-thumbnail -t mp3 -a -
```

This command will download the entire discography of "Tom Waits".

## Installation
Code is hosted on PyPi so you can install it using pip or some other variant like pipx.
```sh
pip install yt-ex
```
