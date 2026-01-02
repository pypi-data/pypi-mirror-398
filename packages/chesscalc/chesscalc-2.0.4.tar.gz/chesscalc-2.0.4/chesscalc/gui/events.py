# events.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""List the events in the database."""

import tkinter
import os
import datetime

from solentware_bind.gui.bindings import Bindings

from . import eventsgrid
from .eventspec import EventSpec
from ..core import identify_event
from ..core import export
from ..shared import task
from .. import REPORT_DIRECTORY


class EventsError(Exception):
    """Raise exception in events module."""


class Events(Bindings):
    """Define widgets which list events of games."""

    def __init__(self, master, database):
        """Create the events widget."""
        super().__init__()
        self._events_grid = eventsgrid.EventsGrid(
            parent=master, database=database
        )

    @property
    def frame(self):
        """Return the top frame of the events widget."""
        return self._events_grid.frame

    @property
    def data_grid(self):
        """Return the events widget."""
        return self._events_grid

    def identify(self, update_widget_and_join_loop):
        """Identify bookmarked events as selected event."""
        title = EventSpec.menu_other_event_identify[1]
        database = self.get_database(title)
        if not database:
            return None
        events_sel = self._events_grid.selection
        events_bmk = self._events_grid.bookmarks
        if len(events_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No event is selected",
            )
            return False
        if len(events_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No events are bookmarked so no changes done",
            )
            return False
        if events_bmk == events_sel:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Selection and bookmark is same so no changes done",
            )
            return False
        new = set(events_bmk)
        if new.intersection(events_sel):
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Selection is one of bookmarked events ",
                        "so no changes done",
                    )
                ),
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_event.identify,
            (database, new, events_sel, answer),
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

    def break_selected(self, update_widget_and_join_loop):
        """Undo identification of bookmarked events as selection event."""
        title = EventSpec.menu_other_event_break[1]
        database = self.get_database(title)
        if not database:
            return None
        events_sel = self._events_grid.selection
        events_bmk = self._events_grid.bookmarks
        if len(events_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No event is selected",
            )
            return False
        if len(events_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No events are bookmarked so no changes done",
            )
            return False
        if events_bmk == events_sel:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Selection and bookmark is same so no changes done",
            )
            return False
        new = set(events_bmk)
        if new.intersection(events_sel):
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Selection is one of bookmarked events ",
                        "so no changes done",
                    )
                ),
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_event.break_bookmarked_aliases,
            (database, new, events_sel, answer),
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
        """Undo identification of all aliases of selected event."""
        title = EventSpec.menu_other_event_split[1]
        database = self.get_database(title)
        if not database:
            return None
        events_sel = self._events_grid.selection
        events_bmk = self._events_grid.bookmarks
        if len(events_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No event is selected",
            )
            return False
        if len(events_bmk) != 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Events are bookmarked so no changes done",
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_event.split_aliases,
            (database, events_sel, answer),
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
        """Undo identification of all aliases of selected event."""
        title = EventSpec.menu_other_event_change[1]
        database = self.get_database(title)
        if not database:
            return None
        events_sel = self._events_grid.selection
        events_bmk = self._events_grid.bookmarks
        if len(events_sel) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No event is selected",
            )
            return False
        if len(events_bmk) != 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="Events are bookmarked so no changes done",
            )
            return False
        answer = {"message": None}
        task.Task(
            database,
            identify_event.change_aliases,
            (database, events_sel, answer),
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

    def _export_players_in_selected_events(
        self, database, events_bmk, events_sel, answer
    ):
        """Prepare player data for export."""
        exporter = export.ExportEventPersons(database, events_bmk, events_sel)
        answer["status"] = exporter.prepare_export_data()
        if answer["status"].error_message is None:
            answer["serialized_data"] = exporter.export_repr()

    def export_players_in_selected_events(self, update_widget_and_join_loop):
        """Export players for selection and bookmarked events."""
        title = EventSpec.menu_other_event_export_persons[1]
        database = self.get_database(title)
        if not database:
            return None
        events_sel = self._events_grid.selection
        events_bmk = self._events_grid.bookmarks
        if len(events_sel) + len(events_bmk) == 0:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="No events are selected or bookmarked",
            )
            return False
        answer = {"status": None, "serialized_data": None}
        task.Task(
            database,
            self._export_players_in_selected_events,
            (database, events_bmk, events_sel, answer),
            update_widget_and_join_loop,
        ).start_and_join()
        if answer["status"] is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                message="\n\n".join(
                    (
                        "Export of event persons failed",
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
                        "Export of event persons failed",
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
                        "identities",
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
                        message="Export of event persons cancelled",
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
                        "Persons in selected events exported to\n\n",
                        export_file,
                    )
                ),
                title=title,
            )
            return True

    def get_database(self, title):
        """Return database if events list is attached to database.

        Return False otherwise after dialogue indicating problem.

        """
        events_ds = self._events_grid.datasource
        if events_ds is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Events list ",
                        "is not attached to database at present",
                    )
                ),
            )
            return False
        events_db = events_ds.dbhome
        if events_db is None:
            tkinter.messagebox.showinfo(
                parent=self.frame,
                title=title,
                message="".join(
                    (
                        "Events list ",
                        "is not attached to database index at present",
                    )
                ),
            )
            return False
        return events_db
