# database.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess Performance Calculation database using Symas LMMD via lmdb."""

from solentware_base import lmdb_database

from ..core.filespec import FileSpec
from ..basecore import database


class Database(database.Database, lmdb_database.Database):
    """Methods and data structures to create, open, and close database."""

    _deferred_update_process = "chesscalc.lmdb.database_du"

    def __init__(
        self,
        DBfile,
        use_specification_items=None,
        dpt_records=None,
        **kargs,
    ):
        """Define database specification then delegate."""
        dbnames = FileSpec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )

        super().__init__(
            dbnames,
            DBfile,
            use_specification_items=use_specification_items,
            **kargs,
        )

        # Hopefully this is enough for normal use.
        # Not doing this at all leaves no room for amendments.
        self._set_map_blocks_above_used_pages(100)

    def delete_database(self):
        """Close and delete the open chess results database."""
        return super().delete_database(
            (self.database_file, "-".join((self.database_file, "lock")))
        )

    # Not doing this at all may make no difference (not necessary).
    def checkpoint_before_close_dbenv(self):
        """Override.  Hijack method to set map size to file size.

        Reverse, to the extent possible, the increase in map size done
        when the database was opened.

        """
        self._set_map_size_above_used_pages_between_transactions(0)
