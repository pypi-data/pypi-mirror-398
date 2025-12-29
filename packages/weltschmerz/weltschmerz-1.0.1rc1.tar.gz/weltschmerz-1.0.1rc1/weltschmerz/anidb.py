#!/usr/bin/python3

import configparser
import argparse
import re

import yumemi
import weltschmerz.anime as anime
import weltschmerz.masks as masks
import datetime
from typing import Optional, List, Any

CLIENT_NAME = "weltschmerz"
CLIENT_VERSION = 0
# request very few attributes from AniDB,
# results might not fit into the reply package otherwise,
# especially for files from episodes with long titles
FMASK = (
    (
        [0, "", ""],  # byte 1
        [1, "int4", "aid"],
        [1, "int4", "eid"],
        [1, "int4", "gid"],
        [1, "int4", "mylist id"],
        [1, "list", "other episodes"],
        [0, "int2", "IsDeprecated"],
        [1, "int2", "state"],
    ),
    (
        [0, "int8", "size"],  # byte 2
        [0, "str", "ed2k"],
        [0, "str", "md5"],
        [0, "str", "sha1"],
        [0, "str", "crc32"],
        [0, "", ""],
        [0, "", "video color depth"],
        [0, "", ""],
    ),
    (
        [1, "str", "quality"],  # byte 3
        [1, "str", "source"],
        [0, "str", "audio codec list"],
        [0, "int4", "audio bitrate list"],
        [0, "str", "video codec"],
        [0, "int4", "video bitrate"],
        [0, "str", "video resolution"],
        [1, "str", "file type (extension)"],
    ),
    (
        [0, "str", "dub language"],  # byte 4
        [0, "str", "sub language"],
        [0, "int4", "length in seconds"],
        [0, "str", "description"],
        [0, "int4", "aired date"],
        [0, "", ""],
        [0, "", ""],
        [0, "str", "anidb file name"],
    ),
    (
        [1, "int4", "mylist state"],  # byte 5
        [1, "int4", "mylist filestate"],
        [1, "int4", "mylist viewed"],
        [1, "int4", "mylist viewdate"],
        [1, "str", "mylist storage"],
        [1, "str", "mylist source"],
        [1, "str", "mylist other"],
        [0, "", ""],
    ),
)
FAMASK = (
    (
        [1, "int4", "anime total episodes"],  # byte 1
        [1, "", "highest episode number"],
        [0, "", "year"],
        [0, "", "type"],
        [0, "", "related aid list"],
        [0, "", "related aid type"],
        [0, "", "category list"],
        [0, "", ""],
    ),
    (
        [0, "str", "romaji name"],  # byte 2
        [0, "str", "kanji name"],
        [0, "str", "english name"],
        [0, "str", "other name"],
        [0, "str", "short name list"],
        [0, "str", "synonym list"],
        [0, "", ""],
        [0, "", ""],
    ),
    (
        [1, "str", "epno"],  # byte 3
        [1, "str", "ep name"],
        [1, "str", "ep romaji name"],
        [1, "str", "ep kanji name"],
        [0, "int4", "episode rating"],
        [0, "int4", "episode vote count"],
        [0, "", ""],
        [0, "", ""],
    ),
    (
        [1, "str", "group name"],  # byte 4
        [1, "str", "group short name"],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "int4", "date aid record updated"],
    ),
)


def get_config(config_file: str = "weltschmerz.cfg"):
    config = configparser.ConfigParser()
    with open(config_file, "r", encoding="UTF-8") as cf:
        config.read_file(cf)

    parser = argparse.ArgumentParser(description="Lookup files in AniDB.")
    parser.add_argument(
        "--database", help="database to use", default=config.get("client", "database")
    )
    parser.add_argument(
        "--debug",
        "-d",
        help="show debug output",
        default=False,
        dest="debug",
        action="store_true",
    )
    parser.add_argument(
        "--folders",
        nargs="*",
        help="folders to process",
        default=re.split(r"\s+", config.get("client", "folders", fallback="")),
    )
    parser.add_argument(
        "--online",
        "-O",
        help="whether to ask anidb about file info",
        default=False,
        dest="online",
        action="store_true",
    )
    parser.add_argument(
        "--add-to-mylist",
        "-M",
        help="whether to add known files to mylist",
        default=False,
        dest="add_to_mylist",
        action="store_true",
    )
    parser.add_argument(
        "--mylist-state",
        help="mylist state",
        default=config.get("anidb", "mylist_state"),
    )
    parser.add_argument(
        "--anidb-username",
        help="AniDB username",
        default=config.get("anidb", "username"),
    )
    parser.add_argument(
        "--anidb-password",
        help="AniDB password",
        default=config.get("anidb", "password"),
    )
    parser.add_argument(
        "--anidb-udp-api-key",
        help="AniDB UDP API Key",
        default=config.get("anidb", "udp_api_key"),
    )

    args = parser.parse_args()
    return args


