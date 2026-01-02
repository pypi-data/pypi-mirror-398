# selectorsrow.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets that display header details of game selection rules."""

import tkinter

from solentware_grid.gui import datarow

from ..core import selectorrecord


class SelectorsRow(selectorrecord.SelectorDBrecord, datarow.DataRow):
    """Display a Game Selector record."""

    header_specification = [
        {
            datarow.WIDGET: tkinter.Label,
            datarow.WIDGET_CONFIGURE: {"text": text, "anchor": tkinter.CENTER},
            datarow.GRID_CONFIGURE: {"column": column, "sticky": tkinter.EW},
            datarow.GRID_COLUMNCONFIGURE: {"weight": 0, "uniform": uniform},
            datarow.ROW: 0,
        }
        for column, text, uniform in (
            (0, "Rule", "u0"),
            (1, "From Date", "u1"),
            (2, "To Date", "u2"),
            (3, "Mode", "u3"),
            (4, "Time Control", "u4"),
            (5, "Person", "u5"),
            (6, "Events", "u6"),
        )
    ]

    def __init__(self, database=None):
        """Extend, define the data displayed from the Game Selector record."""
        super().__init__(valueclass=selectorrecord.SelectorDBvalue)
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
                (6, tkinter.CENTER),
            )
        ]

    def grid_row(self, **kargs):
        """Return tuple of instructions to create row.

        Create textitems argument for PersonsRow instance.

        """
        value = self.value
        return super().grid_row(
            textitems=(
                value.name if value.name is not None else "",
                value.from_date if value.from_date is not None else "",
                value.to_date if value.to_date is not None else "",
                value.mode_identity if value.mode_identity is not None else "",
                value.time_control_identity
                if value.time_control_identity is not None
                else "",
                value.person_identity
                if value.person_identity is not None
                else "",
                value.event_identities
                if value.event_identities is not None
                else "",
            ),
            **kargs
        )
