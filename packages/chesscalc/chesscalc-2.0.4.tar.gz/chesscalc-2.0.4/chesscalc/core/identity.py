# identity.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide a unique identifier for each player record."""

from solentware_base.core.record import KeyData
from solentware_base.core.record import ValueList, Record

from . import constants
from . import filespec


class NoPlayerIdentity(Exception):
    """Raise if unable to allocate player identity code."""


class NoEventIdentity(Exception):
    """Raise if unable to allocate event identity code."""


class NoTimeIdentity(Exception):
    """Raise if unable to allocate time limit identity code."""


class NoModeIdentity(Exception):
    """Raise if unable to allocate playing mode identity code."""


class NoTerminationIdentity(Exception):
    """Raise if unable to allocate termination reason identity code."""


class NoPlayerTypeIdentity(Exception):
    """Raise if unable to allocate player type identity code."""


class IdentityDBkey(KeyData):
    """Primary key of identity code."""


class _IdentityDBvalue(ValueList):
    """Identity data.

    This class is not intended for direct use as it lacks an extended
    version of the pack() method.  Subclasses will need to supply a
    suitable pack() method.
    """

    attributes = {"code": None, "type_": None}
    _attribute_order = ("type_", "code")
    assert set(_attribute_order) == set(attributes)

    def __init__(self):
        """Customise ValueList for identity data."""
        super().__init__()
        self.code = None
        self.type_ = None

    def empty(self):
        """(Re)Initialize value attribute."""
        self.code = None
        self.type_ = None


class IdentityDBvalue(_IdentityDBvalue):
    """Identity data.

    Expected use is IdentityDBrecord(valueclass=IdentityDBvalue).
    """

    def pack(self):
        """Generate identity record and index data."""
        val = super().pack()
        index = val[1]
        index[filespec.IDENTITY_TYPE_FIELD_DEF] = [self.type_]
        return val


class NextIdentityDBvalue(_IdentityDBvalue):
    """Identity data for next code.

    The pack() method is not extended to populate, or depopulate, indicies.
    Thus this class safe to use in deferred updates when modifying the most
    recently allocated identity.

    Expected use is IdentityDBrecord(valueclass=NextIdentityDBvalue).
    """


# For sqlite3, berkeleydb, and others except dpt, this level of indirection
# seems unnecessary: the record key could be the player and person identity
# directly.  Record numbers are arbitrary in DPT and are liable to change
# when a file is reorganized: hence an explicit record to provide unique,
# and permanent, identities for records.
class IdentityDBrecord(Record):
    """Customise Record with IdentityDBkey and IdentityDBvalue by default."""

    def __init__(self, keyclass=IdentityDBkey, valueclass=IdentityDBvalue):
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
            if dbname == filespec.IDENTITY_TYPE_FIELD_DEF:
                return [(self.value.type_, srkey)]
            return []
        except:  # pycodestyle E722: pylint is happy with following 'raise'.
            if datasource is None:
                return []
            raise


def _create_identity_record_if_not_exists(database, key_type):
    """Create record for next identity if it does not exist."""
    database.start_read_only_transaction()
    if database.recordlist_key(
        filespec.IDENTITY_FILE_DEF,
        filespec.IDENTITY_TYPE_FIELD_DEF,
        key=database.encode_record_selector(key_type),
    ).count_records():
        database.end_read_only_transaction()
        return
    database.end_read_only_transaction()
    record = IdentityDBrecord()
    record.value.code = 0
    record.value.type_ = key_type
    database.start_transaction()
    record.put_record(database, filespec.IDENTITY_FILE_DEF)
    database.commit()


def create_player_identity_record_if_not_exists(database):
    """Delegate to _create_identity_record_if_not_exists for players."""
    _create_identity_record_if_not_exists(
        database, constants.PLAYER_IDENTITY_KEY
    )


def create_event_identity_record_if_not_exists(database):
    """Delegate to _create_identity_record_if_not_exists for events."""
    _create_identity_record_if_not_exists(
        database, constants.EVENT_IDENTITY_KEY
    )


