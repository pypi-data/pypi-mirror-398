# gamesgrid.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance database datagrid class for games."""

from solentware_grid.core import dataclient

from . import gamesrow
from . import gridlocator
from ..core import filespec


class GamesGrid(gridlocator.GridLocator):
    """Grid for list of header details of games from PGN files."""

    def __init__(self, database=None, **kwargs):
        """Extend and note sibling grids."""
        super().__init__(**kwargs)
        self.make_header(gamesrow.GamesRow.header_specification)
        source = dataclient.DataSource(
            database,
            filespec.GAME_FILE_DEF,
            filespec.GAME_NAME_FIELD_DEF,
            gamesrow.GamesRow,
        )
        self.set_data_source(source)

        # Not using appsys* modules: so how does chesstab do this if needed?
        # self.appsyspanel.get_appsys().get_data_register().register_in(
        #    self, self.on_data_change
        # )
