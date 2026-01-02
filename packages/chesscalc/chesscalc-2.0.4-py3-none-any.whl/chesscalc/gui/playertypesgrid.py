# playertypesgrid.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance database datagrid class for player types."""

from solentware_grid.core import dataclient

from . import playertypesrow
from . import gridlocator
from ..core import filespec


class PlayerTypesGrid(gridlocator.GridLocator):
    """Grid for list of playing modes of games from PGN files."""

    def __init__(self, database=None, **kwargs):
        """Extend and note sibling grids."""
        super().__init__(**kwargs)
        self.make_header(playertypesrow.PlayerTypesRow.header_specification)
        source = dataclient.DataSource(
            database,
            filespec.PLAYERTYPE_FILE_DEF,
            filespec.PLAYERTYPE_ALIAS_FIELD_DEF,
            playertypesrow.PlayerTypesRow,
        )
        self.set_data_source(source)

        # Not using appsys* modules: so how does chesstab do this if needed?
        # self.appsyspanel.get_appsys().get_data_register().register_in(
        #    self, self.on_data_change
        # )
