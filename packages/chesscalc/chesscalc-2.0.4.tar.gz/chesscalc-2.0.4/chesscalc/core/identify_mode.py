# identify_mode.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions to update mode identification on database.

The modes are ways of conducting the game, such as 'over the board' (OTB)
or 'online'.

The functions support identifying a mode as an existing mode
on the database, or as separate mode, and undoing these
identifications too.

"""
from . import moderecord
from . import filespec
from . import identify_item


class ModeIdentity(Exception):
    """Raise if unable to change alias used as mode identity."""


def identify(database, bookmarks, selection, answer):
    """Make bookmarked modes aliases of selection mode.

    The bookmarked modes must not be aliases already.

    The selection mode can be aliased already.

    The changes are applied to database.

    """
    answer["message"] = identify_item.identify(
        database,
        bookmarks,
        selection,
        moderecord.ModeDBvalue,
        moderecord.ModeDBrecord,
        filespec.MODE_FILE_DEF,
        filespec.MODE_FIELD_DEF,
        filespec.MODE_ALIAS_FIELD_DEF,
        filespec.MODE_IDENTITY_FIELD_DEF,
        "mode",
    )


def break_bookmarked_aliases(database, bookmarks, selection, answer):
    """Break aliases of selection mode in bookmarks.

    The bookmarked aliases of selection become separate modes.

    The changes are applied to database.

    """
    answer["message"] = identify_item.break_bookmarked_aliases(
        database,
        bookmarks,
        selection,
        moderecord.ModeDBvalue,
        moderecord.ModeDBrecord,
        filespec.MODE_FILE_DEF,
        filespec.MODE_FIELD_DEF,
        filespec.MODE_ALIAS_FIELD_DEF,
        filespec.MODE_IDENTITY_FIELD_DEF,
        "mode",
    )


def split_aliases(database, selection, answer):
    """Split aliases of selection mode into separate modes.

    The changes are applied to database.

    """
    answer["message"] = identify_item.split_aliases(
        database,
        selection,
        moderecord.ModeDBvalue,
        moderecord.ModeDBrecord,
        filespec.MODE_FILE_DEF,
        filespec.MODE_FIELD_DEF,
        filespec.MODE_ALIAS_FIELD_DEF,
        filespec.MODE_IDENTITY_FIELD_DEF,
        "mode",
    )


def change_aliases(database, selection, answer):
    """Change alias of all modes with same alias as selection.

    All modes with same alias as selection have their alias changed
    to identity of selection mode.

    The changes are applied to database.

    """
    answer["message"] = identify_item.change_aliases(
        database,
        selection,
        moderecord.ModeDBvalue,
        moderecord.ModeDBrecord,
        filespec.MODE_FILE_DEF,
        filespec.MODE_FIELD_DEF,
        filespec.MODE_ALIAS_FIELD_DEF,
        filespec.MODE_IDENTITY_FIELD_DEF,
        "mode",
    )
