#!/usr/bin/python3

import os
import weltschmerz.pyselect as pyselect
import sys
import difflib
import datetime
import weltschmerz.anime as anime
from sqlalchemy import func
import argparse
import configparser
import re


def get_config(config_file: str = "weltschmerz.cfg"):
    config = configparser.ConfigParser()
    with open(config_file, "r", encoding="UTF-8") as cf:
        config.read_file(cf)

    parser = argparse.ArgumentParser(description="Remove dupes from db and disk.")
    parser.add_argument(
        "--database", help="database to use", default=config.get("client", "database")
    )
    parser.add_argument(
        "--log-file",
        dest="log_file",
        help="logfile to use",
        default=config.get("client", "log"),
    )
    parser.add_argument(
        "--preferred-directory-pattern",
        dest="preferred_directory_pattern",
        help="on duplicates with only one filename, prefer to keep files in directory matching the pattern",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        help="dry-run, no removing deleted files",
        default=False,
        dest="dry_run",
        action="store_true",
    )

    args = parser.parse_args()
    return args


def update_mtimes(files):
    available_files = [file for file in files if os.path.isfile(file.full_path)]
    if len(available_files) > 0:
        oldest_mtime = os.path.getmtime(available_files[0].full_path)
        for file in available_files:
            mtime = os.path.getmtime(file.full_path)
            if mtime <= oldest_mtime:
                oldest_mtime = mtime
        for file in available_files:
            if os.path.getmtime(file.full_path) != oldest_mtime:
                print(
                    f"setting atime/mtime to {datetime.datetime.fromtimestamp(oldest_mtime).isoformat()} for {file.full_path}"
                )
                os.utime(file.full_path, (oldest_mtime, oldest_mtime))
    return available_files


def remove_duplicate_files(
    database: str,
    preferred_directory_pattern: str,
    dry_run: bool = False,
):
    dbs = anime.DatabaseSession(database, False)
    known_dupes = (
        dbs.session.query(anime.LocalFile.hash_ed2k, anime.LocalFile.filesize)
        .group_by(anime.LocalFile.hash_ed2k, anime.LocalFile.filesize)
        .having(func.count() >= 2)
        .all()
    )
    # print(known_dupes)
    # sys.exit(1)
    for i, (hash_ed2k, filesize) in enumerate(known_dupes, start=1):
        known_files = (
            dbs.session.query(anime.LocalFile)
            .filter(
                anime.LocalFile.hash_ed2k == hash_ed2k,
                anime.LocalFile.filesize == filesize,
            )
            .order_by(anime.LocalFile.filename, anime.LocalFile.directory)
            .all()
        )

        print("[ {current:05} / {total:05} ]".format(current=i, total=len(known_dupes)))
        available_files = update_mtimes(known_files)
        if len(available_files) <= 1:
            continue
        print("\n" * 8 + "#" * 128 + "\n")
        file_names = list(
            set([available_file.filename for available_file in available_files])
        )
        print(file_names)
        if len(file_names) == 1:
            selection = available_files[0]
            # keep files from directory matching preferred pattern
            if preferred_directory_pattern:
                print("preferred pattern found")
                for available_file in available_files:
                    if re.match(preferred_directory_pattern, available_file.directory):
                        print(
                            f'selecting file from preferred location: "{available_file.directory}" - "{available_file.filename}"'
                        )
                        selection = available_file
                        break
            print("File to keep:")
            print(f"{selection.filename} ({selection.directory})")
        else:
            sys.stdout.writelines(
                difflib.context_diff(
                    file_names[0], file_names[1], fromfile="a", tofile="b"
                )
            )
            print()
            print("File to keep:")
            # continue
            selection = pyselect.select(
                available_files, 'f"{option.filename} ({option.directory})"'
            )
        # keep only files to remove in array
        available_files.remove(selection)
        print([file.full_path for file in available_files])
        for file in available_files:
            if os.path.isfile(selection.full_path) and os.path.realpath(
                selection.full_path
            ) != os.path.realpath(file.full_path):
                print(f"deleting file: {file.full_path}")
                if not dry_run:
                    os.remove(file.full_path)
                print(f"removing file from db: {file.full_path}")
                if not dry_run:
                    dbs.session.delete(file)
        if not dry_run:
            dbs.session.commit()


if __name__ == "__main__":
    config = get_config()
    remove_duplicate_files(
        database=config.database,
        preferred_directory_pattern=config.preferred_directory_pattern,
        dry_run=config.dry_run,
    )
