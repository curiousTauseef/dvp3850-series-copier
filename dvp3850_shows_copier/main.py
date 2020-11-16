#!/bin/env python3

import argparse
import sys
from pathlib import Path
from typing import Optional

from pymediainfo import MediaInfo

from .cache import Cache
from .config import get_config


def determine_compatibility(video_file: Path,
                            verbose: bool = True):
    """Determines if the video at the provided path is compatible
    with the Philips DVP3850 player.

    Args:
        video_file: Video file to check.
    
    Returns:
        `True` if compatible, `False` otherwise.
    """

    media_info = MediaInfo.parse(video_file)
    
    video_compatible = False
    audio_compatible = False
    for info_track in media_info.tracks:
        try:
            if info_track.track_type == 'Video' and not video_compatible:
                if (
                    ((info_track.codec_id or '').lower() in ['xvid', 'divx'] or
                    (info_track.codec_id_hint or '').lower() in ['xvid', 'divx']) and
                    (1.3 <= float(info_track.display_aspect_ratio) < 1.34)):
                        video_compatible = True
            elif info_track.track_type == 'Audio' and not audio_compatible:
                if ((info_track.codec_id or '').lower()  in ['a_ac3', 'mp3'] or
                    (info_track.codec_id_hint or '').lower() in ['a_ac3', 'mp3']):
                        audio_compatible = True
        except AttributeError:
            continue

    return video_compatible and audio_compatible


def run_copier(shows, base_path, target_path, cache, random=True,
               uniformous=None, verbose=True):

    # print(shows, base_path, target_path, cache.cache_file, random, uniformous, verbose)

    copied = 0
    for show in shows:
        if '/Season ' in show and int(show[-1]) in range(10):
            show_iter = (config['general'].getpath('base path') / show).rglob('*')
        else:
            show_iter = (config['general'].getpath('base path') / show).rglob('Season */*')

        for video_file in sorted(show_iter):
            if video_file.is_dir():
                continue

            if verbose:
                print(f'{video_file.name}... ', end='')


            try:
                # TODO: Implement `in` contains check.
                is_compatible = cache[video_file]
            except Exception:
                is_compatible = determine_compatibility(video_file, cache)

            if verbose:
                print(('yes' if is_compatible else 'no') + ' (from cache)')

            cache[video_file] = is_compatible
            cache.write()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='dvp3850-shows-copier')

    # TODO: Use type `ShowEnum`.
    parser.add_argument('show',
                        nargs='+',
                        type=str,
                        help='shows to include in copy task. optionally, you '
                             'can restrict to a given season, using the '
                             'notation `Friends/Season 01`',
                        metavar='SHOW')
    parser.add_argument('-N', '--count',
                        type=int,
                        required=True,
                        help='amount of episodes to copy')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        default=True,
                        help='use verbose output')
    parser.add_argument('-r', '--random',
                        action='store_true',
                        help='make random selection of episodes')
    parser.add_argument('-u', '--uniformous',
                        action='store_true',
                        help='pick equally many episodes from each show')
    args = parser.parse_args()

    config = get_config()
    base_path = config['general'].getpath('base path')
    target_path = config['general'].getpath('target base path')
    cache = Cache(config['general'].getpath('cache file'), base_path)

    run_copier(args.show, base_path, target_path, cache, random=args.random,
               uniformous=args.uniformous, verbose=args.verbose)

