# ruleedit.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customize rule.Rule for insrtion of new rule into calculations list."""

import tkinter

from . import rule
from .eventspec import EventSpec


class RuleEdit(rule.Rule):
    """Define widget to insert selection rule and calculated performances."""

    def __init__(self, *args):
        """Create the rule widget."""
        super().__init__(*args)
        self._disable_entry_widgets()

    def _disable_entry_widgets(self):
        """Override to disable all entry widgets."""
        self._rule.configure(state=tkinter.DISABLED)

    def _enable_entry_widgets(self):
        """Override to enable changes to all entry widgets."""
        self._rule.configure(state=tkinter.NORMAL)

    def insert_rule(self, update_widget_and_join_loop):
        """Insert selection rule into database."""
        if not tkinter.messagebox.askyesno(
            parent=self.frame,
            title=EventSpec.menu_selectors_edit[1],
            message="Do you want to insert a copy of this rule?",
        ):
            return False
        return super().insert_rule(update_widget_and_join_loop)

    def delete_rule(self):
        """Delete selection rule from database."""
        if not tkinter.messagebox.askyesno(
            parent=self.frame,
            title=EventSpec.menu_selectors_edit[1],
            message="Do you want to delete this rule?",
        ):
            return False
        return super().delete_rule()

    def calulate_performances_for_rule(self):
        """Calculate performances for selection rule on database."""
        tkinter.messagebox.showinfo(
            parent=self.frame,
            title=EventSpec.menu_selectors_edit[1],
            message="Cannot calculate performance from Edit",
        )
