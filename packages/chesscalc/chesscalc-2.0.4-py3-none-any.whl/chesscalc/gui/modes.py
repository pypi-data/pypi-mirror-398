# modes.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""List the modes in the database.

The modes are ways of conducting the game, such as 'over the board' (OTB)
or 'online'.

"""
import tkinter

from solentware_bind.gui.bindings import Bindings

from . import modesgrid
from .eventspec import EventSpec
from ..core import identify_mode
from ..shared import task


class ModesError(Exception):
    """Raise exception in modes module."""


class Modes(Bindings):
    """Define widgets which list modes of games."""

    def __init__(self, master, database):
        """Create the modes widget."""
        super().__init__()
        self._modes_grid = modesgrid.ModesGrid(
            parent=master, database=database
        )

    @property
    def frame(self):
        """Return the top frame of the modes widget."""
        return self._modes_grid.frame

    @property
    def data_grid(self):
        """Return the modes widget."""
        return self._modes_grid

    def identify(self, update_widget_and_join_loop):
        """Identify bookmarked modes as selected mode."""
        title = EventSpec.menu_other_mode_identify[1]
        database = self.get_database(title)
        if not database:
            return None
        modes_sel = self._modes_grid.selection
        modes_bmk = self._modes_grid.bookmarks
        if len(modes_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No mode is selected",
            )
            return False
        if len(modes_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No modes are bookmarked so no changes done",
            )
            return False
        if modes_bmk == modes_sel:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Selection and bookmark is same so no changes done",
            )
            return False
        new = set(modes_bmk)
        if new.intersection(modes_sel):
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Selection is one of bookmarked modes ",
                        "so no changes done",
                    )
                ),
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_mode.identify,
            (database, new, modes_sel, answer),
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
        """Undo identification of bookmarked modes as selection."""
        title = EventSpec.menu_other_mode_break[1]
        database = self.get_database(title)
        if not database:
            return None
        modes_sel = self._modes_grid.selection
        modes_bmk = self._modes_grid.bookmarks
        if len(modes_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No mode is selected",
            )
            return False
        if len(modes_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No modes are bookmarked so no changes done",
            )
            return False
        if modes_bmk == modes_sel:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Selection and bookmark is same so no changes done",
            )
            return False
        new = set(modes_bmk)
        if new.intersection(modes_sel):
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Selection is one of bookmarked modes ",
                        "so no changes done",
                    )
                ),
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_mode.break_bookmarked_aliases,
            (database, new, modes_sel, answer),
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
        """Undo identification of all aliases of selected mode."""
        title = EventSpec.menu_other_mode_split[1]
        database = self.get_database(title)
        if not database:
            return None
        modes_sel = self._modes_grid.selection
        modes_bmk = self._modes_grid.bookmarks
        if len(modes_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No mode is selected",
            )
            return False
        if len(modes_bmk) != 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Modes are bookmarked so no changes done",
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_mode.split_aliases,
            (database, modes_sel, answer),
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
        """Undo identification of all aliases of selected mode."""
        title = EventSpec.menu_other_mode_change[1]
        database = self.get_database(title)
        if not database:
            return None
        modes_sel = self._modes_grid.selection
        modes_bmk = self._modes_grid.bookmarks
        if len(modes_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No mode is selected",
            )
            return False
        if len(modes_bmk) != 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Modes are bookmarked so no changes done",
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_mode.change_aliases,
            (database, modes_sel, answer),
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
        """Return database if modes list is attached to database.

        Return False otherwise after dialogue indicating problem.

        """
        modes_ds = self._modes_grid.datasource
        if modes_ds is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Modes list ",
                        "is not attached to database at present",
                    )
                ),
            )
            return False
        modes_db = modes_ds.dbhome
        if modes_db is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Modes list ",
                        "is not attached to database index at present",
                    )
                ),
            )
            return False
        return modes_db
