# identify_playertype.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions to update playertype identification on database.

The playertypes are expected to be 'human' or 'computer'.

The functions support identifying a player type as an existing player type
on the database, or as separate player type, and undoing these
identifications too.

"""
from . import playertyperecord
from . import filespec
from . import identify_item


class ModeIdentity(Exception):
    """Raise if unable to change alias used as playertype identity."""


def identify(database, bookmarks, selection, answer):
    """Make bookmarked playertypes aliases of selection playertype.

    The bookmarked playertypes must not be aliases already.

    The selection playertype can be aliased already.

    The changes are applied to database.

    """
    answer["message"] = identify_item.identify(
        database,
        bookmarks,
        selection,
        playertyperecord.PlayerTypeDBvalue,
        playertyperecord.PlayerTypeDBrecord,
        filespec.PLAYERTYPE_FILE_DEF,
        filespec.PLAYERTYPE_FIELD_DEF,
        filespec.PLAYERTYPE_ALIAS_FIELD_DEF,
        filespec.PLAYERTYPE_IDENTITY_FIELD_DEF,
        "playertype",
    )


def break_bookmarked_aliases(database, bookmarks, selection, answer):
    """Break aliases of selection playertype in bookmarks.

    The bookmarked aliases of selection become separate modes.

    The changes are applied to database.

    """
    answer["message"] = identify_item.break_bookmarked_aliases(
        database,
        bookmarks,
        selection,
        playertyperecord.PlayerTypeDBvalue,
        playertyperecord.PlayerTypeDBrecord,
        filespec.PLAYERTYPE_FILE_DEF,
        filespec.PLAYERTYPE_FIELD_DEF,
        filespec.PLAYERTYPE_ALIAS_FIELD_DEF,
        filespec.PLAYERTYPE_IDENTITY_FIELD_DEF,
        "playertype",
    )


def split_aliases(database, selection, answer):
    """Split aliases of selection playertype into separate playertypes.

    The changes are applied to database.

    """
    answer["message"] = identify_item.split_aliases(
        database,
        selection,
        playertyperecord.PlayerTypeDBvalue,
        playertyperecord.PlayerTypeDBrecord,
        filespec.PLAYERTYPE_FILE_DEF,
        filespec.PLAYERTYPE_FIELD_DEF,
        filespec.PLAYERTYPE_ALIAS_FIELD_DEF,
        filespec.PLAYERTYPE_IDENTITY_FIELD_DEF,
        "playertype",
    )


def change_aliases(database, selection, answer):
    """Change alias of all playertypes with same alias as selection.

    All playertypes with same alias as selection have their alias changed
    to identity of selection playertype.

    The changes are applied to database.

    """
    answer["message"] = identify_item.change_aliases(
        database,
        selection,
        playertyperecord.PlayerTypeDBvalue,
        playertyperecord.PlayerTypeDBrecord,
        filespec.PLAYERTYPE_FILE_DEF,
        filespec.PLAYERTYPE_FIELD_DEF,
        filespec.PLAYERTYPE_ALIAS_FIELD_DEF,
        filespec.PLAYERTYPE_IDENTITY_FIELD_DEF,
        "playertype",
    )
