import sys, os, yt_ex
from yt_ex import extractors as ex
from argparse import ArgumentParser
from innertube.clients import InnerTube


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Script for extracting data provided by Google's private InnerTube API.")
    _ = parser.add_argument('query', type=str, help='query to make')
    _ = parser.add_argument('--title', action='store_true', help='include title')
    _ = parser.add_argument('--album-type', action='store_true', help='include album type')
    _ = parser.add_argument('--release-year', action='store_true', help='include release year')
    _ = parser.add_argument('--playlist-id', action='store_true', help='include playlist id')
    return parser


def main() -> None:
    parser = get_parser()
    args = parser.parse_args()

    innertube_client = InnerTube('WEB_REMIX')
    response = innertube_client.search(args.query)
    try:
        channel_id = ex.get_channel_id(response)
    except (KeyError, IndexError):
        print(f'no results\n')
        sys.exit(1)

    response = innertube_client.browse(f"MPAD{channel_id}")
    playlists = ex.get_playlists(response)

    try:
        for p in playlists:
            if (
                not args.title and 
                not args.album_type and 
                not args.release_year and
                not args.playlist_id
            ):
                print(f"{p.title} {p.album_type} {p.release_year} {p.playlist_id}")
            else:
                if args.title:
                    print(p.title, end=' ')
                if args.album_type:
                    print(p.album_type, end=' ')
                if args.release_year:
                    print(p.release_year, end=' ')
                if args.playlist_id:
                    print(p.playlist_id, end=' ')
                print()

    except BrokenPipeError:
        # Python flushes standard streams on exit;
        # redirect remaining output to devnull to avoid another BrokenPipeError at shutdown
        devnull = os.open(os.devnull, os.O_WRONLY)
        _ = os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)  # Python exits with error code 1 on EPIPE


if __name__ == '__main__':
  main()

