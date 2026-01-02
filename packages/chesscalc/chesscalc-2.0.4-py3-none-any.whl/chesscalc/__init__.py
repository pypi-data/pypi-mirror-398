# __init__.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Calculate player's performances on a set of games.

Performances are calculated by iteration where each player starts with 0 as
their performance.  The scale used is +50 for a win, -50 for a loss, and 0 for
a draw, relative to the opponents performance.  English Chess Federation (ECF)
grades have the same scale.

The performances are not grades because the results of calculations in previous
runs are not used in this calculation.

"""
import os
import datetime
import traceback

import solentware_base.core.constants as sb_c_constants

APPLICATION_NAME = "ChessPerfCalc"
ERROR_LOG = "ErrorLog"
REPORT_DIRECTORY = "_reports"

# Map database module names to application module
APPLICATION_DATABASE_MODULE = {
    sb_c_constants.BERKELEYDB_MODULE: __name__ + ".berkeleydb.database",
    sb_c_constants.BSDDB3_MODULE: __name__ + ".db.database",
    sb_c_constants.SQLITE3_MODULE: __name__ + ".sqlite.database",
    sb_c_constants.APSW_MODULE: __name__ + ".apsw.database",
    sb_c_constants.DPT_MODULE: __name__ + ".dpt.database",
    sb_c_constants.UNQLITE_MODULE: __name__ + ".unqlite.database",
    sb_c_constants.VEDIS_MODULE: __name__ + ".vedis.database",
    sb_c_constants.DB_TCL_MODULE: __name__ + ".db_tkinter.database",
    sb_c_constants.LMDB_MODULE: __name__ + ".lmdb.database",
}

del sb_c_constants


def write_error_to_log(directory):
    """Write the exception to the error log with a time stamp.

    Consider using the ExceptionHandler.report_exception(...) method if
    the write_error_to_log() call is in an instance of a subclass of the
    solentware_bind.gui.exceptionhandler.ExceptionHandler class.

    """
    with open(
        os.path.join(directory, ERROR_LOG),
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            "".join(
                (
                    "\n\n\n",
                    " ".join(
                        (
                            APPLICATION_NAME,
                            "exception report at",
                            datetime.datetime.now().isoformat(),
                        )
                    ),
                    "\n\n",
                    traceback.format_exc(),
                    "\n\n",
                )
            )
        )
