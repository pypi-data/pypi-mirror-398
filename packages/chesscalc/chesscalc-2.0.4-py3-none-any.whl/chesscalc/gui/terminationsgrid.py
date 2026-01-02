# terminationsgrid.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance database datagrid class for termination reasons."""

from solentware_grid.core import dataclient

from . import terminationsrow
from . import gridlocator
from ..core import filespec


class TerminationsGrid(gridlocator.GridLocator):
    """Grid for list of termination reasons of games from PGN files."""

    def __init__(self, database=None, **kwargs):
        """Extend and note sibling grids."""
        super().__init__(**kwargs)
        self.make_header(terminationsrow.TerminationsRow.header_specification)
        source = dataclient.DataSource(
            database,
            filespec.TERMINATION_FILE_DEF,
            filespec.TERMINATION_ALIAS_FIELD_DEF,
            terminationsrow.TerminationsRow,
        )
        self.set_data_source(source)

        # Not using appsys* modules: so how does chesstab do this if needed?
        # self.appsyspanel.get_appsys().get_data_register().register_in(
        #    self, self.on_data_change
        # )
