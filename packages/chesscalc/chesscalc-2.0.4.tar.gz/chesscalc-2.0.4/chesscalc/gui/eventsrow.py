# eventsrow.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets that display header details of games from PGN files."""

import tkinter

from solentware_grid.gui import datarow

from ..core import eventrecord
from ..core import constants


class EventsRow(eventrecord.EventDBrecord, datarow.DataRow):
    """Display an Event record event detail in event name order."""

    header_specification = [
        {
            datarow.WIDGET: tkinter.Label,
            datarow.WIDGET_CONFIGURE: {"text": text, "anchor": tkinter.CENTER},
            datarow.GRID_CONFIGURE: {"column": column, "sticky": tkinter.EW},
            datarow.GRID_COLUMNCONFIGURE: {"weight": 0, "uniform": uniform},
            datarow.ROW: 0,
        }
        for column, text, uniform in (
            (0, constants.TAG_EVENT, "u0"),
            (1, constants.TAG_EVENTDATE, "u1"),
            (2, constants.TAG_SECTION, "u2"),
            (3, constants.TAG_STAGE, "u3"),
            (4, "Alias", "u4"),
            (5, "Identity", "u5"),
        )
    ]

    def __init__(self, database=None):
        """Extend, define the data displayed from the Event record."""
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
                (3, tkinter.CENTER),
                (4, tkinter.CENTER),
                (5, tkinter.CENTER),
            )
        ]

    def grid_row(self, **kargs):
        """Return tuple of instructions to create row.

        Create textitems argument for EventsRow instance.

        """
        value = self.value
        return super().grid_row(
            textitems=(
                value.event if value.event is not None else "",
                value.eventdate if value.eventdate is not None else "",
                value.section if value.section is not None else "",
                value.stage if value.stage is not None else "",
                value.alias if value.alias is not None else "",
                value.identity if value.identity is not None else "",
            ),
            **kargs
        )
