# utilities.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""This module provides classes for handling PGN dates."""

from solentware_misc.core import utilities


class AppSysDate(utilities.AppSysDate):
    """Override superclass list of allowed date_formats.

    PGN style formats, '.' separators, are moved to start of list, and the
    format defined in the PGN standard, 'yyyy.mm.dd' is added.
    """

    date_formats = (
        "%Y.%m.%d",  # 2006.11.30
        "%d.%m.%Y",  # 30.11.2006
        "%d.%m.%y",  # 30.11.06
        "%m.%d.%Y",  # 11.30.2006
        "%m.%d.%y",  # 11.30.06
        "%d %b %Y",  # 30 Nov 2006
        "%b %d %Y",  # Nov 30 2006
        "%d %B %Y",  # 30 November 2006
        "%B %d %Y",  # November 30 2006
        "%d %b %y",  # 30 Nov 06
        "%b %d %y",  # Nov 30 06
        "%d %B %y",  # 30 November 06
        "%B %d %y",  # November 30 06
        "%Y-%m-%d",  # 2006-11-30
        "%Y/%m/%d",  # 2006/11/30
        "%d/%m/%Y",  # 30/11/2006
        "%d/%m/%y",  # 30/11/06
        "%m/%d/%Y",  # 11/30/2006
        "%m/%d/%y",  # 11/30/06
    )
