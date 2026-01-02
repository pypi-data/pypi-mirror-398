# pgnheaders.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Extract PGN headers from PGN files.

Convert all *.pgn files in the directory tree <directory>/pgn/ to *.pgnhdr
files in the directory tree <directory>/pgnhdr/.

The *.pgnhdr files have all the Tag Pairs for a game, plus the Game
Termination Marker, on a single line.  Thus each line is a valid game in
PGN format ignoring line formatting.

"""
import os
import re
import json

from . import constants

re_pgn_tag_pair = re.compile(constants.PGN_TAG_PAIR)


def extract_pgn_headers(path, json_=False):
    """Walk path tree creating a *.pgnhdr file for each *.pgn file.

    By default an existing *.pgnhdr file is not overwritten.

    Do nothing if path argument is not a directory or does not exist.

    The directory tree 'path/pgn/' is searched for *.pgn files and the
    *.pgnhdr files are put in the 'path/pgnhdr/' tree.

    *.pgn files are read in binary mode, open(<file>, mode="rb).  The tag
    name and tag value are decoded separately, trying utf-8 first and then
    iso-8859-1 with the latter expected to succeed always at the price of
    possibly not accurately representing the *.pgn file content.

    json_ determines if 'repr' or 'json.dumps' serializes the dict of tag
    key and tag values.  Default is False meaning use 'repr'.

    Games without a tag pair for key "Result", or with this tag pair but a
    value other than '1-0', '0-1', or '1/2-1/2', are ignored.

    """
    if not os.path.exists(path):
        return
    if not os.path.isdir(path):
        return
    pgnpath = os.path.join(path, constants.PGNDIR)
    if not os.path.exists(pgnpath):
        return
    if not os.path.isdir(pgnpath):
        return
    pgnhdrpath = os.path.join(path, constants.PGNHDRDIR)
    try:
        os.mkdir(pgnhdrpath)
    except FileExistsError:
        pass
    _extract_pgn_headers_from_directory(pgnpath, pgnhdrpath, json_)


def _extract_pgn_headers_from_directory(pgnpath, pgnhdrpath, json_):
    """Extract PGN headers from pgnpath and write to pgnhdrpath.

    pgnpath is a directory containing *.pgn files and subdirectories.
    pgnhdrpath is a directory containing *,pgnhdr files and subdirectories.
    json_ determines format: True means 'json' and False means 'repr'.

    """
    for entry in os.listdir(pgnpath):
        path = os.path.join(pgnpath, entry)
        if os.path.isdir(path):
            hdrpath = os.path.join(pgnhdrpath, entry)
            try:
                os.mkdir(hdrpath)
            except FileExistsError:
                pass
            _extract_pgn_headers_from_directory(path, hdrpath, json_)
        elif os.path.isfile(path):
            _extract_pgn_headers_from_file(
                path,
                os.path.join(
                    pgnhdrpath,
                    os.path.splitext(entry)[0] + constants.PGNHDREXT,
                ),
                json_,
            )


def _extract_pgn_headers_from_file(pgnpath, pgnhdrpath, json_):
    """Extract PGN headers from pgnpath and write to pgnhdrpath.

    pgnpath is a *.pgn file
    pgnhdrpath is a *,pgnhdr file
    json_ determines format: True means 'json' and False means 'repr'.

    """
    if os.path.exists(pgnhdrpath):
        if not os.path.isfile(pgnhdrpath):
            return
    if not os.path.isfile(pgnpath):
        return
    if not os.path.splitext(pgnpath)[1].lower() == constants.PGNEXT:
        return
    refbase = pgnpath.lstrip(os.path.expanduser("~") + os.path.sep)
    with open(pgnpath, mode="rb") as pgn:
        with open(pgnhdrpath, "w", encoding="utf-8") as pgnhdr:
            headers = {}
            reference = {constants.FILE: refbase, constants.GAME: 0}
            format_ = json.dumps if json_ else repr
            for line in pgn:
                line = line.strip()
                match_ = re_pgn_tag_pair.match(line)
                if match_:
                    tag, value = match_.groups()
                    try:
                        tag = tag.decode()
                    except UnicodeDecodeError:
                        tag = tag.decode(encoding="iso-8859-1")
                    try:
                        value = value.decode()
                    except UnicodeDecodeError:
                        value = value.decode(encoding="iso-8859-1")
                    headers[tag] = value
                    continue
                if not line and headers:
                    reference[constants.GAME] += 1
                    if (
                        headers.get(
                            constants.TAG_RESULT, constants.UNKNOWN_RESULT
                        )
                        != constants.UNKNOWN_RESULT
                    ):
                        pgnhdr.write(
                            format_((reference, headers)) + os.linesep
                        )
                    headers.clear()
