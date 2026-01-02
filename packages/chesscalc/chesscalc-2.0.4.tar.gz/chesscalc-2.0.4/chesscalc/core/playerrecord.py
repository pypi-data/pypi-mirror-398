# playerrecord.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Record definition classes for PGN tag data which identifies a player.

The Black or White tags; plus the Event, Eventdate, Section, Stage,
BlackTeam or WhiteTeam, and BlackFideId or WhiteFideId, tags contribute
to the identity.
"""

from ast import literal_eval

from solentware_base.core.record import KeyData
from solentware_base.core.record import ValueList
from solentware_base.core.record import Record
from solentware_base.core.segmentsize import SegmentSize

from . import filespec
from . import identity


class PlayerDBkey(KeyData):
    """Primary key of player."""


class _PlayerValue(ValueList):
    """The player data used in player and person name indicies.

    Subclasses which provide alias and identity attributes are used in
    database records.
    """

    attributes = {
        "name": None,  # TAG_BLACK or TAG_WHITE.
        "event": None,  # TAG_EVENT.
        "eventdate": None,  # TAG_EVENTDATE.
        "section": None,  # TAG_SECTION.
        "stage": None,  # TAG_STAGE.
        "team": None,  # TAG_BLACKTEAM or TAG_WHITETEAM.
        "fideid": None,  # TAG_BLACKFIDEID or TAG_WHITEFIDEID.
        "type": None,  # TAG_BLACKTYPE or TAG_WHITETYPE.
    }
    _attribute_order = (
        "name",
        "event",
        "eventdate",
        "section",
        "stage",
        "team",
        "fideid",
        "type",
    )
    assert set(_attribute_order) == set(attributes)

    def __init__(self):
        """Customise ValueList for player data."""
        super().__init__()
        self.name = None
        self.event = None
        self.eventdate = None
        self.section = None
        self.stage = None
        self.team = None
        self.fideid = None
        self.type = None

    def alias_index_key(self):
        """Return the key for the playeralias or personalias index."""
        return repr(
            (
                self.name,
                self.event,
                self.eventdate,
                self.section,
                self.stage,
                self.team,
                self.fideid,
                self.type,
            )
        )

    def load_alias_index_key(self, value):
        """Bind playeralias or personalias index attributes to value items.

        Unpack from repr(<attributes>) in value by literal_eval() call.

        """
        (
            self.name,
            self.event,
            self.eventdate,
            self.section,
            self.stage,
            self.team,
            self.fideid,
            self.type,
        ) = literal_eval(value)

    def set_alias_index_key(self, value):
        """Bind playeralias or personalias index attributes to value items.

        Unpack from tuple in value.

        """
        (
            self.name,
            self.event,
            self.eventdate,
            self.section,
            self.stage,
            self.team,
            self.fideid,
            self.type,
        ) = value

    def alias_index(self):
        """Return value packed by alias_index_key method as tuple."""
        return (
            self.name,
            self.event,
            self.eventdate,
            self.section,
            self.stage,
            self.team,
            self.fideid,
            self.type,
        )


# This may never differ from _PlayerValue.
class PersonValue(_PlayerValue):
    """Provide player and person index key manipulation.

    PersonValue should not be used in *Record classes.
    """


class _PlayerDBvalue(_PlayerValue):
    """Player data.

    This class is not intended for direct use as it lacks an extended
    version of the pack() method.  Subclasses will need to supply a
    suitable pack() method.
    """

    attributes = {"alias": None, "identity": None}
    attributes.update(_PlayerValue.attributes)
    _attribute_order = _PlayerValue._attribute_order + (
        "alias",
        "identity",
    )
    assert set(_attribute_order) == set(attributes)

    def __init__(self):
        """Customise _PlayerValue for player data."""
        super().__init__()
        self.alias = None
        self.identity = None

    def empty(self):
        """(Re)Initialize value attribute."""
        self.name = None
        self.event = None
        self.eventdate = None
        self.section = None
        self.stage = None
        self.team = None
        self.fideid = None
        self.alias = None
        self.identity = None


class PlayerDBvalue(_PlayerDBvalue):
    """Player data for record not yet identified with a person.

    When used to update database the pack() method causes the personalias
    index to be cleared of references to the record and the playeralias
    index to be populated with a reference.

    Expected use is PlayerDBrecord(valueclass=PlayerDBvalue).
    """

    def pack(self):
        """Delegate to generate player data then add index data.

        Set playeralias index value to [key] and personalias index to [].

        """
        val = super().pack()
        index = val[1]
        index[filespec.PLAYER_ALIAS_FIELD_DEF] = [self.alias_index_key()]
        index[filespec.PLAYER_NAME_FIELD_DEF] = [self.name]
        index[filespec.PLAYER_KNOWN_FIELD_DEF] = []
        index[filespec.PLAYER_LINKS_FIELD_DEF] = []
        index[filespec.PLAYER_IDENTIFIER_FIELD_DEF] = [self.identity]
        index[filespec.PERSON_ALIAS_FIELD_DEF] = []
        index[filespec.PERSON_NAME_FIELD_DEF] = []
        return val


class PersonDBvalue(_PlayerDBvalue):
    """Player data for record identified with a person.

    When used to update database the pack() method causes the playeralias
    index to be cleared of references to the record and the personalias
    index to be populated with a reference.

    Expected use is PlayerDBrecord(valueclass=PersonDBvalue).
    """

    def pack(self):
        """Delegate to generate player data then add index data.

        Set personalias index value to [key] and playeralias index to [].

        """
        val = super().pack()
        index = val[1]
        index[filespec.PLAYER_ALIAS_FIELD_DEF] = []
        index[filespec.PLAYER_NAME_FIELD_DEF] = []
        if self.identity != self.alias:
            index[filespec.PLAYER_KNOWN_FIELD_DEF] = []
        else:
            index[filespec.PLAYER_KNOWN_FIELD_DEF] = [self.alias]
        index[filespec.PLAYER_LINKS_FIELD_DEF] = [self.alias]
        index[filespec.PLAYER_IDENTIFIER_FIELD_DEF] = [self.identity]
        index[filespec.PERSON_ALIAS_FIELD_DEF] = [self.alias_index_key()]
        index[filespec.PERSON_NAME_FIELD_DEF] = [self.name]
        return val


class PlayerDBrecord(Record):
    """Customise Record with PlayerDBkey and PlayerDBvalue by default."""

    def __init__(self, keyclass=PlayerDBkey, valueclass=PlayerDBvalue):
        """Delegate with keyclass and valueclass arguments."""
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
            if dbname == filespec.PLAYER_ALIAS_FIELD_DEF:
                return [(self.value.alias_index_key(), srkey)]
            if dbname == filespec.PLAYER_LINKS_FIELD_DEF:
                return [(self.value.alias, srkey)]
            if dbname == filespec.PLAYER_KNOWN_FIELD_DEF:
                return [(self.value.alias, srkey)]
            if dbname == filespec.PLAYER_IDENTIFIER_FIELD_DEF:
                return [(self.value.identity, srkey)]
            if dbname == filespec.PERSON_ALIAS_FIELD_DEF:
                return [(self.value.alias_index_key(), srkey)]
            if dbname == filespec.PLAYER_NAME_FIELD_DEF:
                return [(self.value.name, srkey)]
            if dbname == filespec.PERSON_NAME_FIELD_DEF:
                return [(self.value.name, srkey)]
            return []
        except:  # pycodestyle E722: pylint is happy with following 'raise'.
            if datasource is None:
                return []
            raise


class PlayerDBImporter(PlayerDBrecord):
    """Extend with methods to import multiple game headers from PGN files."""

    def copy_player_names_from_games(
        self,
        database,
        reporter=None,
        quit_event=None,
        **kwargs,
    ):
        """Return True if copy player names from games file succeeds.

        quit_event allows the import to be interrupted by passing an Event
        instance which get queried after processing each game.
        kwargs soaks up arguments not used in this method.

        """
        del kwargs
        if reporter is not None:
            reporter.append_text("Copy player names from games.")
        cursor = database.database_cursor(
            filespec.GAME_FILE_DEF, filespec.GAME_PLAYER_FIELD_DEF
        )
        value = self.value
        db_segment_size = SegmentSize.db_segment_size
        game_count = 0
        onfile_count = 0
        copy_count = 0
        prev_record = None
        while True:
            record = cursor.next()
            if record is None:
                break
            this_record = literal_eval(record[0])
            if prev_record == this_record:
                continue
            game_count += 1
            prev_record = this_record
            value.set_alias_index_key(this_record)
            alias = value.alias_index_key()
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Copy stopped.")
                return False
            if database.recordlist_key(
                filespec.PLAYER_FILE_DEF,
                filespec.PERSON_ALIAS_FIELD_DEF,
                key=database.encode_record_selector(alias),
            ).count_records():
                onfile_count += 1
                continue
            if database.recordlist_key(
                filespec.PLAYER_FILE_DEF,
                filespec.PLAYER_ALIAS_FIELD_DEF,
                key=database.encode_record_selector(alias),
            ).count_records():
                onfile_count += 1
                continue
            copy_count += 1
            pid = identity.get_next_player_identity_value_after_allocation(
                database
            )
            value.alias = pid
            value.identity = pid
            self.key.recno = None
            self.put_record(database, filespec.PLAYER_FILE_DEF)
            if int(pid) % db_segment_size == 0:
                # Need the cursor wrapping in berkeleydb, bsddb3, db_tkinter
                # and lmdb too.
                cursor.close()
                database.commit()
                database.deferred_update_housekeeping()
                database.start_transaction()
                cursor = database.database_cursor(
                    filespec.GAME_FILE_DEF, filespec.GAME_PLAYER_FIELD_DEF
                )
                cursor.setat(record)

                if reporter is not None:
                    reporter.append_text(
                        "".join(
                            (
                                "Player ",
                                value.name,
                                " is record ",
                                str(self.key.recno),
                            )
                        )
                    )
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                "".join(
                    (
                        str(copy_count),
                        " players added to database.",
                    )
                )
            )
            reporter.append_text_only(
                "".join(
                    (
                        str(onfile_count),
                        " players already on database.",
                    )
                )
            )
            reporter.append_text_only(
                "".join(
                    (
                        str(game_count),
                        " game references processed.",
                    )
                )
            )
            reporter.append_text_only("")
        return True

    def count_player_names_to_be_copied_from_games(
        self,
        database,
        reporter=None,
        quit_event=None,
        **kwargs,
    ):
        """Return number of player names in games file but not players file.

        quit_event allows the import to be interrupted by passing an Event
        instance which get queried after processing each game.
        kwargs soaks up arguments not used in this method.

        """
        del kwargs
        if reporter is not None:
            reporter.append_text("Count player names to be copied from games.")
        cursor = database.database_cursor(
            filespec.GAME_FILE_DEF, filespec.GAME_PLAYER_FIELD_DEF
        )
        value = self.value
        prev_record = None
        count = 0
        while True:
            record = cursor.next()
            if record is None:
                break
            this_record = literal_eval(record[0])
            if prev_record == this_record:
                continue
            prev_record = this_record
            value.set_alias_index_key(this_record)
            alias = value.alias_index_key()
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Count stopped.")
                return None
            if database.recordlist_key(
                filespec.PLAYER_FILE_DEF,
                filespec.PERSON_ALIAS_FIELD_DEF,
                key=database.encode_record_selector(alias),
            ).count_records():
                continue
            if database.recordlist_key(
                filespec.PLAYER_FILE_DEF,
                filespec.PLAYER_ALIAS_FIELD_DEF,
                key=database.encode_record_selector(alias),
            ).count_records():
                continue
            count += 1
        if reporter is not None:
            reporter.append_text(
                str(count) + " player names to be copied from games."
            )
        return count
