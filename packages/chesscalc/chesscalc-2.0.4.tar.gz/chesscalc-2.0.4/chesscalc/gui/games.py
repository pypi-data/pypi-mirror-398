# games.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""List the games in the database."""

import tkinter

from solentware_bind.gui.bindings import Bindings

from . import gamesgrid
from .eventspec import EventSpec
from ..core import delete_games
from ..shared import task


class GamesError(Exception):
    """Raise exception in games module."""


class Games(Bindings):
    """Define widgets which list of games and PGN file references."""

    def __init__(self, master, database):
        """Create the games widget."""
        super().__init__()
        self._games_grid = gamesgrid.GamesGrid(
            parent=master, database=database
        )

    @property
    def frame(self):
        """Return the top frame of the games widget."""
        return self._games_grid.frame

    @property
    def data_grid(self):
        """Return the games widget."""
        return self._games_grid

    def remove_pgn_file(self, tab, update_widget_and_join_loop):
        """Remove games imported from PGN file os selected from database."""
        title = EventSpec.menu_database_remove_games[1]
        database = self.get_database(title)
        if not database:
            return None
        games_sel = self._games_grid.selection
        games_bmk = self._games_grid.bookmarks
        if len(games_sel) == 0 and len(games_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No games are selected or bookmarked for deletion",
            )
            return False
        if len(games_sel) != 0 and len(games_bmk) != 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Either a PGN file for which all games are ",
                        "deleted must be selected by game, or the ",
                        "games to be deleted must be bookmarked.\n\n",
                        "Cannot both select and bookmark games for "
                        "deletion.",
                    )
                ),
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            delete_games.delete_selected_file_or_bookmarked_games,
            (database, games_bmk, games_sel, tab, answer),
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
        """Return database if games list is attached to database.

        Return False otherwise after dialogue indicating problem.

        """
        games_ds = self._games_grid.datasource
        if games_ds is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Games list ",
                        "is not attached to database at present",
                    )
                ),
            )
            return False
        games_db = games_ds.dbhome
        if games_db is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Games list ",
                        "is not attached to database index at present",
                    )
                ),
            )
            return False
        return games_db
