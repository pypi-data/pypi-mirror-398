# eventsgrid.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance database datagrid class for games."""

from solentware_grid.core import dataclient

from . import eventsrow
from . import gridlocator
from ..core import filespec


class EventsGrid(gridlocator.GridLocator):
    """Grid for list of header details of events from PGN files."""

    def __init__(self, database=None, **kwargs):
        """Extend and note sibling grids."""
        super().__init__(**kwargs)
        self.make_header(eventsrow.EventsRow.header_specification)
        source = dataclient.DataSource(
            database,
            filespec.EVENT_FILE_DEF,
            filespec.EVENT_NAME_FIELD_DEF,
            eventsrow.EventsRow,
        )
        self.set_data_source(source)

        # Not using appsys* modules: so how does chesstab do this if needed?
        # self.appsyspanel.get_appsys().get_data_register().register_in(
        #    self, self.on_data_change
        # )
