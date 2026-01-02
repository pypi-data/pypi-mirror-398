# gamerecord.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Record definition classes for PGN tag data from games in PGN files."""

import os

from solentware_base.core.record import KeyData
from solentware_base.core.record import ValueList, Record
from solentware_base.core.segmentsize import SegmentSize

from pgn_read.core import tagpair_parser

from . import filespec
from . import constants

_NO_OPPONENT = frozenset(
    (constants.BYE_TERMINATION, constants.DEFAULT_TERMINATION)
)
_NO_PLAYER = frozenset((constants.UNKNOWN_VALUE, constants.NO_VALUE))
_RATINGTYPE = {
    constants.TAG_TIMECONTROL: filespec.GAME_TIMECONTROL_FIELD_DEF,
    constants.TAG_MODE: filespec.GAME_MODE_FIELD_DEF,
    constants.TAG_TERMINATION: filespec.GAME_TERMINATION_FIELD_DEF,
    constants.TAG_WHITETYPE: filespec.GAME_PLAYERTYPE_FIELD_DEF,
    constants.TAG_BLACKTYPE: filespec.GAME_PLAYERTYPE_FIELD_DEF,
}


class GameDBvalueError(Exception):
    """Raise if certain file names are given for index packing."""


class GameDBkey(KeyData):
    """Primary key of game."""


class GameDBvalue(ValueList):
    """Game header data.

    All import stages where data is copied to another file are indexed.

    The PGN file name and game number within file are recorded.

    All the PGN tag name and value pairs are recorded.  The tag names
    of interest for game selection are: Result, Date, TimeControl, Mode,
    Termination, BlackType, and WhiteType.

    Result and Date are in the Seven Tag Roster and games are rejected if
    these are missing.

    The others are usually absent but are critical to deciding if a game
    should be included in a performance calculation.  They determine if a
    game is standard, rapid, or blitz; 'over the board' or online, a
    ratable result or a bye or default, human or computer players.  A copy
    of these PGN tags is kept, along with the game value, for modification
    as needed for calculation control.

    Other tag names are relevant for identifying the event and players
    of the white and black pieces.  These are listed in the PlayerDBvalue
    class.
    """

    attributes = {
        "reference": None,  # dict of PGN file name and game number in file.
        "headers": None,  # dict of PGN tag name and value pairs for game.
    }
    _attribute_order = ("headers", "reference")
    assert set(_attribute_order) == set(attributes)

    def pack(self):
        """Extend, return game record and index data."""
        val = super().pack()
        self.pack_detail(val[1])
        return val

    def pack_detail(self, index):
        """Fill index with detail from value.

        Some 'gamestatus' indicies are generated: the ones indicating
        that the 'player', 'event', 'time', and 'mode', files have not
        been populated.  But it is an error if self.status contains
        these references.

        """
        for attr, defn in (
            (constants.FILE, filespec.GAME_PGNFILE_FIELD_DEF),
            (constants.GAME, filespec.GAME_NUMBER_FIELD_DEF),
        ):
            data = self.reference.get(attr)
            if data is not None:
                index[defn] = [data]
            else:
                index[defn] = []
        headers = self.headers
        for attr, defn in (
            (constants.TAG_TIMECONTROL, filespec.GAME_TIMECONTROL_FIELD_DEF),
            (constants.TAG_MODE, filespec.GAME_MODE_FIELD_DEF),
            (constants.TAG_TERMINATION, filespec.GAME_TERMINATION_FIELD_DEF),
        ):
            data = headers.get(attr)
            if data is not None:
                index[defn] = [data]
            else:
                index[defn] = []
        index[filespec.GAME_PLAYERTYPE_FIELD_DEF] = []
        for attr in (constants.TAG_BLACKTYPE, constants.TAG_WHITETYPE):
            data = headers.get(attr)
            if data is not None:
                index[filespec.GAME_PLAYERTYPE_FIELD_DEF].append(data)
        index[filespec.GAME_PLAYER_FIELD_DEF] = [
            self.black_key(),
            self.white_key(),
        ]
        index[filespec.GAME_EVENT_FIELD_DEF] = [
            repr(
                (
                    headers.get(constants.TAG_EVENT),
                    headers.get(constants.TAG_EVENTDATE),
                    headers.get(constants.TAG_SECTION),
                    headers.get(constants.TAG_STAGE),
                )
            ),
        ]
        index[filespec.GAME_NAME_FIELD_DEF] = [
            headers.get(constants.TAG_EVENT)
        ]
        index[filespec.GAME_DATE_FIELD_DEF] = [headers.get(constants.TAG_DATE)]

    def black_key(self):
        """Return the black key for the gameplayer index."""
        headers = self.headers
        return repr(
            (
                headers.get(constants.TAG_BLACK),
                headers.get(constants.TAG_EVENT),
                headers.get(constants.TAG_EVENTDATE),
                headers.get(constants.TAG_SECTION),
                headers.get(constants.TAG_STAGE),
                headers.get(constants.TAG_BLACKTEAM),
                headers.get(constants.TAG_BLACKFIDEID),
                headers.get(constants.TAG_BLACKTYPE),
            )
        )

    def white_key(self):
        """Return the white key for the gameplayer index."""
        headers = self.headers
        return repr(
            (
                headers.get(constants.TAG_WHITE),
                headers.get(constants.TAG_EVENT),
                headers.get(constants.TAG_EVENTDATE),
                headers.get(constants.TAG_SECTION),
                headers.get(constants.TAG_STAGE),
                headers.get(constants.TAG_WHITETEAM),
                headers.get(constants.TAG_WHITEFIDEID),
                headers.get(constants.TAG_WHITETYPE),
            )
        )

    def __eq__(self, other):
        """Return True if attributes of self and other are same."""
        sdict = self.__dict__
        odict = other.__dict__
        if len(sdict) != len(odict):
            return False
        for item in sdict:
            if item not in odict:
                return False
            if not isinstance(sdict[item], type(odict[item])):
                return False
            if sdict[item] != odict[item]:
                return False
        return True

    def __ge__(self, other):
        """Return True always (consistent with __gt__)."""
        return True

    def __gt__(self, other):
        """Return True if __ne__ is True."""
        return self.__ne__(other)

    def __le__(self, other):
        """Return True always (consistent with __lt__)."""
        return True

    def __lt__(self, other):
        """Return True if __ne__ is True."""
        return self.__ne__(other)

    def __ne__(self, other):
        """Return True if attributes of self and other are different."""
        sdict = self.__dict__
        odict = other.__dict__
        if len(sdict) != len(odict):
            return True
        for item in sdict:
            if item not in odict:
                return True
            if not isinstance(sdict[item], type(odict[item])):
                return True
            if sdict[item] != odict[item]:
                return True
        return False


