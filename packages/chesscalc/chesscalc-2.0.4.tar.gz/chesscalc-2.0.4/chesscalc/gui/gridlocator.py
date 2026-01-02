# gridlocator.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide ability to position view of DataGrid instances at arbitrary key.

Currently only the DataGridReadOnly subclass of DataGrid is supported.
"""

import tkinter

from solentware_grid import datagrid
from solentware_grid.gui import gridbindings


class GridLocator(gridbindings.GridBindings, datagrid.DataGridReadOnly):
    """Add a tkinter.ttk.Entry with bindings to control DataGrid scrolling.

    The value in the Entry widget determines the key of the first record
    displayed in the DataGrid instance.
    """

    def __init__(self, **kwargs):
        """Extend, define the data displayed from the playing Mode record.

        datagrid is a subclass of solentware_grid.datagrid.DataGrid.
        kwargs is passed to the superclass.

        """
        super().__init__(**kwargs)
        self._char = ""
        self.scroller = tkinter.ttk.Entry(master=self.parent)
        self.vsbar.configure(takefocus=tkinter.FALSE)
        self.hsbar.configure(takefocus=tkinter.FALSE)
        self.frame.grid(column=0, row=0, sticky=tkinter.NSEW)
        self.scroller.grid(column=0, row=1, sticky=tkinter.NSEW)
        self.bindings()
        self.bind(self.scroller, "<KeyPress>", function=self._note_char)
        self.bind(self.scroller, "<KeyRelease>", function=self._locate_key)

    def show_popup_menu_no_row(self, event=None):
        """Override superclass to do nothing."""
        # Added when DataGridBase changed to assume a popup menu is available
        # when right-click done on empty part of data drid frame.  The popup is
        # used to show all navigation available from grid: but this is not done
        # in chesscalc, at least yet, so avoid the temporary loss of focus to
        # an empty popup menu.

    def _locate_key(self, event=None):
        """Adjust data grid view to fit key starting Entry widget content."""
        if event is None:
            return
        key = self.scroller.get()
        if not key:
            return
        if not self._char:
            return
        self.move_to_row_in_grid(key)
        self._char = ""

    def _note_char(self, event=None):
        """Note capture of character which needs action on KeyRelease."""
        if event is None:
            return
        self._char = event.char
