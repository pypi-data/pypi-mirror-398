# help_.py
# Copyright 2009 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions to create Help widgets for performance calculations."""

import tkinter

from solentware_misc.gui.help_ import help_widget

import chesscalc.help_


def help_about_calculator(master):
    """Display About document for ChessPerfCalc."""
    help_widget(master, chesscalc.help_.ABOUT, chesscalc.help_)


def help_notes_calculator(master):
    """Display Notes document for ChessPerfCalc."""
    help_widget(master, chesscalc.help_.NOTES, chesscalc.help_)


if __name__ == "__main__":
    # Display all help documents without running ChessResults application

    root = tkinter.Tk()
    help_about_calculator(root)
    help_notes_calculator(root)
    root.mainloop()