class GameDBrecord(Record):
    """Game record."""

    def __init__(self, keyclass=GameDBkey, valueclass=GameDBvalue):
        """Customise Record with ResultsDBkeyGame and ResultsDBvalueGame."""
        super().__init__(keyclass, valueclass)

    def get_keys(self, datasource=None, partial=None):
        """Override, return [(key, value)] for datasource or []."""
        try:
            if partial is not None:
                return []
            srkey = datasource.dbhome.encode_record_number(self.key.pack())
            if datasource.primary:
                return [(srkey, self.srvalue)]
            dbname = datasource.dbname
            if dbname == filespec.GAME_DATE_FIELD_DEF:
                return [(self.value.headers["Date"], srkey)]
            if dbname == filespec.GAME_NUMBER_FIELD_DEF:
                return [
                    (
                        repr(
                            (
                                self.value.reference["file"],
                                self.value.reference["game"],
                            )
                        ),
                        srkey,
                    )
                ]
            if dbname == filespec.GAME_TIMECONTROL_FIELD_DEF:
                return [(self.value.headers["TimeControl"], srkey)]
            if dbname == filespec.GAME_MODE_FIELD_DEF:
                return [(self.value.headers["Mode"], srkey)]
            if dbname == filespec.GAME_NAME_FIELD_DEF:
                return [(self.value.headers["Event"], srkey)]
            return []
        except:  # pycodestyle E722: pylint is happy with following 'raise'.
            if datasource is None:
                return []
            raise


