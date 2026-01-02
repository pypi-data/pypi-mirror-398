# database.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Database methods common to all database engine interfaces."""

import os
import shutil

from .. import APPLICATION_NAME, ERROR_LOG, REPORT_DIRECTORY


class Database:
    """Provide methods common to all database engine interfaces."""

    # Non *_du database actions are done in separate threads by default,
    # not the main thread.  Override with 'can_use_thread = False' in
    # subclasses if necessary.
    # For SQLite3 the apsw interface is happy with the default, but the
    # sqlite3 interface gives a sqlite3.programmingerror exception.
    # For Berkeley DB the bsddb3 and berkeleydb interfaces are happy with
    # the default, but the tcl via tkinter interface gives a RuntimeError
    # exception.
    can_use_thread = True

    def use_deferred_update_process(self):
        """Return path to deferred update module."""
        return self._deferred_update_process

    def open_database(self, files=None):
        """Return '' to fit behaviour of dpt version of this method."""
        super().open_database(files=files)
        return ""

    def delete_database(self, names):
        """Delete database and return message about items not deleted."""
        listnames = set(n for n in os.listdir(self.home_directory))
        homenames = set(n for n in names if os.path.basename(n) in listnames)
        for name in (ERROR_LOG, REPORT_DIRECTORY):
            if name in listnames:
                homenames.add(name)
        if len(listnames - set(os.path.basename(h) for h in homenames)):
            message = "".join(
                (
                    "There is at least one file or folder in\n\n",
                    self.home_directory,
                    "\n\nwhich may not be part of the database.  These items ",
                    "have not been deleted by ",
                    APPLICATION_NAME,
                    ".",
                )
            )
        else:
            message = None
        self.close_database()
        for hnm in homenames:
            hnm = os.path.join(self.home_directory, hnm)
            if os.path.isdir(hnm):
                shutil.rmtree(hnm, ignore_errors=True)
            else:
                os.remove(hnm)
        try:
            os.rmdir(self.home_directory)
        except (FileNotFoundError, OSError):
            pass
        return message
