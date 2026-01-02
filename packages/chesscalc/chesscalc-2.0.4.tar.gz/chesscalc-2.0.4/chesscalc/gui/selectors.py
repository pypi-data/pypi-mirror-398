# selectors.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""List the game selectors for performance calculations in the database."""

import tkinter

from solentware_bind.gui.bindings import Bindings

from . import selectorsgrid


class SelectorsError(Exception):
    """Raise exception in selectors module."""


class Selectors(Bindings):
    """Define widgets which show list of game selection rules."""

    def __init__(self, master, database):
        """Create the persons widget."""
        super().__init__()
        self._selectors_grid = selectorsgrid.SelectorsGrid(
            parent=master, database=database
        )

    @property
    def frame(self):
        """Return the persons widget."""
        return self._selectors_grid.frame

    @property
    def data_grid(self):
        """Return the persons widget."""
        return self._selectors_grid

    def get_database(self, title):
        """Return database if identified players list is attached to database.

        Return False otherwise after dialogue indicating problem.

        """
        selectors_ds = self._selectors_grid.datasource
        if selectors_ds is None:
            tkinter.messagebox.showinfo(
                parent=self._selectors_grid,
                title=title,
                message="".join(
                    (
                        "Game Selectors list ",
                        "is not attached to database at present",
                    )
                ),
            )
            return False
        selectors_db = selectors_ds.dbhome
        if selectors_db is None:
            tkinter.messagebox.showinfo(
                parent=self._selectors_grid,
                title=title,
                message="".join(
                    (
                        "Game Selectors list ",
                        "is not attached to database index at present",
                    )
                ),
            )
            return False
        return selectors_db
