# database.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess Performance Calculation database on Berkeley DB via tkinter API."""

from solentware_base import db_tkinter_database

from ..core.filespec import FileSpec
from ..basecore import database


class Database(database.Database, db_tkinter_database.Database):
    """Methods and data structures to create, open, and close database."""

    _deferred_update_process = "chesscalc.db_tkinter.database_du"

    # The tcl via tkinter interface gives a RuntimeError exception if
    # database actions are not done in the main thread.
    can_use_thread = False

    def __init__(
        self,
        DBfile,
        use_specification_items=None,
        dpt_records=None,
        **kargs,
    ):
        """Define database specification and environment then delegate."""
        dbnames = FileSpec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )

        environment = {
            "flags": (
                "-create",
                "-recover",
                "-txn",
                "-private",
                "-system_mem",
            ),
        }

        super().__init__(
            dbnames,
            folder=DBfile,
            environment=environment,
            use_specification_items=use_specification_items,
            **kargs,
        )

    def delete_database(self):
        """Close and delete the open chess results database."""
        return super().delete_database(
            (
                self.database_file,
                "-".join((self.database_file, "lock")),
                self._get_log_dir_name(),
            )
        )
