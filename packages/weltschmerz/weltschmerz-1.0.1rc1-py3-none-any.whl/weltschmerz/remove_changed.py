#!/usr/bin/python3

import weltschmerz.anime as anime
import configparser
import os
import argparse


def get_config(config_file: str = "weltschmerz.cfg"):
    config = configparser.ConfigParser()
    with open(config_file, "r", encoding="UTF-8") as cf:
        config.read_file(cf)

    parser = argparse.ArgumentParser(
        description="Remove files that changed in size from database."
    )
    parser.add_argument(
        "--database", help="database to use", default=config.get("client", "database")
    )
    parser.add_argument(
        "--log-file",
        dest="log_file",
        help="logfile to use",
        default=config.get("client", "log"),
    )
    parser.add_argument("--folder", help="folder to process", default="/")
    parser.add_argument(
        "--dry-run",
        "-n",
        help="dry-run, no removing changed files",
        default=False,
        dest="dry_run",
        action="store_true",
    )

    args = parser.parse_args()
    return args


def remove_changed_files(database: str, folder: str, dry_run: bool = False):
    dbs = anime.DatabaseSession(database, False)
    hashed_files = dbs.session.query(anime.LocalFile).filter(
        anime.LocalFile.directory.like(folder + "%")
    )
    for local_file in hashed_files:
        if os.path.isfile(local_file.full_path):
            if local_file.filesize != os.path.getsize(local_file.full_path):
                print(f"###### filesize mismatch, removing {local_file.full_path}")
                if not dry_run:
                    dbs.session.delete(local_file)


if __name__ == "__main__":
    config = get_config()
    remove_changed_files(
        database=config.database,
        folder=config.folder,
        dry_run=config.dry_run,
    )