class AniDBClient:
    def __init__(
        self,
        local_database: str,
        local_database_verbose: bool = False,
        fmask=masks.FMASK,
        famask=masks.FAMASK,
        online: bool = False,
        anidb_username: Optional[str] = None,
        anidb_password: Optional[str] = None,
        anidb_udp_api_key: Optional[str] = None,
        mylist_state: int = 4,
        debug: bool = False,
    ):
        (self.fmask_string, self.fmask_fields) = masks.make_mask(fmask)
        (self.famask_string, self.famask_fields) = masks.make_mask(famask)
        self.dbs = anime.DatabaseSession(local_database, local_database_verbose)
        self.online = online
        self.client = None
        self.anidb_username = anidb_username
        self.anidb_password = anidb_password
        self.anidb_udp_api_key = anidb_udp_api_key
        self.mylist_state = mylist_state
        self.debug = debug

    def go_online(self):
        if not self.client:
            if self.anidb_username and self.anidb_password and self.online:
                self.client = yumemi.Client(CLIENT_NAME, CLIENT_VERSION)
                if self.anidb_udp_api_key:
                    self.client.encrypt(self.anidb_username, self.anidb_udp_api_key)
                result = self.client.auth(self.anidb_username, self.anidb_password)
                result_encoding = self.client.command("ENCODING", {"name": "UTF-8"})
                if self.debug:
                    print("DEBUG: ", result.code, result.message)
                    print("DEBUG: ", result_encoding.code, result_encoding.message)
            else:
                raise ValueError

    def add_file_to_mylist(
        self,
        # state:
        # 0 - unknown - state is unknown or the user doesn't want to provide this information
        # 1 - internal storage - the file is stored on hdd (but is not shared)
        # 2 - external storage - the file is stored on cd/dvd/...
        # 3 - deleted - the file has been deleted or is not available for other reasons (i.e. reencoded)
        # 4 - remote storage - the file is stored on NAS/cloud/...
        state: int = 4,
        file_size: Optional[int] = None,
        hash_ed2k: Optional[str] = None,
        file_id: Optional[int] = None,
        viewed: Optional[bool] = None,
        viewdate: Optional[str] = None,
        source: Optional[str] = None,
        storage: Optional[str] = None,
        other: Optional[str] = None,
    ) -> dict:
        if not ((file_size and hash_ed2k) or file_id):
            raise ValueError
        if file_size and file_size >= 100000000000:
            print(f"WARN: Adding to mylist failed for {hash_ed2k}: file too large")
            return {}
        if self.online:
            ##############
            # ask AniDB
            ##############
            try:
                params: Optional[dict[str, Any]] = None
                result = {}
                if file_id:
                    params = {"fid": file_id}
                else:
                    params = {
                        "size": file_size,
                        "ed2k": hash_ed2k,
                    }
                if state:
                    params["state"] = state
                if viewed:
                    params["viewed"] = viewed
                if viewdate:
                    params["viewdate"] = viewdate
                if source:
                    params["source"] = source
                if storage:
                    params["storage"] = storage
                if other:
                    params["other"] = other
                if self.debug:
                    print(f"DEBUG: {params}")
                self.go_online()
                if self.client:
                    result = self.client.command(
                        "MYLISTADD",
                        params,
                    )
                    if self.debug:
                        print(f"DEBUG: {result.data[0]}")
                    if result.code == 210:  # mylist entry added
                        mylist_file = None
                        if file_id:
                            mylist_file = anime.MylistFile(
                                fid=file_id,
                            )
                        else:
                            anidb_file = (
                                self.dbs.session.query(anime.File)
                                .filter(anime.AnidbFileResponse.hash_ed2k == hash_ed2k)
                                .filter(anime.AnidbFileResponse.filesize == file_size)
                                .first()
                            )
                            if anidb_file:
                                mylist_file = anime.MylistFile(
                                    fid=anidb_file.fid,
                                )
                        if mylist_file:
                            if state:
                                mylist_file.ml_state = state
                            if viewed:
                                mylist_file.ml_viewed = viewed
                            if viewdate:
                                mylist_file.ml_viewdate = viewdate
                            if source:
                                mylist_file.ml_source = source
                            if storage:
                                mylist_file.ml_storage = storage
                            if other:
                                mylist_file.ml_other = other
                            # ml_state=file["mystate"]["@id"],
                            # ml_viewed=file["state"]["iswatched"],
                            # ml_viewdate=view_date,
                            # ml_storage=file["storage"],
                            # ml_source=file["source"],
                            self.dbs.session.merge(mylist_file)
                            self.dbs.session.commit()
                        elif result.code == 310:  # file already in mylist
                            mylist_data = dict(
                                zip(
                                    [
                                        "lid",
                                        "fid",
                                        "eid",
                                        "aid",
                                        "gid",
                                        "date",
                                        "state",
                                        "viewdate",
                                        "storage",
                                        "source",
                                        "other",
                                        "filestate",
                                    ],
                                    result.data[0],
                                )
                            )
                            if int(mylist_data["viewdate"]) > 0:
                                viewdate = datetime.datetime.fromtimestamp(
                                    int(mylist_data["viewdate"])
                                )
                                viewed = True
                            else:
                                viewdate = None
                                viewed = None
                            mylist_file = anime.MylistFile(
                                fid=int(mylist_data["fid"]),
                                ml_state=int(mylist_data["state"]),
                                ml_viewed=viewed,
                                ml_viewdate=viewdate,
                                ml_storage=mylist_data["storage"],
                                ml_source=mylist_data["source"],
                                ml_other=mylist_data["other"],
                            )
                            self.dbs.session.merge(mylist_file)
                            self.dbs.session.commit()
                        return result

            except yumemi.exceptions.ServerError as e:
                if file_id:
                    file_info = f"file id {file_id}"
                else:
                    file_info = f"{hash_ed2k} / {file_size}"
                print(f"WARN: Adding to mylist failed for {file_info}: {type(e)}")
                self.dbs.session.commit()
                return {}
            except Exception as e:
                if file_id:
                    file_info = f"file id {file_id}"
                else:
                    file_info = f"{hash_ed2k} / {file_size}"
                print(f"WARN: Adding to mylist failed for {file_info}: {type(e)}")
                self.dbs.session.commit()
                raise
        return {}

    def lookup_file(self, file_size: int, hash_ed2k: str) -> dict:
        file_data = {}
        if file_size >= 100000000000:
            print(f"WARN: File is too big for UDP API {hash_ed2k} / {file_size}")
            return file_data
        ##############
        # try cache
        ##############
        cached_response = (
            self.dbs.session.query(anime.AnidbFileResponse)
            .filter(anime.AnidbFileResponse.hash_ed2k == hash_ed2k)
            .filter(anime.AnidbFileResponse.filesize == file_size)
            .first()
        )
        if cached_response:
            file_data = cached_response.data
            if self.debug:
                print(f"DEBUG: cached file data found {file_data}")
        if self.online and not cached_response:
            ##############
            # ask AniDB
            ##############
            try:
                self.go_online()
                result = self.client.command(
                    "FILE",
                    {
                        "size": file_size,
                        "ed2k": hash_ed2k,
                        "fmask": self.fmask_string,
                        "amask": self.famask_string,
                    },
                )
                if self.debug:
                    print(result.code, result.message)
                if result.code == 220:  # file found
                    requested_fields = self.fmask_fields + self.famask_fields
                    # "fid is always returned as the first value, regardless of what masks are provided."
                    file_data = dict(zip(["fid"] + requested_fields, result.data[0]))
            except yumemi.exceptions.ServerError as e:
                print(
                    f"WARN: AniDB lookup failed for {hash_ed2k} / {file_size}: {type(e)}"
                )
                self.dbs.session.commit()
                return file_data
            except Exception as e:
                print(
                    f"WARN: AniDB lookup failed for {hash_ed2k} / {file_size}: {type(e)}"
                )
                self.dbs.session.commit()
                raise
            # persist new cached response
            anidb_file_response = anime.AnidbFileResponse(
                hash_ed2k=hash_ed2k,
                filesize=file_size,
                fmask=self.fmask_string,
                famask=self.famask_string,
                data=file_data,
                updated_at=datetime.datetime.now(datetime.timezone.utc),
            )
            self.dbs.session.merge(anidb_file_response)
            self.dbs.session.commit()
        if len(file_data.keys()) > 0:
            if self.debug:
                print(f"DEBUG: file data found {file_data}")

            # update local DB from data
            local_db_anime = anime.Anime(
                aid=file_data["aid"],
                last_update=datetime.datetime.now(datetime.timezone.utc),
            )
            self.dbs.session.merge(local_db_anime)
            local_db_episode = anime.Episode(
                eid=file_data["eid"],
                aid=file_data["aid"],
                ep=file_data["epno"],
                title_en=file_data["ep name"],
                title_jp=file_data["ep kanji name"],
                title_jp_t=file_data["ep romaji name"],
                last_update=datetime.datetime.now(datetime.timezone.utc),
            )
            self.dbs.session.merge(local_db_episode)
            local_db_file = anime.File(
                fid=file_data["fid"],
                filesize=file_size,
                aid=file_data["aid"],
                eid=file_data["eid"],
                gid=file_data["gid"],
                source=file_data["source"],
                extension=file_data["file type (extension)"],
                hash_ed2k=hash_ed2k,
                last_update=datetime.datetime.now(datetime.timezone.utc),
            )
            self.dbs.session.merge(local_db_file)
            self.dbs.session.commit()
        return file_data


