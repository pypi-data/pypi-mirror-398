from .objs import Video, Playlist


def get_videos(data: dict) -> list[Video]:
    videos: list[Song] = []
    for item in data["contents"]["singleColumnMusicWatchNextResultsRenderer"][
        "tabbedRenderer"]["watchNextTabbedResultsRenderer"]["tabs"][0][
        "tabRenderer"]["content"]["musicQueueRenderer"]["content"][
        "playlistPanelRenderer"]["contents"]:
        if "playlistPanelVideoRenderer" in item:
            item_data = item["playlistPanelVideoRenderer"]
            title = item_data["title"]["runs"][0]["text"]
            video_id = item_data["videoId"]
            videos.append(
                Video(
                    title=title,
                    video_id=video_id
                )
            )
    return videos


def get_channel_id(data: dict) -> str:
    return data["contents"]["tabbedSearchResultsRenderer"][
        "tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"][
        "contents"][1]["musicCardShelfRenderer"]["title"]["runs"][0][
        "navigationEndpoint"]["browseEndpoint"]["browseId"]


def get_playlists(data: dict) -> list[Playlist]:
    albums: list[Playlist] = []
    for item in data["contents"]["singleColumnBrowseResultsRenderer"]["tabs"][0][
        "tabRenderer"]["content"]["sectionListRenderer"]["contents"][
            0]["gridRenderer"]["items"]:

        item_data = item["musicTwoRowItemRenderer"]
        album_type = item_data["subtitle"]["runs"][0]["text"]
        title = item_data["title"]["runs"][0]["text"]
        release_year = int(item_data["subtitle"]["runs"][-1]["text"])
        playlist_id = item_data["menu"]["menuRenderer"]["items"][
            0]["menuNavigationItemRenderer"]["navigationEndpoint"][
            "watchPlaylistEndpoint"]["playlistId"]
        albums.append(
            Playlist(
                title=title,
                album_type=album_type,
                release_year=release_year,
                playlist_id=playlist_id
            )
        )
    return albums


def get_search_suggestions(data: dict) -> list[str]:
    search_suggestions_section: dict = data["contents"][0][
        "searchSuggestionsSectionRenderer"]
    if "contents" in search_suggestions_section:
        contents = search_suggestions_section["contents"]
    else:
        contents: list[dict] = search_suggestions_section["shelfDivider"]
    return [
        el["searchSuggestionRenderer"]["navigationEndpoint"][
            "searchEndpoint"]["query"]
        for el in contents
    ]
