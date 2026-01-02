# players.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""List the players in the database."""

import tkinter

from solentware_bind.gui.bindings import Bindings

from . import playersgrid
from . import personsgrid
from .eventspec import EventSpec
from ..core import identify_person
from ..shared import task


class PlayersError(Exception):
    """Raise exception in players module."""


class Players(Bindings):
    """Define widgets which list players not identified as a person."""

    def __init__(self, master, database):
        """Create the players widget."""
        super().__init__()
        self._players = tkinter.ttk.PanedWindow(
            master=master, orient=tkinter.HORIZONTAL
        )
        players_frame = tkinter.ttk.Frame(master=self._players)
        self._players_grid = playersgrid.PlayersGrid(
            parent=players_frame, database=database
        )
        players_frame.grid_rowconfigure(0, weight=1)
        players_frame.grid_columnconfigure(0, weight=1)
        persons_frame = tkinter.ttk.Frame(master=self._players)
        self._persons_grid = personsgrid.PersonsGrid(
            parent=persons_frame, database=database
        )
        persons_frame.grid_rowconfigure(0, weight=1)
        persons_frame.grid_columnconfigure(0, weight=1)
        self._players.add(players_frame, weight=1)
        self._players.add(persons_frame, weight=1)
        self._players.grid(column=0, row=0, sticky=tkinter.NSEW)

    @property
    def frame(self):
        """Return the players widget."""
        return self._players

    @property
    def players_grid(self):
        """Return the players grid."""
        return self._players_grid

    @property
    def persons_grid(self):
        """Return the persons grid."""
        return self._persons_grid

    def identify(self, update_widget_and_join_loop):
        """Identify selected new players as a person."""
        title = EventSpec.menu_player_identify[1]
        database = self.get_database(title)
        if not database:
            return None
        players_sel = self._players_grid.selection
        players_bmk = self._players_grid.bookmarks
        persons_sel = self._persons_grid.selection
        if len(players_sel) == 0 and len(players_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self._players,
                title=title,
                message="".join(
                    (
                        "No new players are selected or bookmarked for ",
                        "identification as a known player",
                    )
                ),
            )
            return False
        if len(players_sel) == 0 and len(persons_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self._players,
                title=title,
                message="".join(
                    (
                        "A new or known player must be selected as the ",
                        "known player to be aliased",
                    )
                ),
            )
            return False
        if len(persons_sel) == 1:
            if not tkinter.messagebox.askokcancel(
                parent=self._players,
                title=title,
                message="".join(
                    (
                        "The selected and bookmarked new players ",
                        "will become aliases of the selected known ",
                        "player",
                    )
                ),
            ):
                return False
        elif not tkinter.messagebox.askokcancel(
            parent=self._players,
            title=title,
            message="".join(
                (
                    "The selected and bookmarked new players will become ",
                    "aliases of the selected new player",
                )
            ),
        ):
            return False
        new = set(players_bmk)
        if len(persons_sel) == 1:
            identified = persons_sel
            new.update(set(players_sel))
        else:
            identified = players_sel
            new.difference_update(set(players_sel))
        task.Task(
            database,
            identify_person.identify_players_as_person,
            (database, new, identified),
            update_widget_and_join_loop,
        ).start_and_join()
        return True

    def identify_by_name(self, update_widget_and_join_loop):
        """Identify selected new players as persons matching on names."""
        title = EventSpec.menu_player_identify[1]
        database = self.get_database(title)
        if not database:
            return None
        players_sel = self._players_grid.selection
        persons_sel = self._persons_grid.selection
        if self._players_grid.bookmarks or self._persons_grid.bookmarks:
            tkinter.messagebox.showinfo(
                parent=self._players,
                title=title,
                message="".join(
                    (
                        "Bookmarked items are ignored in this action ",
                        "but will be cleared on completion",
                    )
                ),
            )
        if len(players_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self._players,
                title=title,
                message="".join(
                    (
                        "Please select a new player to become a known ",
                        "player (with any of the same name)",
                    )
                ),
            )
            return False
        if len(persons_sel) == 1:
            if not tkinter.messagebox.askokcancel(
                parent=self._players,
                title=title,
                message="".join(
                    (
                        "The selected new player and any with the same ",
                        "name will become aliases of the selected known ",
                        "player",
                    )
                ),
            ):
                return False
        elif not tkinter.messagebox.askokcancel(
            parent=self._players,
            title=title,
            message="".join(
                (
                    "The selected player and any with the same name ",
                    "will become one known player",
                )
            ),
        ):
            return False
        if len(persons_sel) == 1:
            identified = persons_sel
        else:
            identified = players_sel
        task.Task(
            database,
            identify_person.identify_players_by_name_as_person,
            (database, set(players_sel), identified),
            update_widget_and_join_loop,
        ).start_and_join()
        return True

    def match_players_by_name(self, update_widget_and_join_loop):
        """Identify new players with same name as person for all names."""
        title = EventSpec.menu_match_players_by_name[1]
        database = self.get_database(title)
        if not database:
            return None
        if (
            self._players_grid.bookmarks
            or self._persons_grid.bookmarks
            or self._players_grid.selection
            or self._persons_grid.selection
        ):
            if not tkinter.messagebox.askokcancel(
                parent=self._players,
                title=title,
                message="".join(
                    (
                        "Selection and bookmarked items are ignored in this ",
                        "action but will be cleared on completion",
                    )
                ),
            ):
                return False
        task.Task(
            database,
            identify_person.identify_all_players_by_name_as_persons,
            (database,),
            update_widget_and_join_loop,
        ).start_and_join()
        return True

    def get_database(self, title):
        """Return database if both player lists are from same database.

        Return False otherwise after dialogue indicating problem.

        title is the tile for any dialogue shown.

        The player lists are the New and Identified lists.

        """
        players_ds = self._players_grid.datasource
        persons_ds = self._persons_grid.datasource
        if players_ds is None and persons_ds is None:
            tkinter.messagebox.showinfo(
                parent=self._players,
                title=title,
                message="".join(
                    (
                        "New Players and Identified Players lists ",
                        "are not attached to database at present",
                    )
                ),
            )
            return False
        if players_ds is None:
            tkinter.messagebox.showinfo(
                parent=self._players,
                title=title,
                message="".join(
                    (
                        "New Players list ",
                        "is not attached to database at present",
                    )
                ),
            )
            return False
        if persons_ds is None:
            tkinter.messagebox.showinfo(
                parent=self._players,
                title=title,
                message="".join(
                    (
                        "Identified Players list ",
                        "is not attached to database at present",
                    )
                ),
            )
            return False
        players_db = players_ds.dbhome
        persons_db = persons_ds.dbhome
        if players_db is None and persons_db is None:
            tkinter.messagebox.showinfo(
                parent=self._players,
                title=title,
                message="".join(
                    (
                        "New Players and Identified Players lists ",
                        "are not attached to database indicies at present",
                    )
                ),
            )
            return False
        if players_db is None:
            tkinter.messagebox.showinfo(
                parent=self._players,
                title=title,
                message="".join(
                    (
                        "New Players list ",
                        "is not attached to database index at present",
                    )
                ),
            )
            return False
        if persons_db is None:
            tkinter.messagebox.showinfo(
                parent=self._players,
                title=title,
                message="".join(
                    (
                        "Identified Players list ",
                        "is not attached to database index at present",
                    )
                ),
            )
            return False
        if players_db is not persons_db:
            tkinter.messagebox.showinfo(
                parent=self._players,
                title=title,
                message="".join(
                    (
                        "New Players and Identified Players lists ",
                        "are not attached to same database at present",
                    )
                ),
            )
            return False
        return players_db
