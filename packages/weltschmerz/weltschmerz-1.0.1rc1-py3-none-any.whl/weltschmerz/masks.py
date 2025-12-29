#!/usr/bin/python3

AMASK = (
    (
        [1, "int", "aid"],  # byte 1
        [0, "int", "dateflags"],
        [1, "str", "year"],
        [1, "str", "type"],
        [0, "str", "related aid list"],
        [0, "str", "related aid type"],
        [0, "str", "category list"],
        [0, "str", "category weight list"],
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
        [1, "int4", "episodes"],  # byte 3
        [1, "int4", "highest episode number"],
        [1, "int4", "special ep count"],
        [1, "int", "airdate"],
        [1, "int", "end date"],
        [0, "str", "url"],
        [0, "str", "picname"],
        [0, "str", "category id list"],
    ),
    (
        [0, "int4", "rating"],  # byte 4
        [0, "int", "vote count"],
        [0, "int4", "temp rating"],
        [0, "int", "temp vote count"],
        [0, "int4", "average review rating"],
        [0, "int", "review count"],
        [0, "str", "award list"],
        [1, "bool", "is 18+ restricted"],
    ),
    (
        [0, "int", "anime planet id"],  # byte 5
        [0, "int", "ANN id"],
        [0, "int", "allcinema id"],
        [0, "str", "AnimeNfo id"],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [1, "int", "date record updated"],
    ),
    (
        [0, "int", "character id list"],  # byte 6
        [0, "int", "creator id list"],
        [0, "int", "main creator id list"],
        [0, "str", "main creator name list"],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
    ),
    (
        [1, "int4", "specials count"],  # byte 7
        [1, "int4", "credits count"],
        [1, "int4", "other count"],
        [1, "int4", "trailer count"],
        [1, "int4", "parody count"],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
    ),
)
FMASK = (
    (
        [0, "", ""],  # byte 1
        [1, "int4", "aid"],
        [1, "int4", "eid"],
        [1, "int4", "gid"],
        [1, "int4", "mylist id"],
        [1, "list", "other episodes"],
        [1, "int2", "IsDeprecated"],
        [1, "int2", "state"],
    ),
    (
        [1, "int8", "size"],  # byte 2
        [1, "str", "ed2k"],
        [1, "str", "md5"],
        [1, "str", "sha1"],
        [1, "str", "crc32"],
        [0, "", ""],
        [0, "", "video color depth"],
        [0, "", ""],
    ),
    (
        [1, "str", "quality"],  # byte 3
        [1, "str", "source"],
        [1, "str", "audio codec list"],
        [1, "int4", "audio bitrate list"],
        [1, "str", "video codec"],
        [1, "int4", "video bitrate"],
        [1, "str", "video resolution"],
        [0, "str", "file type (extension)"],
    ),
    (
        [1, "str", "dub language"],  # byte 4
        [1, "str", "sub language"],
        [1, "int4", "length in seconds"],
        [1, "str", "description"],
        [1, "int4", "aired date"],
        [0, "", ""],
        [0, "", ""],
        [0, "str", "anidb file name"],
    ),
    (
        [0, "int4", "mylist state"],  # byte 5
        [0, "int4", "mylist filestate"],
        [0, "int4", "mylist viewed"],
        [0, "int4", "mylist viewdate"],
        [0, "str", "mylist storage"],
        [0, "str", "mylist source"],
        [0, "str", "mylist other"],
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
testmask = (
    (
        [0, "", ""],  # byte 1
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
    ),
    (
        [0, "", ""],  # byte 2
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
    ),
    (
        [0, "", ""],  # byte 3
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
    ),
    (
        [0, "", ""],  # byte 4
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
    ),
    (
        [0, "", ""],  # byte 5
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
    ),
    (
        [0, "", ""],  # byte 6
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
    ),
    (
        [0, "", ""],  # byte 7
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
    ),
    (
        [0, "", ""],  # byte 8
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
    ),
)
testmask_two = (
    (
        [1, "", ""],  # byte 1
        [1, "", ""],
        [0, "", ""],
        [0, "", ""],
        [0, "", ""],
        [1, "", ""],
        [0, "", ""],
        [1, "", ""],
    ),
)


def make_mask(mask):
    mask_bits = ""
    fields = []
    for byte in mask:
        total = ""
        for bit in byte:
            total += str(bit[0])
            if bit[0] == 1:
                fields.append(bit[2])
        mask_bits += f"{int(total, 2):b}".rjust(8, "0")

    mask_string = f"{int(mask_bits, 2):X}"
    return (mask_string, fields)


if __name__ == "__main__":
    # print(hexstring(testmask))
    print(make_mask(FMASK))
    print(make_mask(FAMASK))
