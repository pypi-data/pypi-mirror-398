# eventrecord.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Record definition classes for PGN tag data which identifies an event.

The Event, Eventdate, Section, and Stage, tags contribute to the identity.
"""

from ast import literal_eval

from solentware_base.core.record import KeyData
from solentware_base.core.record import ValueList
from solentware_base.core.record import Record
from solentware_base.core.segmentsize import SegmentSize

from . import filespec
from . import identity


class EventDBkey(KeyData):
    """Primary key of event."""


class EventDBvalue(ValueList):
    """Event data."""

    attributes = {
        "event": None,  # TAG_EVENT.
        "eventdate": None,  # TAG_EVENTDATE.
        "section": None,  # TAG_SECTION.
        "stage": None,  # TAG_STAGE.
        "alias": None,
        "identity": None,
    }
    _attribute_order = (
        "event",
        "eventdate",
        "section",
        "stage",
        "alias",
        "identity",
    )
    assert set(_attribute_order) == set(attributes)

    def __init__(self):
        """Customise ValueList for player data."""
        super().__init__()
        self.event = None
        self.eventdate = None
        self.section = None
        self.stage = None
        self.alias = None
        self.identity = None

    def empty(self):
        """(Re)Initialize value attribute."""
        self.event = None
        self.eventdate = None
        self.section = None
        self.stage = None
        self.alias = None
        self.identity = None

    def alias_index_key(self):
        """Return the key for the eventalias index."""
        return repr(
            (
                self.event,
                self.eventdate,
                self.section,
                self.stage,
            )
        )

    def load_alias_index_key(self, value):
        """Bind attributes for the eventalias index to items in value."""
        (
            self.event,
            self.eventdate,
            self.section,
            self.stage,
        ) = literal_eval(value)

    def pack(self):
        """Delegate to generate player data then add index data.

        The eventalias index will have the event name and other descriptive
        detail as it's value, from the alias_index_key() method.

        The eventidentity index will have either the identity number given
        when the record was created (identity attribute), or the identity
        number of the event record which this record currently aliases
        (alias attribute).

        """
        val = super().pack()
        index = val[1]
        index[filespec.EVENT_ALIAS_FIELD_DEF] = [self.alias_index_key()]
        index[filespec.EVENT_IDENTITY_FIELD_DEF] = [self.alias]
        index[filespec.EVENT_NAME_FIELD_DEF] = [self.event]
        return val


class EventDBrecord(Record):
    """Customise Record with EventDBkey and EventDBvalue by default."""

    def __init__(self, keyclass=EventDBkey, valueclass=EventDBvalue):
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
            if dbname == filespec.EVENT_ALIAS_FIELD_DEF:
                return [(self.value.alias_index_key(), srkey)]
            if dbname == filespec.EVENT_IDENTITY_FIELD_DEF:
                return [(self.value.alias, srkey)]
            if dbname == filespec.EVENT_NAME_FIELD_DEF:
                return [(self.value.event, srkey)]
            return []
        except:  # pycodestyle E722: pylint is happy with following 'raise'.
            if datasource is None:
                return []
            raise


class EventDBImporter(EventDBrecord):
    """Extend with methods to import multiple game headers from PGN files."""

    def copy_event_names_from_games(
        self,
        database,
        reporter=None,
        quit_event=None,
        **kwargs,
    ):
        """Return True if copy event names from games file succeeds.

        quit_event allows the import to be interrupted by passing an Event
        instance which get queried after processing each game.
        kwargs soaks up arguments not used in this method.

        """
        del kwargs
        if reporter is not None:
            reporter.append_text("Copy event names from games.")
        cursor = database.database_cursor(
            filespec.GAME_FILE_DEF, filespec.GAME_EVENT_FIELD_DEF
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
            (
                value.event,
                value.eventdate,
                value.section,
                value.stage,
            ) = this_record
            alias = value.alias_index_key()
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Copy stopped.")
                return False
            if database.recordlist_key(
                filespec.EVENT_FILE_DEF,
                filespec.EVENT_ALIAS_FIELD_DEF,
                key=database.encode_record_selector(alias),
            ).count_records():
                onfile_count += 1
                continue
            copy_count += 1
            pid = identity.get_next_event_identity_value_after_allocation(
                database
            )
            value.alias = pid
            value.identity = pid
            self.key.recno = None
            self.put_record(database, filespec.EVENT_FILE_DEF)
            if int(pid) % db_segment_size == 0:
                # Need the cursor wrapping in berkeleydb, bsddb3, db_tkinter
                # and lmdb too.
                cursor.close()
                database.commit()
                database.deferred_update_housekeeping()
                database.start_transaction()
                cursor = database.database_cursor(
                    filespec.GAME_FILE_DEF, filespec.GAME_EVENT_FIELD_DEF
                )
                cursor.setat(record)

                if reporter is not None:
                    reporter.append_text(
                        "".join(
                            (
                                "Event ",
                                value.event,
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
                        " events added to database.",
                    )
                )
            )
            reporter.append_text_only(
                "".join(
                    (
                        str(onfile_count),
                        " events already on database.",
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

    def count_event_names_to_be_copied_from_games(
        self,
        database,
        reporter=None,
        quit_event=None,
        **kwargs,
    ):
        """Return number of event names in games file but not events file.

        quit_event allows the import to be interrupted by passing an Event
        instance which get queried after processing each game.
        kwargs soaks up arguments not used in this method.

        """
        del kwargs
        if reporter is not None:
            reporter.append_text("Count event names to be copied from games.")
        cursor = database.database_cursor(
            filespec.GAME_FILE_DEF, filespec.GAME_EVENT_FIELD_DEF
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
            (
                value.event,
                value.eventdate,
                value.section,
                value.stage,
            ) = this_record
            alias = value.alias_index_key()
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Count stopped.")
                return None
            if database.recordlist_key(
                filespec.EVENT_FILE_DEF,
                filespec.EVENT_ALIAS_FIELD_DEF,
                key=database.encode_record_selector(alias),
            ).count_records():
                continue
            count += 1
        if reporter is not None:
            reporter.append_text(
                str(count) + " event names to be copied from games."
            )
        return count
