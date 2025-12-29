#!/usr/bin/python3

import os.path
import shutil
import pathlib
import weltschmerz.anime as anime
import configparser
import argparse
from typing import List


AID_PAD_WIDTH = 6
AID_CHUNK_SIZE = 2


def get_config(config_file: str = "weltschmerz.cfg"):
    config = configparser.ConfigParser()
    with open(config_file, "r", encoding="UTF-8") as cf:
        config.read_file(cf)

    parser = argparse.ArgumentParser(
        description="Move known local files to target directory."
    )
    parser.add_argument(
        "--database", help="database to use", default=config.get("client", "database")
    )
    parser.add_argument(
        "--source-basedirs",
        nargs="*",
        help="source folders to process",
        default=None,
        dest="source_basedirs",
    )
    parser.add_argument(
        "--target-basedir",
        help="target basedir to move files to",
        default=None,
        dest="target_basedir",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        help="dry-run, no moving files",
        default=False,
        dest="dry_run",
        action="store_true",
    )
    parser.add_argument(
        "--target-crc32",
        "-C",
        help="add crc32 to target filename",
        default=False,
        dest="target_crc32",
        action="store_true",
    )

    args = parser.parse_args()
    return args


def sort_files(
    database: str,
    source_basedirs: List[str],
    target_basedir: str,
    target_crc32: bool = False,
    dry_run: bool = False,
):
    dbs = anime.DatabaseSession(database, False)
    known_files = []
    for source_basedir in source_basedirs:
        known_files_folder = (
            dbs.session.query(anime.LocalFile)
            .join(anime.File, anime.LocalFile.hash_ed2k == anime.File.hash_ed2k)
            .filter(anime.LocalFile.directory.like(f"{source_basedir.rstrip('/')}%"))
            .all()
        )
        known_files += known_files_folder
        print(
            f"DEBUG: known files to sort in ({source_basedir}): {len(known_files_folder)}"
        )
    print(len(known_files))
    # sys.exit(0)
    for local_file in known_files:
        known_file = (
            dbs.session.query(anime.File)
            .filter(anime.File.hash_ed2k == local_file.hash_ed2k)
            .one()
        )
        aid_padded = str(known_file.aid).zfill(AID_PAD_WIDTH)
        aid_path = os.path.join(
            *[
                aid_padded[i : i + AID_CHUNK_SIZE]
                for i in range(0, AID_PAD_WIDTH, AID_CHUNK_SIZE)
            ]
        )
        target_dir = os.path.join(target_basedir, "by-id", aid_path)
        if local_file.directory not in [target_dir]:
            if os.path.isfile(local_file.full_path):
                print(
                    f'file not sorted yet "{local_file.filename}" is in "{local_file.directory}", should be "{target_dir}"'
                )
                if not os.path.isfile(os.path.join(target_dir, local_file.filename)):
                    pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)
                    print(
                        f'##### INFO: moving "{local_file.full_path}" to "{target_dir}"'
                    )
                    if not dry_run:
                        shutil.move(
                            os.path.join(local_file.directory, local_file.filename),
                            target_dir,
                        )
                        local_file.directory = target_dir
                        dbs.session.merge(local_file)
                        dbs.session.commit()
                    else:
                        print("##### INFO: dry-run requested, not moving file")
                else:
                    if target_crc32:
                        print(
                            f'##### INFO: moving "{local_file.full_path}" to "{target_dir}", adding CRC32 to the filename'
                        )
                        target_filename = (
                            local_file.filename[
                                : -len(local_file.filename.split(".")[-1]) - 1
                            ]
                            + f"[{local_file.hash_crc}].{local_file.filename.split('.')[-1]}"
                        )
                        print(f'##### INFO: target filename "{target_filename}"')
                        if not dry_run:
                            shutil.move(
                                os.path.join(local_file.directory, local_file.filename),
                                os.path.join(target_dir, target_filename),
                            )
                            local_file.directory = target_dir
                            local_file.filename = target_filename
                            dbs.session.merge(local_file)
                            dbs.session.commit()
                        else:
                            print("##### INFO: dry-run requested, not moving file")
                    else:
                        print(
                            f'##### WARNING: "{os.path.join(target_dir, local_file.filename)}" already present'
                        )


if __name__ == "__main__":
    config = get_config()
    sort_files(
        database=config.database,
        source_basedirs=config.source_basedirs,
        target_basedir=config.target_basedir,
        target_crc32=config.target_crc32,
        dry_run=config.dry_run,
    )
