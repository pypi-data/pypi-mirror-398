# timecontrolrecord.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Record definition classes for TimeControl PGN tag data."""

from solentware_base.core.record import KeyData
from solentware_base.core.record import ValueList
from solentware_base.core.record import Record
from solentware_base.core.segmentsize import SegmentSize

from . import filespec
from . import identity


class TimeControlDBkey(KeyData):
    """Primary key of time control."""


class TimeControlDBvalue(ValueList):
    """Time control data."""

    attributes = {
        "timecontrol": None,  # TAG_TIMECONTROL.
        "alias": None,
        "identity": None,
    }
    _attribute_order = ("timecontrol", "alias", "identity")
    assert set(_attribute_order) == set(attributes)

    def __init__(self):
        """Customise ValueList for time control data."""
        super().__init__()
        self.timecontrol = None
        self.alias = None
        self.identity = None

    # Should self.timecontrol be self.name?
    @property
    def name(self):
        """Return timecontrol."""
        return self.timecontrol

    def empty(self):
        """(Re)Initialize value attribute."""
        self.timecontrol = None
        self.alias = None
        self.identity = None

    def alias_index_key(self):
        """Return the key for the timealias index."""
        return self.timecontrol

    def load_alias_index_key(self, value):
        """Bind attributes for the timealias index to items in value."""
        self.timecontrol = value

    def pack(self):
        """Delegate to generate time control data then add index data.

        The timealias index will have the time control name and other
        descriptive detail as it's value, from the alias_index_key() method.

        The timeidentity index will have either the identity number given
        when the record was created (identity attribute), or the identity
        number of the time control record which this record currently aliases
        (alias attribute).

        """
        val = super().pack()
        index = val[1]
        index[filespec.TIME_ALIAS_FIELD_DEF] = [self.alias_index_key()]
        index[filespec.TIME_IDENTITY_FIELD_DEF] = [self.alias]
        return val


class TimeControlDBrecord(Record):
    """Customise Record with TimeControlDBkey and TimeControlDBvalue."""

    def __init__(
        self, keyclass=TimeControlDBkey, valueclass=TimeControlDBvalue
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
            if dbname == filespec.TIME_ALIAS_FIELD_DEF:
                return [(self.value.alias_index_key(), srkey)]
            if dbname == filespec.TIME_IDENTITY_FIELD_DEF:
                return [(self.value.alias, srkey)]
            return []
        except:  # pycodestyle E722: pylint is happy with following 'raise'.
            if datasource is None:
                return []
            raise


class TimeControlDBImporter(TimeControlDBrecord):
    """Extend with methods to import multiple game headers from PGN files."""

    def copy_time_control_names_from_games(
        self,
        database,
        reporter=None,
        quit_event=None,
        **kwargs,
    ):
        """Return True if copy time control names from games file succeeds.

        quit_event allows the import to be interrupted by passing an Event
        instance which get queried after processing each game.
        kwargs soaks up arguments not used in this method.

        """
        del kwargs
        if reporter is not None:
            reporter.append_text("Copy time control names from games.")
        cursor = database.database_cursor(
            filespec.GAME_FILE_DEF, filespec.GAME_TIMECONTROL_FIELD_DEF
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
            value.timecontrol = this_record
            alias = value.alias_index_key()
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Copy stopped.")
                return False
            if database.recordlist_key(
                filespec.TIME_FILE_DEF,
                filespec.TIME_ALIAS_FIELD_DEF,
                key=database.encode_record_selector(alias),
            ).count_records():
                onfile_count += 1
                continue
            copy_count += 1
            pid = identity.get_next_timelimit_identity_value_after_allocation(
                database
            )
            value.alias = pid
            value.identity = pid
            self.key.recno = None
            self.put_record(database, filespec.TIME_FILE_DEF)
            if int(pid) % db_segment_size == 0:
                # Need the cursor wrapping in berkeleydb, bsddb3, db_tkinter
                # and lmdb too.
                cursor.close()
                database.commit()
                database.deferred_update_housekeeping()
                database.start_transaction()
                cursor = database.database_cursor(
                    filespec.GAME_FILE_DEF, filespec.GAME_TIMECONTROL_FIELD_DEF
                )
                cursor.setat(record)

                if reporter is not None:
                    reporter.append_text(
                        "".join(
                            (
                                "Time control ",
                                value.timecontrol,
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
                        " time controls added to database.",
                    )
                )
            )
            reporter.append_text_only(
                "".join(
                    (
                        str(onfile_count),
                        " time controls already on database.",
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

    def count_time_control_names_to_be_copied_from_games(
        self,
        database,
        reporter=None,
        quit_event=None,
        **kwargs,
    ):
        """Return number of time control names not in time control file.

        quit_event allows the import to be interrupted by passing an Event
        instance which get queried after processing each game.
        kwargs soaks up arguments not used in this method.

        """
        del kwargs
        if reporter is not None:
            reporter.append_text(
                "Count time control names to be copied from games."
            )
        cursor = database.database_cursor(
            filespec.GAME_FILE_DEF, filespec.GAME_TIMECONTROL_FIELD_DEF
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
            value.timecontrol = this_record
            alias = value.alias_index_key()
            if quit_event and quit_event.is_set():
                if reporter is not None:
                    reporter.append_text_only("")
                    reporter.append_text("Count stopped.")
                return None
            if database.recordlist_key(
                filespec.TIME_FILE_DEF,
                filespec.TIME_ALIAS_FIELD_DEF,
                key=database.encode_record_selector(alias),
            ).count_records():
                continue
            count += 1
        if reporter is not None:
            reporter.append_text(
                str(count) + " time control names to be copied from games."
            )
        return count
