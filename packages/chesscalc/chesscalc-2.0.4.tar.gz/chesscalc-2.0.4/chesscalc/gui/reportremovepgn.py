# reportremovepgn.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Display report on removal of bookmarked games or selected PGN file."""

from . import report


# ReportRemovePGN probably needs a tkinter.Text widget which behaves like
# solentware_misc.gui.logtextbase.LogTextBase, which is not set up for
# 'disabled' state and uses the pack geometry manager.
# No timestamp support to start with, though likely needed eventually.
class ReportRemovePGN(report.Report):
    """Define widget to display report on deletion of PGN games."""

    def __init__(self, master, database):
        """Create the report widget."""
        super().__init__(
            master,
            database,
            "Actions or Problems for PGN Game Removal",
        )
