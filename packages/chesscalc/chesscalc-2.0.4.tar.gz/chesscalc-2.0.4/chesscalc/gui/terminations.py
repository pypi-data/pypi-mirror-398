# terminations.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""List the game termination reasons in the database.

The termination reason defaults to 'normal'.  Plausible alternatives are
'default' and 'bye', but why would such a game exist in a PGN file?

Perhaps to confirm an expected game did not occur.

"""
import tkinter

from solentware_bind.gui.bindings import Bindings

from . import terminationsgrid
from .eventspec import EventSpec
from ..core import identify_termination
from ..shared import task


class TerminationsError(Exception):
    """Raise exception in terminations module."""


class Terminations(Bindings):
    """Define widgets which list terminations of games."""

    def __init__(self, master, database):
        """Create the terminations widget."""
        super().__init__()
        self._terminations_grid = terminationsgrid.TerminationsGrid(
            parent=master, database=database
        )

    @property
    def frame(self):
        """Return the top frame of the terminations widget."""
        return self._terminations_grid.frame

    @property
    def data_grid(self):
        """Return the terminations widget."""
        return self._terminations_grid

    def identify(self, update_widget_and_join_loop):
        """Identify bookmarked terminations as selected termination."""
        title = EventSpec.menu_other_termination_identify[1]
        database = self.get_database(title)
        if not database:
            return None
        terminations_sel = self._terminations_grid.selection
        terminations_bmk = self._terminations_grid.bookmarks
        if len(terminations_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No termination is selected",
            )
            return False
        if len(terminations_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No terminations are bookmarked so no changes done",
            )
            return False
        if terminations_bmk == terminations_sel:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Selection and bookmark is same so no changes done",
            )
            return False
        new = set(terminations_bmk)
        if new.intersection(terminations_sel):
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Selection is one of bookmarked terminations ",
                        "so no changes done",
                    )
                ),
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_termination.identify,
            (database, new, terminations_sel, answer),
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
        """Undo identification of bookmarked terminations as selection."""
        title = EventSpec.menu_other_termination_break[1]
        database = self.get_database(title)
        if not database:
            return None
        terminations_sel = self._terminations_grid.selection
        terminations_bmk = self._terminations_grid.bookmarks
        if len(terminations_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No termination is selected",
            )
            return False
        if len(terminations_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No terminations are bookmarked so no changes done",
            )
            return False
        if terminations_bmk == terminations_sel:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Selection and bookmark is same so no changes done",
            )
            return False
        new = set(terminations_bmk)
        if new.intersection(terminations_sel):
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Selection is one of bookmarked terminations ",
                        "so no changes done",
                    )
                ),
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_termination.break_bookmarked_aliases,
            (database, new, terminations_sel, answer),
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
        """Undo identification of all aliases of selected termination."""
        title = EventSpec.menu_other_termination_split[1]
        database = self.get_database(title)
        if not database:
            return None
        terminations_sel = self._terminations_grid.selection
        terminations_bmk = self._terminations_grid.bookmarks
        if len(terminations_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No termination is selected",
            )
            return False
        if len(terminations_bmk) != 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Terminations are bookmarked so no changes done",
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_termination.split_aliases,
            (database, terminations_sel, answer),
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
        """Undo identification of all aliases of selected termination."""
        title = EventSpec.menu_other_termination_change[1]
        database = self.get_database(title)
        if not database:
            return None
        terminations_sel = self._terminations_grid.selection
        terminations_bmk = self._terminations_grid.bookmarks
        if len(terminations_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No termination is selected",
            )
            return False
        if len(terminations_bmk) != 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Terminations are bookmarked so no changes done",
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_termination.change_aliases,
            (database, terminations_sel, answer),
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
        """Return database if terminations list is attached to database.

        Return False otherwise after dialogue indicating problem.

        """
        terminations_ds = self._terminations_grid.datasource
        if terminations_ds is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Terminations list ",
                        "is not attached to database at present",
                    )
                ),
            )
            return False
        terminations_db = terminations_ds.dbhome
        if terminations_db is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Terminations list ",
                        "is not attached to database index at present",
                    )
                ),
            )
            return False
        return terminations_db
