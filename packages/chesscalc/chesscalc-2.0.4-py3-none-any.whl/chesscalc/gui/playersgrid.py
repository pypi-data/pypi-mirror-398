# playersgrid.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance database datagrid class for persons."""

from solentware_grid.core import dataclient

from . import playersrow
from . import gridlocator
from ..core import filespec


class PlayersGrid(gridlocator.GridLocator):
    """Grid for person details list in PGN headers for games in PGN files."""

    def __init__(self, database=None, **kwargs):
        """Extend and note sibling grids."""
        super().__init__(**kwargs)
        self.make_header(playersrow.PlayersRow.header_specification)
        source = dataclient.DataSource(
            database,
            filespec.PLAYER_FILE_DEF,
            filespec.PLAYER_NAME_FIELD_DEF,
            playersrow.PlayersRow,
        )
        self.set_data_source(source)

        # Not using appsys* modules: so how does chesstab do this if needed?
        # self.appsyspanel.get_appsys().get_data_register().register_in(
        #    self, self.on_data_change
        # )
