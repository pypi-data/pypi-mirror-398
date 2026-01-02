# playertypes.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""List the player types in the database.

Two player types are expected, 'human' and 'computer', but there is no ban
on others.

"""
import tkinter

from solentware_bind.gui.bindings import Bindings

from . import playertypesgrid
from .eventspec import EventSpec
from ..core import identify_playertype
from ..shared import task


class PlayerTypesError(Exception):
    """Raise exception in playertypes module."""


class PlayerTypes(Bindings):
    """Define widgets which list player types of games."""

    def __init__(self, master, database):
        """Create the playertypes widget."""
        super().__init__()
        self._playertypes_grid = playertypesgrid.PlayerTypesGrid(
            parent=master, database=database
        )

    @property
    def frame(self):
        """Return the top frame of the playertypes widget."""
        return self._playertypes_grid.frame

    @property
    def data_grid(self):
        """Return the playertypes widget."""
        return self._playertypes_grid

    def identify(self, update_widget_and_join_loop):
        """Identify bookmarked player types as selected player type."""
        title = EventSpec.menu_other_playertype_identify[1]
        database = self.get_database(title)
        if not database:
            return None
        playertypes_sel = self._playertypes_grid.selection
        playertypes_bmk = self._playertypes_grid.bookmarks
        if len(playertypes_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No player type is selected",
            )
            return False
        if len(playertypes_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No player types are bookmarked so no changes done",
            )
            return False
        if playertypes_bmk == playertypes_sel:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Selection and bookmark is same so no changes done",
            )
            return False
        new = set(playertypes_bmk)
        if new.intersection(playertypes_sel):
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Selection is one of bookmarked player types ",
                        "so no changes done",
                    )
                ),
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_playertype.identify,
            (database, new, playertypes_sel, answer),
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
        """Undo identification of bookmarked player types as selection."""
        title = EventSpec.menu_other_playertype_break[1]
        database = self.get_database(title)
        if not database:
            return None
        playertypes_sel = self._playertypes_grid.selection
        playertypes_bmk = self._playertypes_grid.bookmarks
        if len(playertypes_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No player type is selected",
            )
            return False
        if len(playertypes_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No player types are bookmarked so no changes done",
            )
            return False
        if playertypes_bmk == playertypes_sel:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Selection and bookmark is same so no changes done",
            )
            return False
        new = set(playertypes_bmk)
        if new.intersection(playertypes_sel):
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Selection is one of bookmarked player types ",
                        "so no changes done",
                    )
                ),
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_playertype.break_bookmarked_aliases,
            (database, new, playertypes_sel, answer),
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
        """Undo identification of all aliases of selected player type."""
        title = EventSpec.menu_other_playertype_split[1]
        database = self.get_database(title)
        if not database:
            return None
        playertypes_sel = self._playertypes_grid.selection
        playertypes_bmk = self._playertypes_grid.bookmarks
        if len(playertypes_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No player type is selected",
            )
            return False
        if len(playertypes_bmk) != 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Player types are bookmarked so no changes done",
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_playertype.split_aliases,
            (database, playertypes_sel, answer),
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
        """Undo identification of all aliases of selected player type."""
        title = EventSpec.menu_other_playertype_change[1]
        database = self.get_database(title)
        if not database:
            return None
        playertypes_sel = self._playertypes_grid.selection
        playertypes_bmk = self._playertypes_grid.bookmarks
        if len(playertypes_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No player type is selected",
            )
            return False
        if len(playertypes_bmk) != 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Player types are bookmarked so no changes done",
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_playertype.change_aliases,
            (database, playertypes_sel, answer),
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
        """Return database if player types list is attached to database.

        Return False otherwise after dialogue indicating problem.

        """
        playertypes_ds = self._playertypes_grid.datasource
        if playertypes_ds is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Player types list ",
                        "is not attached to database at present",
                    )
                ),
            )
            return False
        playertypes_db = playertypes_ds.dbhome
        if playertypes_db is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Player types list ",
                        "is not attached to database index at present",
                    )
                ),
            )
            return False
        return playertypes_db
