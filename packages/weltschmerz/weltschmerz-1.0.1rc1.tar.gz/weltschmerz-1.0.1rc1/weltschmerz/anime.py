try:
    from sqlalchemy.orm import declarative_base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Date,
    Boolean,
    ForeignKey,
    Index,
    Float,
    JSON,
    DateTime,
)
from sqlalchemy.orm import sessionmaker, relationship
import sqlalchemy.sql.functions
import os.path
import datetime
import re
import urllib.parse

Base = declarative_base()


class Episode(Base):
    __tablename__ = "episode"
    eid = Column(Integer, primary_key=True, default=None)
    aid = Column(Integer, ForeignKey("anime.aid"))
    ep = Column(String().with_variant(String(collation="numeric"), "postgresql"))
    airdate = Column(Date)
    length = Column(Integer)
    title_en = Column(String)
    title_jp = Column(String)
    title_jp_t = Column(String)
    last_update = Column(Date)
    anime = relationship("Anime", back_populates="episodes")
    screenshots = relationship("TitleScreenShot", lazy="immediate")


class AnimeTitle(Base):
    __tablename__ = "anime_title"
    aid = Column(Integer, ForeignKey("anime.aid"))
    type = Column(Integer, nullable=False, primary_key=True)
    lang = Column(String, nullable=False, primary_key=True)
    title = Column(String, nullable=False, primary_key=True)


class Anime(Base):
    __tablename__ = "anime"
    aid = Column(Integer, unique=True, primary_key=True, default=None)
    year = Column(String)
    type = Column(Integer)
    eps = Column(Integer)
    hep = Column(Integer)
    seps = Column(Integer)
    airdate = Column(Date)
    enddate = Column(Date)
    url = Column(String)
    picname = Column(String)
    rating = Column(Float)
    votecount = Column(Integer)
    tempvote = Column(Float)
    tempvcount = Column(Integer)
    avgreview = Column(Float)
    reviewcount = Column(Integer)
    hrestricted = Column(Boolean)
    count_sp = Column(Integer)
    count_other = Column(Integer)
    count_trailer = Column(Integer)
    count_parody = Column(Integer)
    last_update = Column(Date)
    episodes = relationship(Episode)  # lazy="immediate")

    @property
    def eps_total(self):
        return len(self.episodes)

    @property
    def runtime(self) -> int:
        return sum([episode.length for episode in self.episodes if episode.length])

    @property
    def screenshots(self):
        return sqlalchemy.sql.functions.sum(self.episodes.screenshots)


class File(Base):
    __tablename__ = "file"
    fid = Column(Integer, primary_key=True, default=None)
    filesize = Column(BigInteger, nullable=False)
    original_filename = Column(String)
    aid = Column(Integer, ForeignKey("anime.aid"))
    eid = Column(Integer, ForeignKey("episode.eid"))
    gid = Column(Integer)
    source = Column(String)
    video_codec = Column(String)
    resolution = Column(String)
    extension = Column(String)
    lang_audio = Column(String)
    lang_subs = Column(String)
    hash_crc = Column(String)
    hash_md5 = Column(String)
    hash_sha1 = Column(String)
    hash_tth = Column(String)
    hash_ed2k = Column(String, nullable=False)
    last_update = Column(DateTime(timezone=True), onupdate=datetime.datetime.now(datetime.timezone.utc))
    __table_args__ = (
        Index("idx_file_hash_ed2k", "hash_ed2k", "filesize", unique=True),
    )


class LocalFile(Base):
    __tablename__ = "local_file"
    filename = Column(
        String().with_variant(String(collation="numeric"), "postgresql"),
        nullable=False,
        primary_key=True,
    )
    directory = Column(
        String().with_variant(String(collation="numeric"), "postgresql"),
        nullable=False,
        primary_key=True,
    )
    filesize = Column(BigInteger, nullable=False)
    fid = Column(Integer, ForeignKey("file.fid"))
    aid = Column(Integer, ForeignKey("anime.aid"))
    hash_crc = Column(String)
    hash_md5 = Column(String)
    hash_sha1 = Column(String)
    hash_tth = Column(String)
    hash_ed2k = Column(String, nullable=False)
    mtime = Column(DateTime(timezone=True))
    # screenshots = relationship('TitleScreenShot', foreign_keys=['fid'], lazy="immediate")
    __table_args__ = (
        Index(
            "idx_local_file_path_size", "directory", "filename", "filesize", unique=True
        ),
        Index("idx_local_file_hash_ed2k", "hash_ed2k", "filesize", unique=False),
    )

    @property
    def ed2k_link(self) -> str:
        return f"ed2k://|file|{self.filename}|{self.filesize}|{self.hash_ed2k}|/"

    @property
    def full_path(self) -> str:
        return os.path.join(str(self.directory), str(self.filename))


