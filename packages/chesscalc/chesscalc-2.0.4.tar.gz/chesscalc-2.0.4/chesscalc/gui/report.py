# report.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Create report widget."""

import tkinter
import tkinter.ttk

from solentware_bind.gui.bindings import Bindings


class Report(Bindings):
    """Define widget to display action reports."""

    def __init__(self, master, database, labeltext):
        """Create the report widget."""
        super().__init__()
        self._database = database
        self._frame = master
        self._report = tkinter.Text(
            master=master,
            wrap=tkinter.WORD,
            background="gray93",
            state=tkinter.DISABLED,
        )
        self._report.grid_configure(column=0, row=1, sticky=tkinter.NSEW)
        self._report.configure(
            background="gray85",
            takefocus=tkinter.FALSE,
        )
        tkinter.ttk.Label(
            master=master,
            text=labeltext,
            anchor=tkinter.CENTER,
        ).grid_configure(column=0, row=0, sticky=tkinter.EW, pady=(5, 0))
        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)

    @property
    def frame(self):
        """Return the top frame of the report widget."""
        return self._frame

    @property
    def report_text(self):
        """Return the tkinter.Text object of the report widget."""
        return self._report

    def append_text(self, text):
        """Append text to the report widget."""
        widget = self.report_text
        widget.configure(state=tkinter.NORMAL)
        widget.insert(tkinter.END, text)
        widget.configure(state=tkinter.DISABLED)
        widget.see(tkinter.END)
