# ruleinsert.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customize rule.Rule for insertion of new rule into calculations list."""

import tkinter

from . import rule
from .eventspec import EventSpec


class RuleInsert(rule.Rule):
    """Define widget to insert selection rule and calculated performances."""

    def update_rule(self):
        """Update selection rule on database."""
        tkinter.messagebox.showinfo(
            parent=self.frame,
            title=EventSpec.menu_selectors_new[1],
            message="Cannot update rule from New",
        )

    def delete_rule(self):
        """Delete selection rule from database."""
        tkinter.messagebox.showinfo(
            parent=self.frame,
            title=EventSpec.menu_selectors_new[1],
            message="Cannot delete rule from New",
        )

    def calulate_performances_for_rule(self):
        """Calculate performances for selection rule on database."""
        tkinter.messagebox.showinfo(
            parent=self.frame,
            title=EventSpec.menu_selectors_new[1],
            message="Cannot calculate performance from New",
        )
