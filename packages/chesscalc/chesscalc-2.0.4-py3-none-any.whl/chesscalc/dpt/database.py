# database.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess Performance Calculation database using DPT via dptdb.dptapi."""

import os

from solentware_base.core import constants

from . import dptnofistat
from .. import APPLICATION_NAME


class Database(dptnofistat.Database):
    """Provide access to a database of results of games of chess.

    The open_database() method is extended in a number of ways, all but
    one with a new name.  These methods take the FISTAT flags into
    account when attempting to open the database.
    """

    def __init__(self, *args, **kwargs):
        """Define chess database.

        See superclass for argument descriptions.

        """
        super().__init__(*args, **kwargs)

    def open_database(self, files=None):
        """Return "" if all files are opened in Normal mode (FISTAT == 0).

        Close database and return a report (str != "") if any files are
        not in Normal mode.

        """
        super().open_database(files=files)
        fistat = {}
        for dbo in self.table.values():
            fistat[dbo] = dbo.get_file_parameters(self.dbenv)["FISTAT"]
        for dbo in self.table.values():
            if fistat[dbo][0] != 0:
                break
        else:
            self.increase_database_size(files=None)
            return ""

        # At least one file is not in Normal state.
        report = "\n".join(
            [
                "\t".join((os.path.basename(dbo.file), fistat[dbo][1]))
                for dbo in self.table.values()
            ]
        )
        self.close_database()
        return "".join(
            (
                APPLICATION_NAME,
                " opened the database with file states\n\n",
                report,
                "\n\n",
                APPLICATION_NAME,
                " then closed the database because some of the files ",
                "are not in the Normal state.\n\nRestore the database ",
                "from backups, or source data, before trying again.",
            )
        )

    def delete_database(self):
        """Close and delete the open chess results database."""
        return super().delete_database(
            [spec[constants.FILE] for spec in self.specification.values()]
            + [
                constants.DPT_SYS_FOLDER,
                constants.DPT_SYSDU_FOLDER,
                constants.DPT_SYSFL_FOLDER,
                constants.DPT_SYSFUL_FOLDER,
                constants.DPT_SYSCOPY_FOLDER,
            ]
        )
