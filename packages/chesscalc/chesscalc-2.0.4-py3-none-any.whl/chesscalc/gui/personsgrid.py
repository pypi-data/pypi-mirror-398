# personsgrid.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance database datagrid class for persons."""

from solentware_grid.core import dataclient

from . import personsrow
from . import gridlocator
from ..core import filespec


class PersonsGrid(gridlocator.GridLocator):
    """Grid for person details list in PGN headers for games in PGN files."""

    def __init__(self, database=None, **kwargs):
        """Extend and note sibling grids."""
        super().__init__(**kwargs)
        self.make_header(personsrow.PersonsRow.header_specification)
        source = dataclient.DataSource(
            database,
            filespec.PLAYER_FILE_DEF,
            filespec.PERSON_NAME_FIELD_DEF,
            personsrow.PersonsRow,
        )
        self.set_data_source(source)

        # Not using appsys* modules: so how does chesstab do this if needed?
        # self.appsyspanel.get_appsys().get_data_register().register_in(
        #    self, self.on_data_change
        # )