class MylistFile(Base):
    __tablename__ = "mylist"
    fid = Column(Integer, ForeignKey("file.fid"), primary_key=True, nullable=False)
    ml_state = Column(Integer, nullable=False)
    ml_viewed = Column(Integer)
    ml_viewdate = Column(DateTime(timezone=True))
    ml_storage = Column(String)
    ml_source = Column(String)
    ml_other = Column(String)


class MylistAnime(Base):
    __tablename__ = "mylist_anime"
    aid = Column(Integer, ForeignKey("anime.aid"), nullable=False, primary_key=True)
    ml_count_episodes = Column(Integer)
    ml_count_specials = Column(Integer)
    ml_count_total = Column(Integer)
    ml_watched_episodes = Column(Integer)
    ml_watched_specials = Column(Integer)
    ml_watched_total = Column(Integer)

    @property
    def ml_watched_ratio_total(self) -> float:
        if 0 in [self.ml_watched_total, self.ml_count_total]:
            return 0
        else:
            return self.ml_watched_total / self.ml_count_total

    @property
    def ml_watched_ratio_episodes(self) -> float:
        if 0 in [self.ml_watched_episodes, self.ml_count_episodes]:
            return 0
        else:
            return self.ml_watched_episodes / self.ml_count_episodes

    @property
    def ml_watched_ratio_specials(self) -> float:
        if 0 in [self.ml_watched_specials, self.ml_count_specials]:
            return 0
        else:
            return self.ml_watched_specials / self.ml_count_specials


class TitleScreenShot(Base):
    __tablename__ = "title_screenshot"
    filename = Column(String, nullable=False, primary_key=True)
    aid = Column(Integer, ForeignKey("anime.aid"))
    eid = Column(Integer, ForeignKey("episode.eid"))
    fid = Column(Integer, ForeignKey("file.fid"))

    time_position = Column(String, nullable=False)
    time_position_raw = Column(Float, nullable=False)
    title_type = Column(Integer)
    source_file_source = Column(String)
    source_file_duration = Column(String)
    source_file_duration_raw = Column(Float)
    source_file_name = Column(String)
    source_file_size = Column(BigInteger, nullable=False)
    source_file_hash_crc = Column(String)
    source_file_hash_md5 = Column(String)
    source_file_hash_sha1 = Column(String)
    source_file_hash_tth = Column(String)
    source_file_hash_ed2k = Column(String, nullable=False)
    episode = relationship("Episode", back_populates="screenshots")

    @property
    def thumbnail_path(self) -> str:
        return re.match(r"^.*/by-id/(.*)\..*$", self.filename).groups()[0]

    @property
    def get_srcset(
        self,
        sizes=[256, 512],
        img_formats=["jxl", "avif", "webp", "jpeg"],
        basedir: str = "/thumbnails",
    ):
        file_base = re.match(r"^.*/(by-id/.*)\..*$", self.filename).groups()[0]
        srcset = []
        for img_format in img_formats:
            srcset.append(
                (
                    img_format,
                    ", ".join(
                        [
                            f"{basedir}/{size}x{size}/{urllib.parse.quote(file_base)}.{img_format} {size}w"
                            for size in sizes
                        ]
                    ),
                )
            )
        return srcset


class AnidbFileResponse(Base):
    __tablename__ = "anidb_file_response"
    hash_ed2k = Column(String, nullable=False, primary_key=True)
    filesize = Column(BigInteger, nullable=False, primary_key=True)
    fmask = Column(String, nullable=False, primary_key=True)
    famask = Column(String, nullable=False, primary_key=True)
    data = Column(JSON)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.datetime.now(datetime.timezone.utc))

    __table_args__ = (
        Index(
            "idx_anidb_file_response_hash_ed2k_filesize",
            "hash_ed2k",
            "filesize",
            unique=True,
        ),
    )


class DatabaseSession:
    def __init__(self, db="sqlite:///:memory:", echo=False):
        engine = create_engine(db, echo=echo)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()
