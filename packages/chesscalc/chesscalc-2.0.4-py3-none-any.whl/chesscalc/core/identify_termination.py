# identify_termination.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions to update termination reason identification on database.

The termination reasons are descriptive of the way a game ended.  Relevant
reasons here are 'dafault' and 'bye', for example.

The functions support identifying a termination reason as an existing
termination reason on the database, or as separate termination reason, and
undoing these identifications too.

"""
from . import terminationrecord
from . import filespec
from . import identify_item


class TerminationIdentity(Exception):
    """Raise if unable to change alias used as termination identity."""


def identify(database, bookmarks, selection, answer):
    """Make bookmarked terminations aliases of selection mode.

    The bookmarked terminations must not be aliases already.

    The selection termination can be aliased already.

    The changes are applied to database.

    """
    answer["message"] = identify_item.identify(
        database,
        bookmarks,
        selection,
        terminationrecord.TerminationDBvalue,
        terminationrecord.TerminationDBrecord,
        filespec.TERMINATION_FILE_DEF,
        filespec.TERMINATION_FIELD_DEF,
        filespec.TERMINATION_ALIAS_FIELD_DEF,
        filespec.TERMINATION_IDENTITY_FIELD_DEF,
        "termination",
    )


def break_bookmarked_aliases(database, bookmarks, selection, answer):
    """Break aliases of selection termination in bookmarks.

    The bookmarked aliases of selection become separate terminations.

    The changes are applied to database.

    """
    answer["message"] = identify_item.break_bookmarked_aliases(
        database,
        bookmarks,
        selection,
        terminationrecord.TerminationDBvalue,
        terminationrecord.TerminationDBrecord,
        filespec.TERMINATION_FILE_DEF,
        filespec.TERMINATION_FIELD_DEF,
        filespec.TERMINATION_ALIAS_FIELD_DEF,
        filespec.TERMINATION_IDENTITY_FIELD_DEF,
        "termination",
    )


def split_aliases(database, selection, answer):
    """Split aliases of selection termination into separate terminations.

    The changes are applied to database.

    """
    answer["message"] = identify_item.split_aliases(
        database,
        selection,
        terminationrecord.TerminationDBvalue,
        terminationrecord.TerminationDBrecord,
        filespec.TERMINATION_FILE_DEF,
        filespec.TERMINATION_FIELD_DEF,
        filespec.TERMINATION_ALIAS_FIELD_DEF,
        filespec.TERMINATION_IDENTITY_FIELD_DEF,
        "termination",
    )


def change_aliases(database, selection, answer):
    """Change alias of all terminations with same alias as selection.

    All terminations with same alias as selection have their alias changed
    to identity of selection termination.

    The changes are applied to database.

    """
    answer["message"] = identify_item.change_aliases(
        database,
        selection,
        terminationrecord.TerminationDBvalue,
        terminationrecord.TerminationDBrecord,
        filespec.TERMINATION_FILE_DEF,
        filespec.TERMINATION_FIELD_DEF,
        filespec.TERMINATION_ALIAS_FIELD_DEF,
        filespec.TERMINATION_IDENTITY_FIELD_DEF,
        "termination",
    )