class GameDBImporter(GameDBrecord):
    """Extend with methods to import multiple game headers from PGN files."""

    def import_pgn_headers(
        self,
        database,
        path,
        reporter=None,
        quit_event=None,
    ):
        """Return True if import to database of PGN files in path succeeds.

        Games without a tag pair for tag name "Result", or with this tag
        pair but a tag value other than '1-0', '0-1', or '1/2-1/2', are
        ignored.

        Do nothing and return False if path argument is not a directory or
        does not exist.

        *.pgn files are read trying utf-8 first and then iso-8859-1 with
        the latter expected to succeed always possibly not accurately
        representing the *.pgn file content.

        quit_event allows the import to be interrupted by passing an Event
        instance which get queried after processing each game.

        """
        if not os.path.exists(path):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(path + " does not exist")
            return False
        if not os.path.isdir(path):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(path + " is not a directory")
            return False
        self.value.headers = {}
        self.value.reference = {}
        done_ok = self._extract_pgn_headers_from_directory(
            database, path, reporter, quit_event
        )
        if reporter is not None:
            reporter.append_text_only("")
        return done_ok

    def count_pgn_games(
        self,
        database,
        path,
        reporter=None,
        quit_event=None,
    ):
        """Return number of games in files or False.

        Games without a tag pair for tag name "Result", or with this tag
        pair but a tag value other than '1-0', '0-1', or '1/2-1/2', are
        ignored.

        Do nothing and return False if path argument is not a directory or
        does not exist.

        *.pgn files are read trying utf-8 first and then iso-8859-1 with
        the latter expected to succeed always possibly not accurately
        representing the *.pgn file content.

        quit_event allows the import to be interrupted by passing an Event
        instance which get queried after processing each game.

        """
        if not os.path.exists(path):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(path + " does not exist")
            return False
        if not os.path.isdir(path):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(path + " is not a directory")
            return False
        done_ok = self._count_pgn_games_in_directory(
            database, path, reporter, quit_event
        )
        if reporter is not None:
            reporter.append_text_only("")
        return done_ok

    def _process_pgn_headers_from_directory(
        self, database, pgnpath, reporter, quit_event
    ):
        """Extract PGN headers from directories and *.pgn files in pgnpath."""
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text("Processing files in " + pgnpath)
        for entry in os.listdir(pgnpath):
            path = os.path.join(pgnpath, entry)
            if os.path.isfile(path):
                if not self._extract_pgn_headers_from_file(
                    database, path, reporter, quit_event
                ):
                    return False
        for entry in os.listdir(pgnpath):
            path = os.path.join(pgnpath, entry)
            if os.path.isdir(path):
                if not self._extract_pgn_headers_from_directory(
                    database, path, reporter, quit_event
                ):
                    return False
        return True

    def _process_pgn_games_from_directory(
        self, database, pgnpath, reporter, quit_event
    ):
        """Count games in directories and *.pgn files in pgnpath."""
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text("Processing files in " + pgnpath)
        directory_count = 0
        for entry in os.listdir(pgnpath):
            path = os.path.join(pgnpath, entry)
            if os.path.isfile(path):
                count = self._count_pgn_games_in_file(
                    database, path, reporter, quit_event
                )
                if count is None:
                    return False
                directory_count += count
        for entry in os.listdir(pgnpath):
            path = os.path.join(pgnpath, entry)
            if os.path.isdir(path):
                count = self._count_pgn_games_in_directory(
                    database, path, reporter, quit_event
                )
                if count is None:
                    return False
                directory_count += count
        return directory_count

    def _extract_pgn_headers_from_directory(
        self, database, pgnpath, reporter, quit_event
    ):
        """Search directory pgnpath for *.pgn files and extract headers."""
        return self._process_pgn_headers_from_directory(
            database,
            pgnpath,
            reporter,
            quit_event,
        )

    # Probably needed only by DPT database engine.
    # Probably only in this class to use _process_pgn_headers_from_directory
    # machinery and from similarity to copy_* classes.
    def _count_pgn_games_in_directory(
        self, database, pgnpath, reporter, quit_event
    ):
        """Search directory tree pgnpath for *.pgn files and count games."""
        return self._process_pgn_games_from_directory(
            database,
            pgnpath,
            reporter,
            quit_event,
        )

    @staticmethod
    def _is_file_pgn_ext(pgnpath, reporter):
        """Return True if pgnpath is a PGN file."""
        if not os.path.isfile(pgnpath):
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(pgnpath + " is not a file")
                reporter.append_text_only("")
            return False
        if not os.path.splitext(pgnpath)[1].lower() == constants.PGNEXT:
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(
                    pgnpath + " is not a " + constants.PGNEXT + " file"
                )
                reporter.append_text_only("")
            return False
        return True

    def _extract_pgn_headers_from_file(
        self, database, pgnpath, reporter, quit_event
    ):
        """Return True if import succeeds or pgnpath is not a PGN file."""
        del quit_event
        if not self._is_file_pgn_ext(pgnpath, reporter):
            return True
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                "Extracting game headers from " + os.path.basename(pgnpath)
            )

        # Maybe /home is symlink to /usr/home like on FreeBSD.
        user = os.path.realpath(os.path.expanduser("~"))

        if pgnpath.startswith(user):
            refbase = pgnpath[len(user) + 1 :]  # black says '1 :'.
        else:
            refbase = pgnpath
        parser = tagpair_parser.PGNTagPair(
            game_class=tagpair_parser.TagPairGame
        )
        self.set_database(database)
        reference = self.value.reference
        db_segment_size = SegmentSize.db_segment_size
        reference[constants.FILE] = os.path.basename(refbase)
        game_number = 0
        copy_number = 0
        seen_number = 0
        game_offset = None
        # The PGN specification assumes iso-8859-1 encoding but try
        # utf-8 encoding first.
        encoding = None
        for try_encoding in ("utf-8", "iso-8859-1"):
            with open(pgnpath, mode="r", encoding=try_encoding) as pgntext:
                try:
                    while True:
                        if not pgntext.read(1024 * 1000):
                            encoding = try_encoding
                            break
                except UnicodeDecodeError:
                    pass
        if encoding is None:
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(
                    "".join(
                        (
                            "Unable to read ",
                            reference[constants.FILE],
                            " as utf-8 or iso-8859-1 ",
                            "encoding.",
                        )
                    )
                )
            return True
        file_games = database.recordlist_key(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PGNFILE_FIELD_DEF,
            key=database.encode_record_selector(reference[constants.FILE]),
        )
        file_count = file_games.count_records()
        file_games.close()
        if file_count:
            if reporter is not None:
                reporter.append_text_only("")
                reporter.append_text(
                    "".join(
                        (
                            str(file_count),
                            " games from file ",
                            reference[constants.FILE],
                            " already on database: only missing ",
                            "game numbers will be copied.",
                        )
                    )
                )
        with open(pgnpath, mode="r", encoding=encoding) as pgntext:
            for collected_game in parser.read_games(pgntext):
                game_offset = collected_game.game_offset
                game_number += 1
                reference[constants.GAME] = str(game_number)
                if file_count:
                    number_games = database.recordlist_key(
                        filespec.GAME_FILE_DEF,
                        filespec.GAME_NUMBER_FIELD_DEF,
                        key=database.encode_record_selector(
                            reference[constants.GAME]
                        ),
                    )
                    number_count = number_games.count_records()
                    if number_count:
                        file_games = database.recordlist_key(
                            filespec.GAME_FILE_DEF,
                            filespec.GAME_PGNFILE_FIELD_DEF,
                            key=database.encode_record_selector(
                                reference[constants.FILE]
                            ),
                        )
                        present_game = number_games & file_games
                        present_count = present_game.count_records()
                        present_game.close()
                        if present_count:
                            file_games.close()
                            number_games.close()
                            continue
                        file_games.close()
                    number_games.close()
                seen_number += 1
                self.value.headers = collected_game.pgn_tags
                # Should games be discarded for following reason if player
                # type is held?
                message = self._is_game_not_ratable_between_two_humans()
                if message:
                    if reporter is not None:
                        reporter.append_text_only(
                            "".join(
                                (
                                    "Game ",
                                    reference[constants.GAME],
                                    " in ",
                                    reference[constants.FILE],
                                    " : ",
                                    message,
                                )
                            )
                        )
                    continue

                # Symas LMDB does not supported zero length bytestring keys.
                if not database.zero_length_keys_supported:
                    headers = self.value.headers
                    for name in (
                        constants.TAG_TIMECONTROL,
                        constants.TAG_MODE,
                        constants.TAG_TERMINATION,
                    ):
                        if headers.get(name) == "":
                            del headers[name]
                            if reporter is not None:
                                reporter.append_text_only(
                                    "".join(
                                        (
                                            "Game ",
                                            reference[constants.GAME],
                                            " in ",
                                            reference[constants.FILE],
                                            " : tag ",
                                            name,
                                            ' with value "" ignored.',
                                        )
                                    )
                                )

                copy_number += 1
                self.key.recno = None
                self.put_record(self.database, filespec.GAME_FILE_DEF)
                if copy_number % db_segment_size == 0:
                    database.commit()
                    database.deferred_update_housekeeping()
                    database.start_transaction()
                    if reporter is not None:
                        reporter.append_text(
                            "".join(
                                (
                                    "Record ",
                                    str(self.key.recno),
                                    " is from game ",
                                    reference[constants.GAME],
                                    " in ",
                                    reference[constants.FILE],
                                )
                            )
                        )
        if reporter is not None and game_offset is not None:
            reporter.append_text_only("")
            reporter.append_text(
                "".join(
                    (
                        str(game_number),
                        " games read from ",
                        reference[constants.FILE],
                        " to character ",
                        str(game_offset),
                    )
                )
            )
            reporter.append_text_only(
                "".join(
                    (
                        str(copy_number),
                        " games added to database.",
                    )
                )
            )
            reporter.append_text_only(
                "".join(
                    (
                        str(file_count),
                        " games already on database.",
                    )
                )
            )
            reporter.append_text_only(
                "".join(
                    (
                        str(seen_number - copy_number),
                        " games were not copied for reasons given above.",
                    )
                )
            )
        return True

    def _is_game_not_ratable_between_two_humans(self):
        """Return False if game is ratable or a message if not.

        The Mode tag distinguishes OTB and online, etc, games.

        The TimeControl tag distinguishes blitz and rapidplay, etc, from
        standard play.

        """
        headers = self.value.headers
        for name in (constants.TAG_WHITETYPE, constants.TAG_BLACKTYPE):
            if headers.get(name, constants.HUMAN).lower() != constants.HUMAN:
                return "game is not between two human players"
        for name in (constants.TAG_WHITE, constants.TAG_BLACK):
            value = headers.get(name, "")
            if constants.CONSULTATION in value:
                return "game is a consultation game"
            if value in _NO_PLAYER:
                return "".join(
                    ("game has '", value, "' as value of '", name, "' tag")
                )
            if not value:
                return name.join(
                    ("game is missing ", ' tag or it has "" value')
                )
        if headers.get(constants.TAG_RESULT) not in constants.WIN_DRAW_LOSS:
            return "game result is not 1-0, 0-1, or 1/2-1/2"
        termination = headers.get(constants.TAG_TERMINATION, "")
        if termination.lower() in _NO_OPPONENT:
            return termination.join(
                ("game is not ratable due to termination reason: '", "'")
            )
        if constants.TAG_FEN in headers:
            if headers[constants.TAG_FEN] != constants.NORMAL_START:
                return "game is not from normal start position"
        for name in (
            constants.TAG_EVENT,
            constants.TAG_SITE,
            constants.TAG_DATE,
        ):
            if not headers.get(name):
                return name.join(
                    ("game is missing ", ' tag or it has "" value')
                )
        return False

    # Probably needed only by DPT database engine.
    # Probably only in this class to use _process_pgn_headers_from_directory
    # machinery and from similarity to copy_* classes.
    def _count_pgn_games_in_file(
        self, database, pgnpath, reporter, quit_event
    ):
        """Return True if import succeeds or pgnpath is not a PGN file."""
        del database, quit_event
        if not self._is_file_pgn_ext(pgnpath, reporter):
            return True
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                "Counting games in " + os.path.basename(pgnpath)
            )

        # Maybe /home is symlink to /usr/home like on FreeBSD.
        user = os.path.realpath(os.path.expanduser("~"))

        if pgnpath.startswith(user):
            refbase = pgnpath[len(user) + 1 :]  # black says '1 :'.
        else:
            refbase = pgnpath
        parser = tagpair_parser.PGNTagPair(game_class=tagpair_parser.GameCount)
        game_number = 0
        game_offset = None
        # The PGN specification assumes 'iso-8859-1' encoding but do not
        # bother trying 'utf-8' encoding first because things are only
        # being counted.
        with open(pgnpath, mode="r", encoding="iso-8859-1") as pgntext:
            for collected_game in parser.read_games(pgntext):
                game_offset = collected_game.game_offset
                game_number += 1
        if reporter is not None and game_offset is not None:
            reporter.append_text_only("")
            reporter.append_text(
                "".join(
                    (
                        str(game_number),
                        " games read from ",
                        os.path.basename(refbase),
                        " to character ",
                        str(game_offset),
                    )
                )
            )
        return game_number
