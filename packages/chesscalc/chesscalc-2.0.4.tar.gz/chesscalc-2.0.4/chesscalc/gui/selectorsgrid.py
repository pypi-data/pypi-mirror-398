# selectorsgrid.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance database datagrid class for game selection."""

from solentware_grid.core import dataclient

from . import selectorsrow
from . import gridlocator
from ..core import filespec


class SelectorsGrid(gridlocator.GridLocator):
    """Grid for game selectors list for performance calculations."""

    def __init__(self, database=None, **kwargs):
        """Extend and note sibling grids."""
        super().__init__(**kwargs)
        self.make_header(selectorsrow.SelectorsRow.header_specification)
        source = dataclient.DataSource(
            database,
            filespec.SELECTION_FILE_DEF,
            filespec.RULE_FIELD_DEF,
            selectorsrow.SelectorsRow,
        )
        self.set_data_source(source)

        # Not using appsys* modules: so how does chesstab do this if needed?
        # self.appsyspanel.get_appsys().get_data_register().register_in(
        #    self, self.on_data_change
        # )
