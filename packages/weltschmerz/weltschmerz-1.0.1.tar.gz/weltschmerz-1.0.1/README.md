# weltschmerz

Maintain a (local) database for anime files.
Contains scripts to hash and sort anime files,
as well as looking up files in AniDB utilizing the `yumemi` Python module.

This project is licensed under the terms of the MIT license. These third-party files are included:

* `pyselect.py`: Copyright 2013 Matthew Behrens, under the terms of the MIT license.
* `sorttable.js`: Copyright 2007 Stuart Langridge, under the terms of the X11/MIT license.

See also [LICENSE.md](./LICENSE.md)

## Requirements

* Python 3 (>=3.6)
* [yumemi](https://pypi.org/project/yumemi/) Python module (optional, for interacting with AniDB)
* SQL database
  * PostgreSQL works, and is recommended
  * SQLite3 works, but does not support the `numeric` collation, order for T/S/P/O episodes might be wrong

## Configuration file

Copy `weltschmerz.cfg.example` to `weltschmerz.cfg` or `$HOME/.config/weltschmerz/weltschmerz.cfg` and adjust as necessary.

## Import AniDB MyList export

It is recommended to import your MyList first, as that will populate the Anime, Episode, and File tables.

1. Request an `xml-plain-full` export of your MyList at [AniDB - MyList Export](https://anidb.net/user/export)
1. Download export file
1. Extract the export file:`tar xf <mylist_export>.tgz`
1. Parse the export and populate the local database: `./parse_mylist_export.py --mylist-xml-files anime/a*.xml`

## Hash local files

`weltschmerz files hash --folder /anime/by-id/00/00/01/ --folder /anime/by-id/00/00/02/`

## Add files to your AniDB MyList

Lookup the local files in AniDB and add them to your MyList, if they are present in AniDB.
`weltschmerz anidb lookup-files --folder /anime/by-id/00 --folder /anime/by-id/01 --debug --online --add-to-mylist --mylist-state 4`

## Deduplicate local files

Interactively deduplicate local files, as well as set the modified time of duplicate files to the oldest one.
`weltschmerz files remove-duplicates --preferred-directory-pattern /anime/by-id`

## Sort local files

Sort/Move files, this will put the files into folders according to their anime ids (padded to 6 digits) from AniDB.
e.g. files for [Seikai no Monshou (anime id 1)](https://anidb.net/anime/1) will be put in `<target_basedir>/by-id/00/00/01`.

`weltschmerz files sort --source-basedir /anime/unsorted --target-basedir /anime`

## Create symlinks for local anime folders

To be able to look for local anime by name, create symlinks to point to the folders created by "Sort local files".
This creates a `by-name` folder under the target basedir.

1. Download anime titles dump (XML) from AniDB, see [AniDB Wiki - API/Anime Titles](https://wiki.anidb.net/API#Anime_Titles) for instructions.
1. Decompress the title dump: `gunzip anime-titles.xml.gz`
1. Run script to create the symlinks: `./animetitle.py anime-titles.xml /anime/`
