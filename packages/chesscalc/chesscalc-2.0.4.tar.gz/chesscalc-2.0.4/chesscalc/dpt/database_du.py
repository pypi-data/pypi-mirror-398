# database_du.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance database deferred update using DPT via dpt."""

from solentware_base import dptdu_database
from solentware_base import dpt_database

from ..shared import litedu
from ..shared import alldu


class DPTDatabaseduError(Exception):
    """Exception class for dpt.database_du module."""


class Database(alldu.Alldu, litedu.Litedu, dptdu_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, databasefolder, **kargs):
        """Delegate with DPTDatabaseduError as exception class."""
        super().__init__(databasefolder, DPTDatabaseduError, **kargs)


class DatabaseSU(alldu.Alldu, litedu.Litedu, dpt_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, databasefolder, **kargs):
        """Delegate with DPTDatabaseduError as exception class."""
        super().__init__(databasefolder, DPTDatabaseduError, **kargs)
