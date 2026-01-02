# identify_timecontrol.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions to update time control identification on database.

The functions support identifying a time control as an existing time control
on the database, or as separate time control, and undoing these
identifications too.

"""
from . import timecontrolrecord
from . import filespec
from . import identify_item


def identify(database, bookmarks, selection, answer):
    """Make bookmarked time controls aliases of selection time control.

    The bookmarked time controls must not be aliases already.

    The selection time control can be aliased already.

    The changes are applied to database.

    """
    answer["message"] = identify_item.identify(
        database,
        bookmarks,
        selection,
        timecontrolrecord.TimeControlDBvalue,
        timecontrolrecord.TimeControlDBrecord,
        filespec.TIME_FILE_DEF,
        filespec.TIME_FIELD_DEF,
        filespec.TIME_ALIAS_FIELD_DEF,
        filespec.TIME_IDENTITY_FIELD_DEF,
        "time control",
    )


def break_bookmarked_aliases(database, bookmarks, selection, answer):
    """Break aliases of selection time control in bookmarks.

    The bookmarked aliases of selection become separate time controls.

    The changes are applied to database.

    """
    answer["message"] = identify_item.break_bookmarked_aliases(
        database,
        bookmarks,
        selection,
        timecontrolrecord.TimeControlDBvalue,
        timecontrolrecord.TimeControlDBrecord,
        filespec.TIME_FILE_DEF,
        filespec.TIME_FIELD_DEF,
        filespec.TIME_ALIAS_FIELD_DEF,
        filespec.TIME_IDENTITY_FIELD_DEF,
        "time control",
    )


def split_aliases(database, selection, answer):
    """Split aliases of selection time control into separate time controls.

    The changes are applied to database.

    """
    answer["message"] = identify_item.split_aliases(
        database,
        selection,
        timecontrolrecord.TimeControlDBvalue,
        timecontrolrecord.TimeControlDBrecord,
        filespec.TIME_FILE_DEF,
        filespec.TIME_FIELD_DEF,
        filespec.TIME_ALIAS_FIELD_DEF,
        filespec.TIME_IDENTITY_FIELD_DEF,
        "time control",
    )


def change_aliases(database, selection, answer):
    """Change alias of all time controls with same alias as selection.

    All time controls with same alias as selection have their alias changed to
    identity of selection time control.

    The changes are applied to database.

    """
    answer["message"] = identify_item.change_aliases(
        database,
        selection,
        timecontrolrecord.TimeControlDBvalue,
        timecontrolrecord.TimeControlDBrecord,
        filespec.TIME_FILE_DEF,
        filespec.TIME_FIELD_DEF,
        filespec.TIME_ALIAS_FIELD_DEF,
        filespec.TIME_IDENTITY_FIELD_DEF,
        "time control",
    )
