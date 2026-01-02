# modesgrid.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance database datagrid class for modes."""

from solentware_grid.core import dataclient

from . import modesrow
from . import gridlocator
from ..core import filespec


class ModesGrid(gridlocator.GridLocator):
    """Grid for list of playing modes of games from PGN files."""

    def __init__(self, database=None, **kwargs):
        """Extend and note sibling grids."""
        super().__init__(**kwargs)
        self.make_header(modesrow.ModesRow.header_specification)
        source = dataclient.DataSource(
            database,
            filespec.MODE_FILE_DEF,
            filespec.MODE_ALIAS_FIELD_DEF,
            modesrow.ModesRow,
        )
        self.set_data_source(source)

        # Not using appsys* modules: so how does chesstab do this if needed?
        # self.appsyspanel.get_appsys().get_data_register().register_in(
        #    self, self.on_data_change
        # )
