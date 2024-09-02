import os
import argparse
from mutagen.easymp4 import EasyMP4
import musicbrainzngs
import logging
from difflib import SequenceMatcher
import re

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set the logging level for the musicbrainzngs library to WARNING
logging.getLogger('musicbrainzngs').setLevel(logging.WARNING)

# MusicBrainz API initialization
musicbrainzngs.set_useragent("AlbumTagger", "1.0", "https://example.com")

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def clean_track_title(title):
    return re.sub(r'\s*\(Live\)\s*', '', title, flags=re.IGNORECASE).strip()

def get_album_info_from_musicbrainz(album_name, artist):
    try:
        logging.info(f"Searching for album: {album_name}, artist: {artist}")
        result = musicbrainzngs.search_releases(release=album_name, artist=artist, limit=25)
        if result['release-list']:
            logging.info(f"{len(result['release-list'])} results found for album: {album_name}, artist: {artist}")
            return result['release-list']
        logging.info(f"No live tag found for album: {album_name}, artist: {artist}")
        return []
    except Exception as e:
        logging.error(f"\033[91mError querying MusicBrainz: {e}\033[0m")
        return []

def get_release_track_list(release_id):
    try:
        result = musicbrainzngs.get_release_by_id(release_id, includes=["recordings"])
        tracks = []
        for medium in result['release']['medium-list']:
            for track in medium['track-list']:
                tracks.append(track['recording']['title'])
        return tracks
    except Exception as e:
        logging.error(f"\033[91mError fetching track list for release ID {release_id}: {e}\033[0m")
        return []

def match_tracks(local_tracks, mb_release):
    mb_tracks = get_release_track_list(mb_release['id'])
    logging.info(f"MB track list for release '{mb_release['title']}': {mb_tracks}")

    matches = 0
    for local_track in local_tracks:
        cleaned_local_track = clean_track_title(local_track)
        for mb_track in mb_tracks:
            similarity = similar(cleaned_local_track, mb_track)
            if similarity > 0.8:  # similarity threshold
                matches += 1
                break
    return matches, len(mb_tracks)

def contains_live_tracks(local_tracks):
    live_title_count = 0
    for local_track in local_tracks:
        if "live" in local_track.lower():
            live_title_count += 1
    return live_title_count, len(local_tracks)

def is_live_album(mb_release):
    primary_type = mb_release['release-group'].get('primary-type', '').lower()
    secondary_types = [stype.lower() for stype in mb_release['release-group'].get('secondary-type-list', [])]
    return 'live' in primary_type or 'live' in secondary_types

def process_album(album_name, album_artist, file_paths):
    local_tracks = []

    if file_paths:
        local_tracks = [EasyMP4(fp).get('title', [None])[0] for fp in file_paths]

    logging.info(f"Processing album: {album_name}, artist: {album_artist}")
    mb_releases = get_album_info_from_musicbrainz(album_name, album_artist)
    best_match = None
    best_match_score = 0
    best_match_total_tracks = 0

    # Erste Überprüfung: Suche nach dem besten passenden Release
    for mb_release in mb_releases:
        if not is_live_album(mb_release):
            continue
        matches, total_tracks = match_tracks(local_tracks, mb_release)

        if total_tracks > 0 and (matches / total_tracks > 0.75) and matches > best_match_score:
            best_match = mb_release
            best_match_score = matches
            best_match_total_tracks = total_tracks

    if best_match:
        logging.info(f"\033[94mBest match for album: {album_name} by {album_artist} with {best_match_score} matching tracks out of {best_match_total_tracks}\033[0m")
        update_album_metadata(file_paths, album_name, album_artist)
    else:
        # Zweite Überprüfung: Überprüfe, ob das Album viele "Live"-Titel enthält
        live_title_count, total_tracks = contains_live_tracks(local_tracks)

        if total_tracks > 0 and (live_title_count / total_tracks > 0.8):
            logging.info(f"\033[94mAlbum '{album_name}' by {album_artist} seems to be a live album because {live_title_count} out of {total_tracks} tracks contain 'live'.\033[0m")
            update_album_metadata(file_paths, album_name, album_artist)
        else:
            logging.info(f"\033[91mNo type album for album: {album_name} by {album_artist}\033[0m")  # Red

def update_album_metadata(file_paths, album_name, album_artist):
    clean_album_name = re.sub(r'\s*\(Live\)\s*', '', album_name, flags=re.IGNORECASE).strip()
    new_album_name = f"(Live) {clean_album_name}"

    for file_path in file_paths:
        audio = EasyMP4(file_path)
        audio['album'] = new_album_name
        audio.save()
        print(f"\033[92mUpdated album '{album_name}' by {album_artist} to '{new_album_name}: {file_path}'\033[0m")  # Green


def crawl_music_directory(directory):
    music_tags = {}
    for root, _, files in os.walk(directory):
        # Überprüfe, ob "(EP)" im Verzeichnisnamen enthalten ist
        if "(EP)" in root:
            logging.warning(f"\033[93mIgnoring '(Live)' in album/track names for directory: {root} because it contains '(EP)'\033[0m")
            continue
        else:
            for file in files:
                if file.endswith('.m4a'):
                    file_path = os.path.join(root, file)
                    audio = EasyMP4(file_path)
                    album_name = audio.get('album', [None])[0]
                    album_artist = audio.get('artist', [None])[0]
                    if album_name and album_artist:
                        album_key = (album_name, album_artist)
                        if album_key not in music_tags:
                            music_tags[album_key] = []
                        music_tags[album_key].append(file_path)
                        logging.info(f"Found album: {album_name}, artist: {album_artist}, file: {file_path}")
                    else:
                        logging.warning(f"Album name or artist not found for file: {file_path}")
    return music_tags

def main(directory):
    open("Tagging_is_running.txt", 'w').close()

    logging.info(f"Starting processing of directory: {directory}")
    music_tags = crawl_music_directory(directory)
    for (album_name, album_artist), file_paths in music_tags.items():
        process_album(album_name, album_artist, file_paths)
    logging.info(f"Processing of directory completed: {directory}")

    os.remove("Tagging_is_running.txt")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process music directory and update album tags.")
    parser.add_argument('-p', '--path', type=str, required=True, help='Path to the music directory')

    args = parser.parse_args()

    main(args.path)
