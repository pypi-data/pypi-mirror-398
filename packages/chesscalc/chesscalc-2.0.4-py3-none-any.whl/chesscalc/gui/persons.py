# persons.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""List the persons in the database."""

import tkinter
import os
import datetime

from solentware_bind.gui.bindings import Bindings

from . import personsgrid
from .eventspec import EventSpec
from ..core import identify_person
from ..core import export
from ..shared import task
from .. import REPORT_DIRECTORY


class PersonsError(Exception):
    """Raise exception in persons module."""


class Persons(Bindings):
    """Define widgets which list persons not identified as a person."""

    def __init__(self, master, database):
        """Create the persons widget."""
        super().__init__()
        self._persons_grid = personsgrid.PersonsGrid(
            parent=master, database=database
        )

    @property
    def frame(self):
        """Return the persons widget."""
        return self._persons_grid.frame

    @property
    def data_grid(self):
        """Return the persons widget."""
        return self._persons_grid

    def break_selected(self, update_widget_and_join_loop):
        """Undo identification of selected players as a person."""
        title = EventSpec.menu_player_break[1]
        database = self.get_database(title)
        if not database:
            return None
        persons_sel = self._persons_grid.selection
        persons_bmk = self._persons_grid.bookmarks
        if len(persons_sel) == 0 and len(persons_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "No identified person is selected and no aliases ",
                        "are bookmarked to be made new players",
                    )
                ),
            )
            return False
        if len(persons_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No identified person is selected",
            )
            return False
        if len(persons_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "No aliases ",
                        "are bookmarked to be made new players",
                    )
                ),
            )
            return False
        aliases = set(persons_bmk)
        if persons_sel[0] in aliases:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Cannot break associations when selected entry ",
                        "is also bookmarked",
                    )
                ),
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_person.break_person_into_picked_players,
            (database, persons_sel, aliases, answer),
            update_widget_and_join_loop,
        ).start_and_join()
        if answer["message"]:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message=answer["message"],
            )
            return False
        return True

    def split_all(self, update_widget_and_join_loop):
        """Undo identification of all player aliases as a person."""
        title = EventSpec.menu_player_split[1]
        database = self.get_database(title)
        if not database:
            return None
        persons_sel = self._persons_grid.selection
        persons_bmk = self._persons_grid.bookmarks
        if len(persons_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "No identified person is selected to split ",
                        "into all aliases",
                    )
                ),
            )
            return False
        if len(persons_sel) != 1:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Exactly one identified person must be selected ",
                        "to split into all aliases",
                    )
                ),
            )
            return False
        if len(persons_bmk) != 0:
            if not tkinter.messagebox.askokcancel(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "The selected identified person will split into all "
                        "aliases (bookmarks on identified persons are "
                        "ignored)",
                    )
                ),
            ):
                return False
        elif not tkinter.messagebox.askokcancel(
            parent=self.frame,
            title=title,
            message="".join(
                (
                    "The selected identified person will split into all "
                    "aliases",
                )
            ),
        ):
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_person.split_person_into_all_players,
            (database, persons_sel, answer),
            update_widget_and_join_loop,
        ).start_and_join()
        if answer["message"]:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message=answer["message"],
            )
            return False
        return True

    def change_identity(self, update_widget_and_join_loop):
        """Change identification of all player aliases as a person."""
        title = EventSpec.menu_player_change[1]
        database = self.get_database(title)
        if not database:
            return None
        persons_sel = self._persons_grid.selection
        persons_bmk = self._persons_grid.bookmarks
        if len(persons_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "No identified person is selected to have ",
                        "identity changed",
                    )
                ),
            )
            return False
        if len(persons_sel) != 1:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Exactly one identified person must be selected ",
                        "to change identity",
                    )
                ),
            )
            return False
        if len(persons_bmk) != 0:
            if not tkinter.messagebox.askokcancel(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "The selected alias will become the identified ",
                        "person (bookmarks on identified persons are "
                        "ignored)",
                    )
                ),
            ):
                return False
        elif not tkinter.messagebox.askokcancel(
            parent=self.frame,
            title=title,
            message="".join(
                ("The selected alias will become the identified ", "person")
            ),
        ):
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_person.change_identified_person,
            (database, persons_sel, answer),
            update_widget_and_join_loop,
        ).start_and_join()
        if answer["message"]:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message=answer["message"],
            )
            return False
        return True

    def _export_selected_players(
        self, database, persons_bmk, persons_sel, answer
    ):
        """Prepare player data for export."""
        exporter = export.ExportPersons(database, persons_bmk, persons_sel)
        answer["status"] = exporter.prepare_export_data()
        if answer["status"].error_message is None:
            answer["serialized_data"] = exporter.export_repr()

    def export_selected_players(self, update_widget_and_join_loop):
        """Export players for selection and bookmarked events."""
        title = EventSpec.menu_player_export[1]
        database = self.get_database(title)
        if not database:
            return None
        persons_sel = self._persons_grid.selection
        persons_bmk = self._persons_grid.bookmarks
        if len(persons_sel) + len(persons_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No identified persons are selected or bookmarked",
            )
            return False
        answer = {"status": None, "serialized_data": None}
        task.Task(
            database,
            self._export_selected_players,
            (database, persons_bmk, persons_sel, answer),
            update_widget_and_join_loop,
        ).start_and_join()
        if answer["status"] is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                message="\n\n".join(
                    (
                        "Export of selected persons failed",
                        "Unable to extract data",
                    )
                ),
                title=title,
            )
            return False
        if answer["status"].error_message is not None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                message="\n\n".join(
                    (
                        "Export of selected persons failed",
                        answer["status"].error_message,
                    )
                ),
                title=title,
            )
            return False
        directory = os.path.join(database.home_directory, REPORT_DIRECTORY)
        if not os.path.isdir(directory):
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        directory,
                        " is not a directory or does not exist\n\n",
                        "Please create this directory",
                    )
                ),
            )
        while True:
            export_file = os.path.join(
                directory,
                "_".join(
                    (
                        "aliases",
                        datetime.datetime.now().isoformat(
                            sep="_", timespec="seconds"
                        ),
                    )
                ),
            )
            if os.path.exists(export_file):
                if not tkinter.messagebox.askyesno(
                    parent=self.frame,
                    title=title,
                    message="".join(
                        (
                            os.path.basename(export_file),
                            " exists\n\nPlease try again",
                            " to get a new timestamp",
                        )
                    ),
                ):
                    tkinter.messagebox.showinfo(
                        parent=self.frame,
                        message="Export of persons cancelled",
                        title=title,
                    )
                    return False
                continue
            task.Task(
                database,
                export.write_export_file,
                (export_file, answer["serialized_data"]),
                update_widget_and_join_loop,
            ).start_and_join()
            tkinter.messagebox.showinfo(
                parent=self.frame,
                message="".join(
                    (
                        "Selected persons exported to\n\n",
                        export_file,
                    )
                ),
                title=title,
            )
            return True

    def get_database(self, title):
        """Return database if identified players list is attached to database.

        Return False otherwise after dialogue indicating problem.

        """
        persons_ds = self._persons_grid.datasource
        if persons_ds is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Identified Players list ",
                        "is not attached to database at present",
                    )
                ),
            )
            return False
        persons_db = persons_ds.dbhome
        if persons_db is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Identified Players list ",
                        "is not attached to database index at present",
                    )
                ),
            )
            return False
        return persons_db
