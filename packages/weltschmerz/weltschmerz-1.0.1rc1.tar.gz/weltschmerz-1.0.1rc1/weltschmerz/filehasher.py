#!/usr/bin/python3

import weltschmerz.anime as anime
import weltschmerz.filehash as filehash
import os
import re
import configparser
import argparse
import logging
import datetime
from typing import List
from itertools import islice


def get_config(config_file="weltschmerz.cfg"):
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
    parser.add_argument(
        "--folders",
        nargs="*",
        help="folders to process",
        default=re.split(r"\s+", config.get("client", "folders", fallback="")),
    )
    parser.add_argument(
        "--folders-exclude",
        dest="folders_exclude",
        nargs="*",
        help="folders to exclude",
        default=re.split(r"\s+", config.get("client", "folders_exclude")),
    )
    parser.add_argument(
        "--foldernames-exclude",
        dest="foldernames_exclude",
        nargs="*",
        help="foldernames to exclude",
        default=re.split(r"\s+", config.get("client", "foldernames_exclude")),
    )
    parser.add_argument(
        "--extensions",
        nargs="*",
        help="folders to process",
        default=re.split(r"\s+", config.get("client", "fileextensions")),
    )

    args = parser.parse_args()
    logging.basicConfig(
        filename=args.log_file,
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.DEBUG,
    )
    return args


class FileHasher:
    def __init__(self, db="sqlite:///:memory:", echo=False):
        self.dbs = anime.DatabaseSession(db, echo)
        self.files = []

    def _batched(self, iterable, n):
        it = iter(iterable)
        while True:
            batch = list(islice(it, n))
            if not batch:
                return
            yield batch

    def get_files(self, folders, folders_exclude, foldernames_exclude, exts):
        files = {}
        for path in folders:
            logging.info("".join(("Scanning for files: ", path)))
            for dirpath, dirnames, filenames in os.walk(path, topdown=True):
                dirnames[:] = [
                    d
                    for d in dirnames
                    if not (
                        os.path.join(dirpath, d).startswith(tuple(folders_exclude))
                        or d in foldernames_exclude
                        or not d.encode("utf-8", errors="replace")
                    )
                ]
                filenames[:] = [
                    f
                    for f in filenames
                    if f.casefold().endswith(tuple(exts))
                    and f.encode("utf-8", errors="replace")
                ]
                print(
                    f"{dirpath.encode('utf-8', errors='replace').decode('utf-8')}: {len(set(filenames))}"
                )
                for filename in filenames:
                    real_path = os.path.realpath(os.path.abspath(dirpath))
                    full_path = os.path.join(real_path, filename)
                    try:
                        full_path.encode("utf-8")
                    except UnicodeEncodeError as e:
                        logging.warning(f"Skipping a file: {e}")
                        continue
                    if (
                        real_path in files.keys()
                        and filename in files[real_path]["files_to_hash"]
                    ):
                        continue
                    elif os.path.islink(full_path):
                        continue
                    else:
                        if real_path not in files.keys():
                            files[real_path] = {
                                "known_files": [],
                                "files_to_hash": [filename],
                            }
                        else:
                            files[real_path]["files_to_hash"].append(filename)
                        # print(f"found {os.path.join(real_path, filename)}")
                        # files.append((real_path, filename))

        # check hashed files for the folders in batches to reduce complexity of the SQL query
        for batch in self._batched(files.keys(), 1000):
            for kf in (
                self.dbs.session.query(anime.LocalFile)
                .filter(anime.LocalFile.directory.in_(batch))
                .all()
            ):
                files[kf.directory]["known_files"].append(kf.filename)
        return files


def hash_files(
    database: str,
    folders: List[str],
    folders_exclude: List[str],
    foldernames_exclude: List[str],
    file_extensions: List[str],
):
    hasher = FileHasher(database, False)
    files: dict[str, List[str]] = hasher.get_files(
        folders,
        folders_exclude,
        foldernames_exclude,
        file_extensions,
    )
    for directory, data in files.items():
        to_hash = list(set(data["files_to_hash"]).difference(data["known_files"]))
        print(
            f"{directory}: {len(data['files_to_hash'])} file(s) found / {len(data['known_files'])} known - {len(to_hash)} to hash"
        )
        for filename in to_hash:
            if filename in data["known_files"]:
                continue
            fhash = filehash.FileHash(directory, filename)
            mtime_raw = os.path.getmtime(os.path.join(directory, filename))
            mtime = datetime.datetime.fromtimestamp(mtime_raw, tz=datetime.timezone.utc)
            lf = anime.LocalFile(
                filename=fhash.filename,
                directory=fhash.directory,
                filesize=fhash.filesize,
                hash_crc=fhash.crc32,
                hash_md5=fhash.md5,
                hash_sha1=fhash.sha1,
                hash_ed2k=fhash.ed2k,
                mtime=mtime,
            )
            known_file = (
                hasher.dbs.session.query(anime.File)
                .join(
                    anime.LocalFile, anime.LocalFile.hash_ed2k == anime.File.hash_ed2k
                )
                .filter(anime.File.hash_ed2k == lf.hash_ed2k)
                .all()
            )
            if len(known_file) == 1:
                lf.fid = known_file[0].fid
                lf.aid = known_file[0].aid
            print(f"{lf.filename}: {lf.hash_crc}")
            hasher.dbs.session.merge(lf)
            hasher.dbs.session.commit()


if __name__ == "__main__":
    config = get_config()
    hash_files(
        database=config.database,
        folders=config.folders,
        folders_exclude=config.folders_exclude,
        foldernames_exclude=config.foldernames_exclude,
        file_extensions=config.extensions,
    )
