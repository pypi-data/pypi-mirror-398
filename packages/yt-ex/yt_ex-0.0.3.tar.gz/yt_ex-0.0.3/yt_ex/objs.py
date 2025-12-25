from dataclasses import dataclass


@dataclass
class Playlist:
    title: str
    album_type: str
    release_year: int
    playlist_id: str


@dataclass
class Video:
    title: str
    video_id: str
