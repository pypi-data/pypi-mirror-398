#!/usr/bin/python3

import weltschmerz.anime as anime
import os.path
import configparser
import argparse


def get_config(config_file: str = "weltschmerz.cfg"):
    config = configparser.ConfigParser()
    with open(config_file, "r", encoding="UTF-8") as cf:
        config.read_file(cf)

    parser = argparse.ArgumentParser(description="Hash files and add info to database.")
    parser.add_argument(
        "--database", help="database to use", default=config.get("client", "database")
    )
    parser.add_argument(
        "--log-file",
        dest="log_file",
        help="logfile to use",
        default=config.get("client", "log"),
    )
    parser.add_argument("--folder", help="folder to query", default=None)
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


def remove_deleted_files(database: str, folder=None, dry_run: bool = False):
    dbs = anime.DatabaseSession(database, False)
    if folder:
        known_files = (
            dbs.session.query(anime.LocalFile)
            .filter(anime.LocalFile.directory.like(f"{folder.rstrip('/')}%"))
            .all()
        )
    else:
        known_files = dbs.session.query(anime.LocalFile).all()

    print(len(known_files))
    for known_file in known_files:
        if not os.path.isfile(known_file.full_path):
            print(f"###### removing {known_file.full_path}")
            if not dry_run:
                dbs.session.delete(known_file)
            else:
                print("##### INFO: dry-run requested, not removing deleted file")
        else:
            continue
    if not dry_run:
        dbs.session.commit()


if __name__ == "__main__":
    config = get_config()
    remove_deleted_files(
        database=config.database,
        folder=config.folder,
        dry_run=config.dry_run,
    )
