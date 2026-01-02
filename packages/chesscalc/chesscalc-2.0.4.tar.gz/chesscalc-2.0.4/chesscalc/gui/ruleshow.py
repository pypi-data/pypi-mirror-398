# ruleshow.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Customize rule.Rule for insrtion of new rule into calculations list."""

import tkinter

from . import rule
from .eventspec import EventSpec


class RuleShow(rule.Rule):
    """Define widget to insert selection rule and calculated performances."""

    def __init__(self, *args):
        """Create the rule widget."""
        super().__init__(*args)
        self._disable_entry_widgets()
        self._event_identities.configure(
            background="gray85",
            takefocus=tkinter.FALSE,
        )

    def _disable_entry_widgets(self):
        """Override to disable all entry widgets."""
        self._rule.configure(state=tkinter.DISABLED)
        self._player_identity.configure(state=tkinter.DISABLED)
        self._from_date.configure(state=tkinter.DISABLED)
        self._to_date.configure(state=tkinter.DISABLED)
        self._time_control_identity.configure(state=tkinter.DISABLED)
        self._mode_identity.configure(state=tkinter.DISABLED)
        self._termination_identity.configure(state=tkinter.DISABLED)
        self._player_type_identity.configure(state=tkinter.DISABLED)
        self._event_identities.configure(state=tkinter.DISABLED)

    def _enable_entry_widgets(self):
        """Override to enable changes to all entry widgets."""
        self._rule.configure(state=tkinter.NORMAL)
        self._player_identity.configure(state=tkinter.NORMAL)
        self._from_date.configure(state=tkinter.NORMAL)
        self._to_date.configure(state=tkinter.NORMAL)
        self._time_control_identity.configure(state=tkinter.NORMAL)
        self._mode_identity.configure(state=tkinter.NORMAL)
        self._termination_identity.configure(state=tkinter.NORMAL)
        self._player_type_identity.configure(state=tkinter.NORMAL)
        self._event_identities.configure(state=tkinter.NORMAL)

    def insert_rule(self, update_widget_and_join_loop):
        """Insert selection rule into database."""
        if not tkinter.messagebox.askyesno(
            parent=self.frame,
            title=EventSpec.menu_selectors_show[1],
            message="Do you want to insert a copy of this rule?",
        ):
            return False
        return super().insert_rule(update_widget_and_join_loop)

    def update_rule(self):
        """Update selection rule on database."""
        tkinter.messagebox.showinfo(
            parent=self.frame,
            title=EventSpec.menu_selectors_show[1],
            message="Cannot update rule from Show",
        )

    def delete_rule(self):
        """Delete selection rule from database."""
        if not tkinter.messagebox.askyesno(
            parent=self.frame,
            title=EventSpec.menu_selectors_show[1],
            message="Do you want to delete this rule?",
        ):
            return False
        return super().delete_rule()