def lookup_files(
    database: str,
    database_verbose: bool = False,
    fmask=FMASK,
    famask=FAMASK,
    online: bool = False,
    anidb_username: Optional[str] = None,
    anidb_password: Optional[str] = None,
    anidb_udp_api_key: Optional[str] = None,
    add_to_mylist: bool = False,
    mylist_state: int = 4,
    debug: bool = False,
    folders: List[str] = ["/"],
):
    adbc = AniDBClient(
        local_database=database,
        local_database_verbose=database_verbose,
        fmask=fmask,
        famask=famask,
        online=online,
        anidb_username=anidb_username,
        anidb_password=anidb_password,
        anidb_udp_api_key=anidb_udp_api_key,
        mylist_state=mylist_state,
        debug=debug,
    )
    unknown_files = []
    for folder in folders:
        unknown_files_folder_query = (
            adbc.dbs.session.query(anime.LocalFile)
            .filter(anime.LocalFile.directory.like(f"{folder.rstrip('/')}%"))
            .filter((anime.LocalFile.fid == None) | (anime.LocalFile.aid == None))
        )
        if online:
            unknown_files_folder_query = unknown_files_folder_query.join(
                anime.AnidbFileResponse,
                anime.LocalFile.hash_ed2k == anime.AnidbFileResponse.hash_ed2k,
                isouter=True,
            ).filter(anime.AnidbFileResponse.hash_ed2k == None)
        else:
            unknown_files_folder_query = unknown_files_folder_query.join(
                anime.AnidbFileResponse,
                anime.LocalFile.hash_ed2k == anime.AnidbFileResponse.hash_ed2k,
                isouter=False,
            ).filter(anime.AnidbFileResponse.data == None)

        unknown_files_folder = unknown_files_folder_query.all()
        unknown_files += unknown_files_folder
        print(
            f"DEBUG: unknown files to look up ({folder}): {len(unknown_files_folder)}"
        )
    print(f"INFO: unknown files to look up: {len(unknown_files)}")

    known_files = []
    for i, unknown_file in enumerate(unknown_files, start=1):
        if debug:
            print(f"DEBUG: {i}/{len(unknown_files)}")
        known_file = (
            adbc.dbs.session.query(anime.File)
            .join(anime.LocalFile, anime.LocalFile.hash_ed2k == anime.File.hash_ed2k)
            .filter(anime.File.hash_ed2k == unknown_file.hash_ed2k)
            .first()
        )
        if known_file:
            print(f"INFO: found file {known_file.fid}")
            unknown_file.fid = known_file.fid
            unknown_file.aid = known_file.aid
            known_files.append(unknown_file)
            if add_to_mylist and online:
                mylist_file = (
                    adbc.dbs.session.query(anime.MylistFile)
                    .filter(anime.MylistFile.fid == unknown_file.fid)
                    .first()
                )
                # add file to mylist of not in there yet
                if not mylist_file:
                    result = adbc.add_file_to_mylist(
                        file_id=unknown_file.fid,
                        state=adbc.mylist_state,
                    )

        elif online:
            anidb_result = adbc.lookup_file(
                unknown_file.filesize,
                unknown_file.hash_ed2k,
            )
            if "fid" in anidb_result.keys():
                unknown_file.aid = anidb_result["aid"]
                unknown_file.fid = anidb_result["fid"]
                if add_to_mylist:
                    result = adbc.add_file_to_mylist(
                        file_id=anidb_result["fid"],
                        state=adbc.mylist_state,
                    )
        if i % 10 == 0 and len(adbc.dbs.session.dirty) > 0:
            if debug:
                print("DEBUG: comitting...")
            adbc.dbs.session.commit()
    adbc.dbs.session.commit()
    if adbc.online and adbc.client:
        adbc.client.logout()


if __name__ == "__main__":
    config = get_config()
    lookup_files(
        database=config.database,
        database_verbose=config.database_verbose,
        online=config.online,
        anidb_username=config.anidb_username,
        anidb_password=config.anidb_password,
        anidb_udp_api_key=config.anidb_udp_api_key,
        add_to_mylist=config.add_to_mylist,
        mylist_state=config.mylist_state,
        debug=config.debug,
        folders=config.folders,
    )
