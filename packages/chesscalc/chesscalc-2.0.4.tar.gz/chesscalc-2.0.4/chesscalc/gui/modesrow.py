# modesrow.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets that display playing modes of games from PGN files."""

import tkinter

from solentware_grid.gui import datarow

from ..core import moderecord
from ..core import constants


class ModesRow(moderecord.ModeDBrecord, datarow.DataRow):
    """Display a playing mode record detail in playing mode name order."""

    header_specification = [
        {
            datarow.WIDGET: tkinter.Label,
            datarow.WIDGET_CONFIGURE: {"text": text, "anchor": tkinter.CENTER},
            datarow.GRID_CONFIGURE: {"column": column, "sticky": tkinter.EW},
            datarow.GRID_COLUMNCONFIGURE: {"weight": 0, "uniform": uniform},
            datarow.ROW: 0,
        }
        for column, text, uniform in (
            (0, constants.TAG_MODE, "u0"),
            (4, "Alias", "u1"),
            (5, "Identity", "u2"),
        )
    ]

    def __init__(self, database=None):
        """Extend, define the data displayed from the playing Mode record."""
        super().__init__()
        self.set_database(database)
        self.row_specification = [
            {
                datarow.WIDGET: tkinter.Label,
                datarow.WIDGET_CONFIGURE: {"anchor": anchor},
                datarow.GRID_CONFIGURE: {
                    "column": column,
                    "sticky": tkinter.EW,
                },
                datarow.ROW: 0,
            }
            for column, anchor in (
                (0, tkinter.CENTER),
                (1, tkinter.CENTER),
                (2, tkinter.CENTER),
            )
        ]

    def grid_row(self, **kargs):
        """Return tuple of instructions to create row.

        Create textitems argument for ModesRow instance.

        """
        value = self.value
        return super().grid_row(
            textitems=(
                value.mode if value.mode is not None else "",
                value.alias if value.alias is not None else "",
                value.identity if value.identity is not None else "",
            ),
            **kargs
        )
