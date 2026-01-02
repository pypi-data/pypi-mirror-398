# timecontrols.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""List the time controls in the database."""

import tkinter

from solentware_bind.gui.bindings import Bindings

from . import timecontrolsgrid
from .eventspec import EventSpec
from ..core import identify_timecontrol
from ..shared import task


class TimeControlsError(Exception):
    """Raise exception in timecontrols module."""


class TimeControls(Bindings):
    """Define widgets which list time controls of games."""

    def __init__(self, master, database):
        """Create the time controls widget."""
        super().__init__()
        self._time_limits_grid = timecontrolsgrid.TimeControlsGrid(
            parent=master, database=database
        )

    @property
    def frame(self):
        """Return the top frame of the time controls widget."""
        return self._time_limits_grid.frame

    @property
    def data_grid(self):
        """Return the time controls widget."""
        return self._time_limits_grid

    def identify(self, update_widget_and_join_loop):
        """Identify bookmarked time controls as selected time control."""
        title = EventSpec.menu_other_time_identify[1]
        database = self.get_database(title)
        if not database:
            return None
        time_controls_sel = self._time_limits_grid.selection
        time_controls_bmk = self._time_limits_grid.bookmarks
        if len(time_controls_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No time control is selected",
            )
            return False
        if len(time_controls_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No time controls are bookmarked so no changes done",
            )
            return False
        if time_controls_bmk == time_controls_sel:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Selection and bookmark is same so no changes done",
            )
            return False
        new = set(time_controls_bmk)
        if new.intersection(time_controls_sel):
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Selection is one of bookmarked time controls ",
                        "so no changes done",
                    )
                ),
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_timecontrol.identify,
            (database, new, time_controls_sel, answer),
            update_widget_and_join_loop,
        ).start_and_join()
        if answer["message"]:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message=answer["message"],
            )
            return False
        return True

    def break_selected(self, update_widget_and_join_loop):
        """Undo identification of bookmarked time controls as selection."""
        title = EventSpec.menu_other_time_break[1]
        database = self.get_database(title)
        if not database:
            return None
        time_controls_sel = self._time_limits_grid.selection
        time_controls_bmk = self._time_limits_grid.bookmarks
        if len(time_controls_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No time control is selected",
            )
            return False
        if len(time_controls_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No time controls are bookmarked so no changes done",
            )
            return False
        if time_controls_bmk == time_controls_sel:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Selection and bookmark is same so no changes done",
            )
            return False
        new = set(time_controls_bmk)
        if new.intersection(time_controls_sel):
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Selection is one of bookmarked time controls ",
                        "so no changes done",
                    )
                ),
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_timecontrol.break_bookmarked_aliases,
            (database, new, time_controls_sel, answer),
            update_widget_and_join_loop,
        ).start_and_join()
        if answer["message"]:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message=answer["message"],
            )
            return False
        return True

    def split_all(self, update_widget_and_join_loop):
        """Undo identification of all aliases of selected time control."""
        title = EventSpec.menu_other_time_split[1]
        database = self.get_database(title)
        if not database:
            return None
        time_controls_sel = self._time_limits_grid.selection
        time_controls_bmk = self._time_limits_grid.bookmarks
        if len(time_controls_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No time control is selected",
            )
            return False
        if len(time_controls_bmk) != 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Time controls are bookmarked so no changes done",
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_timecontrol.split_aliases,
            (database, time_controls_sel, answer),
            update_widget_and_join_loop,
        ).start_and_join()
        if answer["message"]:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message=answer["message"],
            )
            return False
        return True

    def change_identity(self, update_widget_and_join_loop):
        """Undo identification of all aliases of selected time control."""
        title = EventSpec.menu_other_time_change[1]
        database = self.get_database(title)
        if not database:
            return None
        time_controls_sel = self._time_limits_grid.selection
        time_controls_bmk = self._time_limits_grid.bookmarks
        if len(time_controls_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No time control is selected",
            )
            return False
        if len(time_controls_bmk) != 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Time controls are bookmarked so no changes done",
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_timecontrol.change_aliases,
            (database, time_controls_sel, answer),
            update_widget_and_join_loop,
        ).start_and_join()
        if answer["message"]:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message=answer["message"],
            )
            return False
        return True

    def get_database(self, title):
        """Return database if time controls list is attached to database.

        Return False otherwise after dialogue indicating problem.

        """
        time_controls_ds = self._time_limits_grid.datasource
        if time_controls_ds is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Time controls list ",
                        "is not attached to database at present",
                    )
                ),
            )
            return False
        time_controls_db = time_controls_ds.dbhome
        if time_controls_db is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Time controls list ",
                        "is not attached to database index at present",
                    )
                ),
            )
            return False
        return time_controls_db
