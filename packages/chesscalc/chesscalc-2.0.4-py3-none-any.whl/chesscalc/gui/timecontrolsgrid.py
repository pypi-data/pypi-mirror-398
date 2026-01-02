# timecontrolsgrid.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance database datagrid class for time controls."""

from solentware_grid.core import dataclient

from . import timecontrolsrow
from . import gridlocator
from ..core import filespec


class TimeControlsGrid(gridlocator.GridLocator):
    """Grid for list of time control details in games from PGN files."""

    def __init__(self, database=None, **kwargs):
        """Extend and note sibling grids."""
        super().__init__(**kwargs)
        self.make_header(timecontrolsrow.TimeControlsRow.header_specification)
        source = dataclient.DataSource(
            database,
            filespec.TIME_FILE_DEF,
            filespec.TIME_ALIAS_FIELD_DEF,
            timecontrolsrow.TimeControlsRow,
        )
        self.set_data_source(source)

        # Not using appsys* modules: so how does chesstab do this if needed?
        # self.appsyspanel.get_appsys().get_data_register().register_in(
        #    self, self.on_data_change
        # )
