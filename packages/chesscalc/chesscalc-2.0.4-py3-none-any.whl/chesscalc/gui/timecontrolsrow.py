# timecontrolsrow.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets that display header details of games from PGN files."""

import tkinter

from solentware_grid.gui import datarow

from ..core import timecontrolrecord
from ..core import constants


class TimeControlsRow(timecontrolrecord.TimeControlDBrecord, datarow.DataRow):
    """Display a time control record detail in time control name order."""

    header_specification = [
        {
            datarow.WIDGET: tkinter.Label,
            datarow.WIDGET_CONFIGURE: {"text": text, "anchor": tkinter.CENTER},
            datarow.GRID_CONFIGURE: {"column": column, "sticky": tkinter.EW},
            datarow.GRID_COLUMNCONFIGURE: {"weight": 0, "uniform": uniform},
            datarow.ROW: 0,
        }
        for column, text, uniform in (
            (0, constants.TAG_TIMECONTROL, "u0"),
            (4, "Alias", "u1"),
            (5, "Identity", "u2"),
        )
    ]

    def __init__(self, database=None):
        """Extend, define layout of displayed time control data."""
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

        Create textitems argument for TimeControlsRow instance.

        """
        value = self.value
        return super().grid_row(
            textitems=(
                value.timecontrol if value.timecontrol is not None else "",
                value.alias if value.alias is not None else "",
                value.identity if value.identity is not None else "",
            ),
            **kargs
        )
