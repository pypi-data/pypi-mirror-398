# identify_event.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions to update event identification on database.

The functions support identifying an event as an existing event on the
database, or as separate event, and undoing these identifications too.

"""
from . import eventrecord
from . import filespec
from . import identify_item


def identify(database, bookmarks, selection, answer):
    """Make bookmarked events aliases of selection event on database.

    The bookmarked events must not be aliases already.

    The selection event can be aliased already.

    The changes are applied to database.

    """
    answer["message"] = identify_item.identify(
        database,
        {_event(database, *b) for b in bookmarks},
        [_event(database, *s) for s in selection],
        eventrecord.EventDBvalue,
        eventrecord.EventDBrecord,
        filespec.EVENT_FILE_DEF,
        filespec.EVENT_FIELD_DEF,
        filespec.EVENT_ALIAS_FIELD_DEF,
        filespec.EVENT_IDENTITY_FIELD_DEF,
        "event",
    )


def break_bookmarked_aliases(database, bookmarks, selection, answer):
    """Break aliases of selection event in bookmarks on database.

    The bookmarked aliases of selection become separate events.

    The changes are applied to database.

    """
    answer["message"] = identify_item.break_bookmarked_aliases(
        database,
        {_event(database, *b) for b in bookmarks},
        [_event(database, *s) for s in selection],
        eventrecord.EventDBvalue,
        eventrecord.EventDBrecord,
        filespec.EVENT_FILE_DEF,
        filespec.EVENT_FIELD_DEF,
        filespec.EVENT_ALIAS_FIELD_DEF,
        filespec.EVENT_IDENTITY_FIELD_DEF,
        "event",
    )


def split_aliases(database, selection, answer):
    """Split aliases of selection event into separate events on database.

    The changes are applied to database.

    """
    answer["message"] = identify_item.split_aliases(
        database,
        [_event(database, *s) for s in selection],
        eventrecord.EventDBvalue,
        eventrecord.EventDBrecord,
        filespec.EVENT_FILE_DEF,
        filespec.EVENT_FIELD_DEF,
        filespec.EVENT_ALIAS_FIELD_DEF,
        filespec.EVENT_IDENTITY_FIELD_DEF,
        "event",
    )


def change_aliases(database, selection, answer):
    """Change alias of all events with same alias as selection on database.

    All events with same alias as selection have their alias changed to
    identity of selection event.

    The changes are applied to database.

    """
    answer["message"] = identify_item.change_aliases(
        database,
        [_event(database, *s) for s in selection],
        eventrecord.EventDBvalue,
        eventrecord.EventDBrecord,
        filespec.EVENT_FILE_DEF,
        filespec.EVENT_FIELD_DEF,
        filespec.EVENT_ALIAS_FIELD_DEF,
        filespec.EVENT_IDENTITY_FIELD_DEF,
        "event",
    )


def _event(database, name, record_number):
    """Return fule name of event and record number for record number.

    Events are sorted for display by name.  Identify actions need the
    full name of the event which can be found by looking up the
    record number.

    """
    database.start_read_only_transaction()
    try:
        recordlist = database.recordlist_record_number(
            filespec.EVENT_FILE_DEF, key=record_number
        )
        primary_record = identify_item.get_first_item_on_recordlist(
            database, recordlist, filespec.EVENT_FILE_DEF
        )
    finally:
        database.end_read_only_transaction()
    event_record = eventrecord.EventDBrecord()
    event_record.load_record(primary_record)
    assert name == event_record.value.event
    return (event_record.value.alias_index_key(), record_number)
