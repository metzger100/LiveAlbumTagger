# LiveAlbumTagger

LiveAlbumTagger is a Python script that uses the MusicBrainz API to identify and tag live albums in your music library. It scans your music directory, retrieves album information from MusicBrainz, and updates album tags to include "(Live)" if the album is identified as a live album.

## Features

- Scans a directory of music files in `.m4a` format.
- Uses the MusicBrainz API to fetch album information.
- Identifies live albums based on MusicBrainz metadata.
- Updates album tags to include "(Live)" for identified live albums.
- Ignores existing "(Live)" tags to avoid duplication.

## Requirements

- Python 3.x
- `mutagen` library
- `musicbrainzngs` library

## Installation

1. Ensure you have Python 3.x installed on your system.
2. Install the required libraries

## Usage

Run the script using the following command:

```sh
python livealbumtagger.py -p <path_to_music_directory>
```

Replace `<path_to_music_directory>` with the path to the directory containing your `.m4a` music files.

### Example

```sh
python livealbumtagger.py -p "music"
```

This will process all `.m4a` files in the "music" directory, update album tags to include "(Live)" for identified live albums, and print the results to the console.

## How It Works

1. **Initialization**: The script initializes the MusicBrainz API with a user agent.
2. **Directory Scan**: It scans the specified music directory for `.m4a` files.
3. **Album Identification**: For each album, it fetches album information from MusicBrainz.
4. **Track Matching**: It matches the local tracks with the tracks retrieved from MusicBrainz.
5. **Live Album Check**: It checks if the album is categorized as "Live" in MusicBrainz.
6. **Tag Update**: If the album is identified as live, it updates the album tag to include "(Live)" and removes any existing "(Live)" tags to avoid duplication.

## Logging

The script uses Python's built-in logging module to log the processing steps. Log messages include information about the albums being processed, matches found, and any errors encountered.
