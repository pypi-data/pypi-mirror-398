# dbdu.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""The Dbdu class for methods shared by Berkeley DB interface modules.

This module is relevant to the berkeleydb, bsddb3, and tcl, interfaces to
Berkeley DB.

"""
from ..core import constants
from .litedu import Litedu


class Dbdu(Litedu):
    """Provide deferred update methods shared by the Berkeley DB interfaces.

    The methods provided by Litedu are shared with engines other than
    Berkeley DB.

    The whole database can be put in a single file, or each table (called a
    database in Berkeley DB terminology) in the database can be put in a
    file of it's own.
    """

    def __init__(self, databasefile, exception_class, flags, **kargs):
        """Define chess database.

        **kargs
        allowcreate == False - remove file descriptions from FileSpec so
        that superclass cannot create them.
        Other arguments are passed through to superclass __init__.

        """
        environment = {
            "flags": flags,
            "gbytes": constants.DB_ENVIRONMENT_GIGABYTES,
            "bytes": constants.DB_ENVIRONMENT_BYTES,
            "maxlocks": constants.DB_ENVIRONMENT_MAXLOCKS,
            "maxobjects": constants.DB_ENVIRONMENT_MAXOBJECTS,
        }
        super().__init__(
            databasefile, exception_class, environment=environment, **kargs
        )
