#!/usr/bin/python3

import hashlib
import os.path
import zlib
import time
from Crypto.Hash import MD4
from threading import Thread, Semaphore
from io import BytesIO

BLOCKSIZE = 64 * 2**20


class T(Thread):
    def __init__(self, h, o):
        self.h = h
        self.o = o
        self.ready = Semaphore(0)
        self.idle = Semaphore(0)
        Thread.__init__(self)

    def run(self):
        while True:
            self.idle.release()
            self.ready.acquire()
            if not len(self.o[0]):
                return
            self.h.update(self.o[0])


class Crc32:
    def __init__(self):
        self.v = 0

    def update(self, x):
        self.v = zlib.crc32(x, self.v)

    def hexdigest(self):
        return "%08x" % (self.v & 0xFFFFFFFF)


class Ed2k:
    def __init__(self):
        self.block_size = 9728000
        try:
            self.md4chunk = hashlib.new("md4")
        except ValueError:
            self.md4chunk = MD4.new()
        self.md4chunk_pos = 0
        self.md4list = []

    def update(self, data=b""):
        data_length = len(data)
        b = BytesIO(data)
        pos = 0
        if data_length > 0:
            while pos < data_length:
                read_size = min(self.block_size - self.md4chunk_pos, data_length - pos)
                self.md4chunk.update(b.read(read_size))
                pos += read_size
                self.md4chunk_pos += read_size
                if self.block_size == self.md4chunk_pos:
                    self.md4list.append(self.md4chunk.digest())
                    self.md4chunk_pos = 0
                    try:
                        self.md4chunk = hashlib.new("md4")
                    except ValueError:
                        self.md4chunk = MD4.new()
        else:
            return
        b.close()

    def hexdigest(self):
        if len(self.md4list) > 0:
            try:
                return hashlib.new(
                    "md4", b"".join(self.md4list) + self.md4chunk.digest()
                ).hexdigest()
            except ValueError:
                return MD4.new(
                    b"".join(self.md4list) + self.md4chunk.digest()
                ).hexdigest()
        else:
            return self.md4chunk.hexdigest()


class FileHash:
    def __init__(self, directory: str, filename: str, block_size=BLOCKSIZE):
        self.directory: str = directory
        self.filename: str = filename
        self.block_size: int = block_size
        self.filesize: int = os.path.getsize(os.path.join(directory, filename))
        start = time.time()
        (self.crc32, self.md5, self.sha1, self.ed2k) = self.hash_file()
        end = time.time()
        self.hash_duration = end - start

    def hash_file(self):
        """Creates multiple hashes for a file in one go.

        Returns file name, size, crc32, md5, sha1, ed2k.
        Uses the red variant of ed2k. Info: http://wiki.anidb.net/w/Ed2k-hash
        """
        hashes = {
            "ed2k": Ed2k(),
            "sha1": hashlib.sha1(),
            "md5": hashlib.md5(),
            "crc32": Crc32(),
        }
        data = [b""]
        threads = [T(h, data) for n, h in hashes.items()]
        [t.start() for t in threads]
        with open(os.path.join(self.directory, self.filename), "rb") as f:
            while True:
                data.append(f.read(self.block_size))
                [t.idle.acquire() for t in threads]
                del data[0]
                [t.ready.release() for t in threads]
                if not len(data[0]):
                    break
        [t.join() for t in threads]
        return [hashes[h].hexdigest() for h in ["crc32", "md5", "sha1", "ed2k"]]

    def ed2k_link(self) -> str:
        return f"ed2k://|file|{self.filename}|{self.filesize}|{self.ed2k}|/"


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--stats", action="store_true", default=False)
    parser.add_argument(
        "-b", "--block-size", dest="block_size", type=int, default=BLOCKSIZE
    )
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()

    for file in args.files:
        try:
            file_info = FileHash(*os.path.split(file), block_size=args.block_size)
            print(file_info.ed2k_link())
            if args.stats:
                print(
                    "{} MiB/s".format(
                        file_info.filesize / 1048576.0 / file_info.hash_duration
                    ),
                    file=sys.stderr,
                )
        except IOError as err:
            print("error:", err, file=sys.stderr)
            sys.exit(1)
