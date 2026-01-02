# personsrow.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create widgets that display header details of persons from PGN files.

A Person record equates to a Player record where the details are one way
of naming a person.

"""

import tkinter

from solentware_grid.gui import datarow

from ..core import playerrecord
from ..core import constants


class PersonsRow(playerrecord.PlayerDBrecord, datarow.DataRow):
    """Display a Person record."""

    header_specification = [
        {
            datarow.WIDGET: tkinter.Label,
            datarow.WIDGET_CONFIGURE: {"text": text, "anchor": tkinter.CENTER},
            datarow.GRID_CONFIGURE: {"column": column, "sticky": tkinter.EW},
            datarow.GRID_COLUMNCONFIGURE: {"weight": 0, "uniform": uniform},
            datarow.ROW: 0,
        }
        for column, text, uniform in (
            (0, "FideId", "u0"),
            (1, "Name", "u1"),
            (2, constants.TAG_EVENT, "u2"),
            (3, constants.TAG_EVENTDATE, "u3"),
            (4, constants.TAG_SECTION, "u4"),
            (5, constants.TAG_STAGE, "u5"),
            (6, "Team", "u6"),
            (7, "Type", "u7"),
            (8, "Alias", "u8"),
            (9, "Identity", "u9"),
        )
    ]

    def __init__(self, database=None):
        """Extend, define the data displayed from the Person record."""
        super().__init__(valueclass=playerrecord.PersonDBvalue)
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
                (7, tkinter.CENTER),
                (8, tkinter.CENTER),
                (9, tkinter.CENTER),
            )
        ]

    def grid_row(self, **kargs):
        """Return tuple of instructions to create row.

        Create textitems argument for PersonsRow instance.

        """
        value = self.value
        return super().grid_row(
            textitems=(
                value.fideid if value.fideid is not None else "",
                value.name if value.name is not None else "",
                value.event if value.event is not None else "",
                value.eventdate if value.eventdate is not None else "",
                value.section if value.section is not None else "",
                value.stage if value.stage is not None else "",
                value.team if value.team is not None else "",
                value.type if value.type is not None else "",
                value.alias if value.alias is not None else "",
                value.identity if value.identity is not None else "",
            ),
            **kargs
        )