def create_time_limit_identity_record_if_not_exists(database):
    """Delegate to _create_identity_record_if_not_exists for time limits."""
    _create_identity_record_if_not_exists(
        database, constants.TIME_IDENTITY_KEY
    )


def create_playing_mode_identity_record_if_not_exists(database):
    """Delegate to _create_identity_record_if_not_exists for playing modes."""
    _create_identity_record_if_not_exists(
        database, constants.MODE_IDENTITY_KEY
    )


def create_termination_identity_record_if_not_exists(database):
    """Delegate to _create_identity_record_if_not_exists for terminations."""
    _create_identity_record_if_not_exists(
        database, constants.TERMINATION_IDENTITY_KEY
    )


def create_player_type_identity_record_if_not_exists(database):
    """Delegate to _create_identity_record_if_not_exists for player types."""
    _create_identity_record_if_not_exists(
        database, constants.PLAYERTYPE_IDENTITY_KEY
    )


def _get_next_identity_value_after_allocation(database, keytype, exception):
    """Allocate and return next identity code for keytype.

    Raise exception if next identity cannot be allocated.

    """
    recordlist = database.recordlist_key(
        filespec.IDENTITY_FILE_DEF,
        filespec.IDENTITY_TYPE_FIELD_DEF,
        key=database.encode_record_selector(keytype),
    )
    count = recordlist.count_records()
    if count == 0:
        raise exception("Identity code cannot be allocated")
    if count > 1:
        raise exception("Duplicate identity codes available")
    cursor = database.database_cursor(
        filespec.IDENTITY_FILE_DEF,
        None,
        recordset=recordlist,
    )
    record = IdentityDBrecord(valueclass=NextIdentityDBvalue)
    instance = cursor.first()
    if not instance:
        raise exception("Identity code record expected but not found")
    record.load_record(instance)
    new_record = record.clone()
    value = new_record.value
    if value.type_ != keytype:
        raise exception("Record is not the correct identity code type")
    value.code += 1

    # None is safe because self.srkey == new_record.srkey.
    record.edit_record(database, filespec.IDENTITY_FILE_DEF, None, new_record)

    # Plain value.code, an int object, is acceptable in sqlite3 but str(...)
    # is necessary for berkeleydb, lmdb, and others.
    return str(value.code)


def get_next_player_identity_value_after_allocation(database):
    """Allocate and return next player identity code.

    Raise NoPlayerIdentity if next identity cannot be allocated.

    """
    return _get_next_identity_value_after_allocation(
        database, constants.PLAYER_IDENTITY_KEY, NoPlayerIdentity
    )


def get_next_event_identity_value_after_allocation(database):
    """Allocate and return next event identity code.

    Raise NoEventIdentity if next identity cannot be allocated.

    """
    return _get_next_identity_value_after_allocation(
        database, constants.EVENT_IDENTITY_KEY, NoEventIdentity
    )


def get_next_timelimit_identity_value_after_allocation(database):
    """Allocate and return next time control identity code.

    Raise NoTimeIdentity if next identity cannot be allocated.

    """
    return _get_next_identity_value_after_allocation(
        database, constants.TIME_IDENTITY_KEY, NoTimeIdentity
    )


def get_next_mode_identity_value_after_allocation(database):
    """Allocate and return next playing mode identity code.

    Raise NoModeIdentity if next identity cannot be allocated.

    """
    return _get_next_identity_value_after_allocation(
        database, constants.MODE_IDENTITY_KEY, NoModeIdentity
    )


def get_next_playertype_identity_value_after_allocation(database):
    """Allocate and return next time control identity code.

    Raise NoPlayerTypeIdentity if next identity cannot be allocated.

    """
    return _get_next_identity_value_after_allocation(
        database, constants.PLAYERTYPE_IDENTITY_KEY, NoPlayerTypeIdentity
    )


def get_next_termination_identity_value_after_allocation(database):
    """Allocate and return next time control identity code.

    Raise NoTerminationIdentity if next identity cannot be allocated.

    """
    return _get_next_identity_value_after_allocation(
        database, constants.TERMINATION_IDENTITY_KEY, NoTerminationIdentity
    )
