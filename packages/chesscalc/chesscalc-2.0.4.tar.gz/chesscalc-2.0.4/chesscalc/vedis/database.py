# database.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess Performance Calculation database using NoSQL style via vedis."""

from solentware_base import vedis_database

from ..core.filespec import FileSpec
from ..basecore import database


class Database(database.Database, vedis_database.Database):
    """Methods and data structures to create, open, and close database."""

    _deferred_update_process = "chesscalc.vedis.database_du"

    def __init__(
        self,
        nosqlfile,
        use_specification_items=None,
        dpt_records=None,
        **kargs,
    ):
        """Define database specification then delegate."""
        names = FileSpec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )

        super().__init__(
            names,
            nosqlfile,
            use_specification_items=use_specification_items,
            **kargs,
        )

    def delete_database(self):
        """Close and delete the open chess results database."""
        return super().delete_database(
            (
                self.database_file,
                "-".join((self.database_file, "lock")),
                "_".join((self.database_file, "vedis", "journal")),
            )
        )
