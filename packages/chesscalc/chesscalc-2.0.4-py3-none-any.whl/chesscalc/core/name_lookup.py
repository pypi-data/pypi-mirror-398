# name_lookup.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""This module provides functions to translate identities to names.

The names must be suitable as the text of a tkinter.ttk.Entry widget.
"""

from . import eventrecord
from . import moderecord
from . import playerrecord
from . import playertyperecord
from . import terminationrecord
from . import timecontrolrecord
from . import filespec
from . import identify_item


def get_player_name_from_identity(database, identity):
    """Return player name for identity or None."""
    person_record = None
    database.start_read_only_transaction()
    try:
        person_record = get_player_record_from_identity(database, identity)
    finally:
        database.end_read_only_transaction()
    if person_record is None:
        return None
    return person_record.value.alias_index_key()


def get_player_record_from_identity(database, identity):
    """Return player record for identity or None."""
    recordlist = database.recordlist_key(
        filespec.PLAYER_FILE_DEF,
        filespec.PLAYER_IDENTIFIER_FIELD_DEF,
        key=database.encode_record_selector(identity),
    )
    primary_record = identify_item.get_first_item_on_recordlist(
        database,
        recordlist,
        filespec.PLAYER_FILE_DEF,
    )
    if primary_record is None:
        return None
    person_record = playerrecord.PlayerDBrecord()
    person_record.load_record(primary_record)
    return person_record


def get_known_player_record_from_identity(database, identity):
    """Return player record for identity or None."""
    recordlist = database.recordlist_key(
        filespec.PLAYER_FILE_DEF,
        filespec.PLAYER_KNOWN_FIELD_DEF,
        key=database.encode_record_selector(identity),
    )
    primary_record = identify_item.get_identity_item_on_recordlist(
        playerrecord.PersonDBvalue,
        database,
        recordlist,
        filespec.PLAYER_FILE_DEF,
    )
    if primary_record is None:
        return None
    person_record = playerrecord.PlayerDBrecord()
    person_record.load_record(primary_record)
    return person_record


def get_time_control_name_from_identity(database, identity):
    """Return time control name for identity or None."""
    time_control_record = None
    database.start_read_only_transaction()
    try:
        time_control_record = get_time_control_record_from_identity(
            database, identity
        )
    finally:
        database.end_read_only_transaction()
    if time_control_record is None:
        return None
    return time_control_record.value.alias_index_key()


def get_time_control_record_from_identity(database, identity):
    """Return time control record for identity or None."""
    recordlist = database.recordlist_key(
        filespec.TIME_FILE_DEF,
        filespec.TIME_IDENTITY_FIELD_DEF,
        key=database.encode_record_selector(identity),
    )
    primary_record = identify_item.get_identity_item_on_recordlist(
        timecontrolrecord.TimeControlDBvalue,
        database,
        recordlist,
        filespec.TIME_FILE_DEF,
    )
    if primary_record is None:
        return None
    time_control_record = timecontrolrecord.TimeControlDBrecord()
    time_control_record.load_record(primary_record)
    return time_control_record


def get_mode_name_from_identity(database, identity):
    """Return mode name for identity or None."""
    mode_record = None
    database.start_read_only_transaction()
    try:
        mode_record = get_mode_record_from_identity(database, identity)
    finally:
        database.end_read_only_transaction()
    if mode_record is None:
        return None
    return mode_record.value.alias_index_key()


def get_mode_record_from_identity(database, identity):
    """Return mode record for identity or None."""
    recordlist = database.recordlist_key(
        filespec.MODE_FILE_DEF,
        filespec.MODE_IDENTITY_FIELD_DEF,
        key=database.encode_record_selector(identity),
    )
    primary_record = identify_item.get_identity_item_on_recordlist(
        moderecord.ModeDBvalue,
        database,
        recordlist,
        filespec.MODE_FILE_DEF,
    )
    if primary_record is None:
        return None
    mode_record = moderecord.ModeDBrecord()
    mode_record.load_record(primary_record)
    return mode_record


def get_termination_name_from_identity(database, identity):
    """Return termination name for identity or None."""
    mode_record = None
    database.start_read_only_transaction()
    try:
        mode_record = get_termination_record_from_identity(database, identity)
    finally:
        database.end_read_only_transaction()
    if mode_record is None:
        return None
    return mode_record.value.alias_index_key()


def get_termination_record_from_identity(database, identity):
    """Return termination record for identity or None."""
    recordlist = database.recordlist_key(
        filespec.TERMINATION_FILE_DEF,
        filespec.TERMINATION_IDENTITY_FIELD_DEF,
        key=database.encode_record_selector(identity),
    )
    primary_record = identify_item.get_identity_item_on_recordlist(
        terminationrecord.TerminationDBvalue,
        database,
        recordlist,
        filespec.TERMINATION_FILE_DEF,
    )
    if primary_record is None:
        return None
    mode_record = terminationrecord.TerminationDBrecord()
    mode_record.load_record(primary_record)
    return mode_record


def get_player_type_name_from_identity(database, identity):
    """Return player type name for identity or None."""
    mode_record = None
    database.start_read_only_transaction()
    try:
        mode_record = get_player_type_record_from_identity(database, identity)
    finally:
        database.end_read_only_transaction()
    if mode_record is None:
        return None
    return mode_record.value.alias_index_key()


def get_player_type_record_from_identity(database, identity):
    """Return player type record for identity or None."""
    recordlist = database.recordlist_key(
        filespec.PLAYERTYPE_FILE_DEF,
        filespec.PLAYERTYPE_IDENTITY_FIELD_DEF,
        key=database.encode_record_selector(identity),
    )
    primary_record = identify_item.get_identity_item_on_recordlist(
        playertyperecord.PlayerTypeDBvalue,
        database,
        recordlist,
        filespec.PLAYERTYPE_FILE_DEF,
    )
    if primary_record is None:
        return None
    mode_record = playertyperecord.PlayerTypeDBrecord()
    mode_record.load_record(primary_record)
    return mode_record


def get_event_name_from_identity(database, identity):
    """Return event name for identity or None."""
    event_record = None
    database.start_read_only_transaction()
    try:
        event_record = get_event_record_from_identity(database, identity)
    finally:
        database.end_read_only_transaction()
    if event_record is None:
        return None
    return event_record.value.alias_index_key()


def get_event_record_from_identity(database, identity):
    """Return event record for identity or None."""
    recordlist = database.recordlist_key(
        filespec.EVENT_FILE_DEF,
        filespec.EVENT_IDENTITY_FIELD_DEF,
        key=database.encode_record_selector(identity),
    )
    primary_record = identify_item.get_identity_item_on_recordlist(
        eventrecord.EventDBvalue,
        database,
        recordlist,
        filespec.EVENT_FILE_DEF,
    )
    if primary_record is None:
        return None
    event_record = eventrecord.EventDBrecord()
    event_record.load_record(primary_record)
    return event_record
