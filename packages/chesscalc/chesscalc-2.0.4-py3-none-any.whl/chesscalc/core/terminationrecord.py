# terminationrecord.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Record definition classes for Termination PGN tag data."""

from solentware_base.core.record import KeyData
from solentware_base.core.record import ValueList
from solentware_base.core.record import Record
from solentware_base.core.segmentsize import SegmentSize

from . import filespec
from . import identity


class TerminationDBkey(KeyData):
    """Primary key of playing mode."""


class TerminationDBvalue(ValueList):
    """Playing mode data."""

    attributes = {
        "termination": None,  # TAG_TERMINATION.
        "alias": None,
        "identity": None,
    }
    _attribute_order = ("termination", "alias", "identity")
    assert set(_attribute_order) == set(attributes)

    def __init__(self):
        """Customise ValueList for playing termination data."""
        super().__init__()
        self.termination = None
        self.alias = None
        self.identity = None

    # Should self.termination be self.name?
    @property
    def name(self):
        """Return termination."""
        return self.termination

    def empty(self):
        """(Re)Initialize value attribute."""
        self.termination = None
        self.alias = None
        self.identity = None

    def alias_index_key(self):
        """Return the key for the terminationalias index."""
        return self.termination

    def load_alias_index_key(self, value):
        """Bind attributes for the terminationalias index to items in value."""
        self.termination = value

    def pack(self):
        """Delegate to generate termination data then add index data.

        The terminationalias index will have the termination name and other
        descriptive detail as it's value, from the alias_index_key() method.

        The terminationidentity index will have either the identity number
        given when the record was created (identity attribute), or the
        identity number of the playing mode record which this record currently
        aliases (alias attribute).

        """
        val = super().pack()
        index = val[1]
        index[filespec.TERMINATION_ALIAS_FIELD_DEF] = [self.alias_index_key()]
        index[filespec.TERMINATION_IDENTITY_FIELD_DEF] = [self.alias]
        return val


class TerminationDBrecord(Record):
    """Customise Record with TerminationDBkey and TerminationDBvalue.

    Arguments keyclass and keyvalue enable overrides.
    """

    def __init__(
        self, keyclass=TerminationDBkey, valueclass=TerminationDBvalue
    ):
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
            if dbname == filespec.TERMINATION_ALIAS_FIELD_DEF:
                return [(self.value.alias_index_key(), srkey)]
            if dbname == filespec.TERMINATION_IDENTITY_FIELD_DEF:
                return [(self.value.alias, srkey)]
            return []
        except:  # pycodestyle E722: pylint is happy with following 'raise'.
            if datasource is None:
                return []
            raise


class TerminationDBImporter(TerminationDBrecord):
    """Extend with methods to import multiple game headers from PGN files."""

    def copy_termination_names_from_games(
        self,
        database,
        reporter=None,
        quit_event=None,
        **kwargs,
    ):
        """Return True if copy termination names from games file succeeds.

        quit_event allows the import to be interrupted by passing an Event
        instance which get queried after processing each game.
        kwargs soaks up arguments not used in this method.

        """
        del kwargs
        if reporter is not None:
            reporter.append_text("Copy termination names from games.")
        cursor = database.database_cursor(
            filespec.GAME_FILE_DEF, filespec.GAME_TERMINATION_FIELD_DEF
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
            this_record = record[0]
            if prev_record == this_record:
                continue
            game_count += 1
            prev_record = this_record
            value.termination = this_record
            alias = value.alias_index_key()
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Copy stopped.")
                return False
            if database.recordlist_key(
                filespec.TERMINATION_FILE_DEF,
                filespec.TERMINATION_ALIAS_FIELD_DEF,
                key=database.encode_record_selector(alias),
            ).count_records():
                onfile_count += 1
                continue
            copy_count += 1
            pid = (
                identity.get_next_termination_identity_value_after_allocation(
                    database
                )
            )
            value.alias = pid
            value.identity = pid
            self.key.recno = None
            self.put_record(database, filespec.TERMINATION_FILE_DEF)
            if int(pid) % db_segment_size == 0:
                # Need the cursor wrapping in berkeleydb, bsddb3, db_tkinter
                # and lmdb too.
                cursor.close()
                database.commit()
                database.deferred_update_housekeeping()
                database.start_transaction()
                cursor = database.database_cursor(
                    filespec.GAME_FILE_DEF, filespec.GAME_TERMINATION_FIELD_DEF
                )
                cursor.setat(record)

                if reporter is not None:
                    reporter.append_text(
                        "".join(
                            (
                                "Termination ",
                                value.termination,
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
                        " terminations added to database.",
                    )
                )
            )
            reporter.append_text_only(
                "".join(
                    (
                        str(onfile_count),
                        " terminations already on database.",
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

    def count_termination_names_to_be_copied_from_games(
        self,
        database,
        reporter=None,
        quit_event=None,
        **kwargs,
    ):
        """Return count of termination names in games not in termination file.

        quit_event allows the import to be interrupted by passing an Event
        instance which get queried after processing each game.
        kwargs soaks up arguments not used in this method.

        """
        del kwargs
        if reporter is not None:
            reporter.append_text(
                "Count termination names to be copied from games."
            )
        cursor = database.database_cursor(
            filespec.GAME_FILE_DEF, filespec.GAME_TERMINATION_FIELD_DEF
        )
        value = self.value
        prev_record = None
        count = 0
        while True:
            record = cursor.next()
            if record is None:
                break
            this_record = record[0]
            if prev_record == this_record:
                continue
            prev_record = this_record
            (value.termination,) = this_record
            alias = value.alias_index_key()
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Count stopped.")
                return None
            if database.recordlist_key(
                filespec.TERMINATION_FILE_DEF,
                filespec.TERMINATION_ALIAS_FIELD_DEF,
                key=database.encode_record_selector(alias),
            ).count_records():
                continue
            count += 1
        if reporter is not None:
            reporter.append_text(
                str(count) + " termination names to be copied from games."
            )
        return count
