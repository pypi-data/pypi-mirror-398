# performancedu.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Define User Interface for deferred update process."""

import os
import datetime
import tkinter
import tkinter.font
import tkinter.messagebox
import queue
import multiprocessing
import multiprocessing.dummy

from solentware_misc.gui.logtextbase import LogTextBase

from solentware_bind.gui.bindings import Bindings

from solentware_base.core import constants as sb_core_constants

from .. import ERROR_LOG, APPLICATION_NAME, REPORT_DIRECTORY
from ..core import filespec
from ..shared import alldu


class _Reporter:
    """Helper class to keep 'LogText' API for adding text to log.

    Not used in dptcompatdu module but is used in chessdptdu module.

    """

    def __init__(self, append_text, append_text_only, empty):
        """Note the timestamp plus text, and text only, append methods."""
        self.append_text = append_text
        self.append_text_only = append_text_only
        self.empty = empty


class IncreaseDataProcess:
    """Define a process to do an increase data size (table B) process."""

    def __init__(self, database, report_queue, quit_event):
        """Provide queues for communication with GUI."""
        self.database = database
        self.report_queue = report_queue
        self.quit_event = quit_event
        self.process = multiprocessing.Process(
            target=self._increase_data_size,
            args=(),
        )
        self.stop_thread = None

    def _report_to_log(self, text):
        """Add text to report queue with timestamp."""
        day, hms = (
            datetime.datetime.now().isoformat(timespec="seconds").split("T")
        )
        self.report_queue.put("".join((day, " ", hms, "  ", text, "\n")))

    def _report_to_log_text_only(self, text):
        """Add text to report queue without timestamp."""
        self.report_queue.put("".join(("                     ", text, "\n")))

    def _increase_data_size(self):
        """Increase data size."""
        self.stop_thread = multiprocessing.dummy.DummyProcess(
            target=self._wait_for_quit_event
        )
        self.stop_thread.start()
        self._increase()
        self.quit_event.set()

    def _wait_for_quit_event(self):
        """Wait for quit event."""
        self.quit_event.wait()

    def _increase(self):
        """Increase data size in DPT games file."""
        database = self.database
        files = (filespec.GAME_FILE_DEF,)
        database.open_database(files=(filespec.GAME_FILE_DEF,))
        try:
            parameter = database.get_database_parameters(files=files)[
                filespec.GAME_FILE_DEF
            ]
            bsize = parameter["BSIZE"]
            bused = max(0, parameter["BHIGHPG"])
            bfree = bsize - bused
            dsize = parameter["DSIZE"]
            dused = parameter["DPGSUSED"]
            dfree = dsize - dused
            table = database.table[filespec.GAME_FILE_DEF]
            specification = database.specification[filespec.GAME_FILE_DEF]
            default_records = specification[sb_core_constants.DEFAULT_RECORDS]
            btod_factor = specification[filespec.BTOD_FACTOR]
            brecppg = table.filedesc[sb_core_constants.BRECPPG]
            bdefault = database.get_database_pages_for_record_counts(
                files={
                    filespec.GAME_FILE_DEF: (default_records, default_records)
                }
            )[filespec.GAME_FILE_DEF][0]
            bfree_recs = bfree * brecppg
            dfree_recs = (dfree * brecppg) // btod_factor
            blow = bfree + min(bdefault, bfree)
            bhigh = bfree + max(bdefault, bfree)
            blowrecs = bfree_recs + min(default_records, bfree_recs)
            bhighrecs = bfree_recs + max(default_records, bfree_recs)
            if len(table.get_extents()) % 2 == 0:
                if not tkinter.messagebox.askokcancel(
                    title="Increase Data Size",
                    message="".join(
                        (
                            "At present it is better to do index ",
                            "increases first for this file, if any ",
                            "are needed.\n\nIt is estimated the ",
                            "current index size can cope with an ",
                            "estimated extra ",
                            str(dfree_recs),
                            " games.\n\nPlease confirm you wish to ",
                            "continue with data increase.",
                        )
                    ),
                ):
                    return
            if blow != bhigh:
                choice = tkinter.messagebox.askyesnocancel(
                    title="Increase Data Size",
                    message="".join(
                        (
                            "Please choose between a data size increase ",
                            "to cope with an estimated extra ",
                            str(blowrecs),
                            " or ",
                            str(bhighrecs),
                            " games.\n\nThe current data size can cope ",
                            "with an estimated extra ",
                            str(bfree_recs),
                            " games.\n\nDo you want to increase the data ",
                            "size for the smaller number of games?",
                        )
                    ),
                )
                if choice is True:  # Yes
                    bincrease = blow - bfree
                    bextrarecs = blowrecs
                elif choice is False:  # No
                    bincrease = bhigh - bfree
                    bextrarecs = bhighrecs
                else:  # Cancel assumed (choice is None).
                    return
            else:
                choice = tkinter.messagebox.askokcancel(
                    title="Increase Data Size",
                    message="".join(
                        (
                            "Please confirm a data size increase ",
                            "to cope with an estimated extra ",
                            str(blowrecs),
                            " games.\n\nThe current data size can cope ",
                            "with an estimated extra ",
                            str(bfree_recs),
                            " games.",
                        )
                    ),
                )
                if choice is True:  # Yes
                    bincrease = blow - bfree
                    bextrarecs = blowrecs
                else:  # Cancel assumed (choice is None).
                    return
            table.opencontext.Increase(bincrease, False)
            self._report_to_log_text_only("")
            self._report_to_log("Data size increased.")
            self._report_to_log_text_only(
                " ".join(
                    (
                        "Estimate of standard profile games which fit:",
                        str(bextrarecs),
                    )
                )
            )
        finally:
            database.close_database()


class IncreaseIndexProcess:
    """Define a process to do an increase index size (table D) process."""

    def __init__(self, database, report_queue, quit_event):
        """Provide queues for communication with GUI."""
        self.database = database
        self.report_queue = report_queue
        self.quit_event = quit_event
        self.process = multiprocessing.Process(
            target=self._increase_index_size,
            args=(),
        )
        self.stop_thread = None

    def _report_to_log(self, text):
        """Add text to report queue with timestamp."""
        day, hms = (
            datetime.datetime.now().isoformat(timespec="seconds").split("T")
        )
        self.report_queue.put("".join((day, " ", hms, "  ", text, "\n")))

    def _report_to_log_text_only(self, text):
        """Add text to report queue without timestamp."""
        self.report_queue.put("".join(("                     ", text, "\n")))

    def _increase_index_size(self):
        """Increase index size."""
        self.stop_thread = multiprocessing.dummy.DummyProcess(
            target=self._wait_for_quit_event
        )
        self.stop_thread.start()
        self._increase()
        self.quit_event.set()

    def _wait_for_quit_event(self):
        """Wait for quit event."""
        self.quit_event.wait()

    def _increase(self):
        """Increase index size in DPT games file."""
        database = self.database
        files = (filespec.GAME_FILE_DEF,)
        database.open_database(files=(filespec.GAME_FILE_DEF,))
        try:
            parameter = database.get_database_parameters(files=files)[
                filespec.GAME_FILE_DEF
            ]
            bsize = parameter["BSIZE"]
            bused = max(0, parameter["BHIGHPG"])
            bfree = bsize - bused
            dsize = parameter["DSIZE"]
            dused = parameter["DPGSUSED"]
            dfree = dsize - dused
            table = database.table[filespec.GAME_FILE_DEF]
            specification = database.specification[filespec.GAME_FILE_DEF]
            default_records = specification[sb_core_constants.DEFAULT_RECORDS]
            btod_factor = specification[filespec.BTOD_FACTOR]
            brecppg = table.filedesc[sb_core_constants.BRECPPG]
            ddefault = database.get_database_pages_for_record_counts(
                files={
                    filespec.GAME_FILE_DEF: (default_records, default_records)
                }
            )[filespec.GAME_FILE_DEF][1]
            bfree_recs = bfree * brecppg
            dfree_recs = (dfree * brecppg) // btod_factor
            dlow = dfree + min(ddefault, dfree)
            dhigh = dfree + max(ddefault, dfree)
            dlowrecs = dfree_recs + min(default_records, dfree_recs)
            dhighrecs = dfree_recs + max(default_records, dfree_recs)
            if len(table.get_extents()) % 2 != 0:
                if not tkinter.messagebox.askokcancel(
                    title="Increase Index Size",
                    message="".join(
                        (
                            "At present it is better to do data ",
                            "increases first for this file, if any ",
                            "are needed.\n\nIt is estimated the ",
                            "current data size can cope with an ",
                            "estimated extra ",
                            str(bfree_recs),
                            " games.\n\nPlease confirm you wish to ",
                            "continue with index increase.",
                        )
                    ),
                ):
                    return
            if dlow != dhigh:
                choice = tkinter.messagebox.askyesnocancel(
                    title="Increase Index Size",
                    message="".join(
                        (
                            "Please choose between an index size increase ",
                            "to cope with an estimated extra ",
                            str(dlowrecs),
                            " or ",
                            str(dhighrecs),
                            " games.\n\nThe current index size can cope ",
                            "with an estimated extra ",
                            str(dfree_recs),
                            " games.\n\nDo you want to increase the index ",
                            "size for the smaller number of games?",
                        )
                    ),
                )
                if choice is True:  # Yes
                    dincrease = dlow - dfree
                    dextrarecs = dlowrecs
                elif choice is False:  # No
                    dincrease = dhigh - dfree
                    dextrarecs = dhighrecs
                else:  # Cancel assumed (choice is None).
                    return
            else:
                choice = tkinter.messagebox.askokcancel(
                    title="Increase Index Size",
                    message="".join(
                        (
                            "Please confirm an index size increase ",
                            "to cope with an estimated extra ",
                            str(dlowrecs),
                            " games.\n\nThe current index size can cope ",
                            "with an estimated extra ",
                            str(dfree_recs),
                            " games.",
                        )
                    ),
                )
                if choice is True:  # Yes
                    dincrease = dlow - dfree
                    dextrarecs = dlowrecs
                else:  # Cancel assumed (choice is None).
                    return
            table.opencontext.Increase(dincrease, True)
            self._report_to_log_text_only("")
            self._report_to_log("Index size increased.")
            self._report_to_log_text_only(
                " ".join(
                    (
                        "Estimate of standard profile games which fit:",
                        str(dextrarecs),
                    )
                )
            )
        finally:
            database.close_database()


class DeferredUpdateProcess:
    """Define a process to do a deferred update task."""

    def __init__(
        self,
        database,
        method,
        du_class,
        report_queue,
        quit_event,
        increases,
        home_directory,
        pgn_directory,
        du_file,
    ):
        """Provide queues for communication with GUI."""
        self.database = database
        self.method = method
        self.du_class = du_class
        self.report_queue = report_queue
        self.quit_event = quit_event
        self.increases = increases
        self.home_directory = home_directory
        self.pgn_directory = pgn_directory
        self.du_file = du_file
        self.process = multiprocessing.Process(
            target=self._run_import,
            args=(),
        )

    def _report_to_log(self, text):
        """Add text to report queue with timestamp."""
        day, hms = (
            datetime.datetime.now().isoformat(timespec="seconds").split("T")
        )
        self.report_queue.put("".join((day, " ", hms, "  ", text, "\n")))

    def _report_to_log_text_only(self, text):
        """Add text to report queue without timestamp."""
        self.report_queue.put("".join(("                     ", text, "\n")))

    def _run_import(self):
        """Invoke method to do the deferred update and display job status."""
        self.method(
            self.home_directory,
            self.du_class,
            self.pgn_directory,
            file=self.du_file,
            reporter=_Reporter(
                self._report_to_log,
                self._report_to_log_text_only,
                self.report_queue.empty,
            ),
            quit_event=self.quit_event,
            increases=self.increases,
        )


class DeferredUpdate(Bindings):
    """Connect a chess performance database with UI for deferred update."""

    def __init__(
        self,
        deferred_update_module=None,
        database_class=None,
        home_directory=None,
        pgn_directory=None,
        sample=5000,
    ):
        """Create the database and User Interface objects.

        deferred_update_module - module with methods to do update tasks.
        database_class - access the database with an instance of this class.
        sample - estimate import size from first 'sample' games in PGN file.

        The deferred update module for each database engine will have one or
        more methods to do tasks as the target method of a multiprocessing
        Process: so these methods must have the same name in each module.

        """
        super().__init__()
        self.set_error_file_name(os.path.join(home_directory, ERROR_LOG))
        self.report_queue = multiprocessing.Queue()
        self.quit_event = multiprocessing.Event()
        self.increases = multiprocessing.Array("i", [0, 0, 0, 0])
        self.home_directory = home_directory
        self.pgn_directory = pgn_directory
        self.deferred_update_module = deferred_update_module
        self.sample = sample
        self._import_done = False
        self._import_job = None
        self._task_name = "estimating"  # Placeholder: no estimating done.
        self.database = database_class(
            home_directory,
            allowcreate=True,
            sysfolder=os.path.join(
                home_directory, sb_core_constants.DPT_SYSFUL_FOLDER
            ),
            deferupdatefiles={filespec.GAME_FILE_DEF},
        )

        self.root = tkinter.Tk()
        self.root.wm_title(
            " - ".join(
                (
                    " ".join((APPLICATION_NAME, "Import")),
                    os.path.basename(home_directory),
                )
            )
        )
        frame = tkinter.Frame(master=self.root)
        frame.pack(side=tkinter.BOTTOM)
        # Not yet sure 'self.buttonframe' should become 'buttonframe'.
        self.buttonframe = tkinter.Frame(master=frame)
        self.buttonframe.pack(side=tkinter.BOTTOM)
        tkinter.Button(
            master=self.buttonframe,
            text="Dismiss Log",
            underline=0,
            command=self.try_command(
                self._dismiss_import_log,
                self.buttonframe,
            ),
        ).pack(side=tkinter.RIGHT, padx=12)
        tkinter.Button(
            master=self.buttonframe,
            text="Stop Process",
            underline=0,
            command=self.try_command(self._stop_task, self.buttonframe),
        ).pack(side=tkinter.RIGHT, padx=12)
        tkinter.Button(
            master=self.buttonframe,
            text="Import",
            underline=0,
            command=self.try_command(self._do_import, self.buttonframe),
        ).pack(side=tkinter.RIGHT, padx=12)
        if self._database_looks_like_dpt():
            tkinter.Button(
                master=self.buttonframe,
                text="Increase Index",
                underline=13,
                command=self.try_command(
                    self._increase_index, self.buttonframe
                ),
            ).pack(side=tkinter.RIGHT, padx=12)
            tkinter.Button(
                master=self.buttonframe,
                text="Increase Data",
                underline=9,
                command=self.try_command(
                    self._increase_data, self.buttonframe
                ),
            ).pack(side=tkinter.RIGHT, padx=12)

        self.report = LogTextBase(
            master=self.root,
            cnf={"wrap": tkinter.WORD, "undo": tkinter.FALSE},
        )
        self.report.focus_set()
        if self._database_looks_like_dpt():
            self.bind(
                self.report,
                "<Alt-d>",
                function=self.try_event(self._increase_data),
            )
            self.bind(
                self.report,
                "<Alt-x>",
                function=self.try_event(self._increase_index),
            )
        self.bind(
            self.report,
            "<Alt-i>",
            function=self.try_event(self._do_import),
        )
        self.bind(
            self.report,
            "<Alt-d>",
            function=self.try_event(
                self._dismiss_import_log,
            ),
        )
        self.bind(
            self.report,
            "<Alt-s>",
            function=self.try_event(self._stop_task),
        )

        self.report.tag_configure(
            "margin",
            lmargin2=tkinter.font.nametofont(self.report.cget("font")).measure(
                "2010-05-23 10:20:57  "
            ),
        )
        self.tagstart = "1.0"
        self._report_to_log(
            "".join(("Ready to import to database ", home_directory, "."))
        )
        self.report.pack(
            side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.TRUE
        )
        self.root.iconify()
        self.root.update()
        self.root.deiconify()
        self._allow_task = True
        self._add_queued_reports_to_log()

    def _database_looks_like_dpt(self):
        """Return True if database attribute signature looks like DPT.

        Check a few attriute names expected only in Database class in
        solentware_base.core._dpt module.

        """
        # This describes situation before changes to resolve problem, but
        # the return value remains relevant.
        # An alternative implementation of this difference calls a method
        # add_import_buttons() rather than add the buttons if the test
        # here returns True.  Two versions of add_import_buttons() are
        # defined in classes ..dpt.chessdptdu.ChessDatabase and
        # ..shared.dptcompatdu.DptCompatdu and the class hierarchy does
        # the test implemented here.  At present that implementation fails
        # because module pickling errors occur for the import action if
        # preceded by an increase action: but some solved problems in this
        # implementation hint at changes which might allow the alternative
        # implementation to succeed.  A practical benefit of the alternative
        # is losing the process startup overhead in the two (quite quick)
        # increase actions relevant only in DPT.
        return hasattr(self.database, "parms") and hasattr(
            self.database, "msgctl"
        )

    def _report_to_log(self, text):
        """Add text to report queue with timestamp."""
        day, hms = (
            datetime.datetime.now().isoformat(timespec="seconds").split("T")
        )
        self.report_queue.put("".join((day, " ", hms, "  ", text, "\n")))

    def _report_to_log_text_only(self, text):
        """Add text to report queue without timestamp."""
        self.report_queue.put("".join(("                     ", text, "\n")))

    def _add_queued_reports_to_log(self):
        """Check report queue every 200ms and add reports to log."""
        # Items are put on queue infrequently relative to polling, so testing
        # the unreliable qsize() value is worthwhile because it will usually
        # be 0 thus avoiding the Empty exception.
        while self.report_queue.qsize():
            try:
                self.report.append_raw_text(self.report_queue.get_nowait())
            except queue.Empty:
                pass
        self.root.after(200, self._add_queued_reports_to_log)

    def _deferred_update_stage_join(self):
        """join() deferred_update process then allow next stage."""
        self.du_task.process.join()
        self._allow_task = True

    def _deferred_update_import_join(self):
        """Delegate to _deferred_update_stage_join then copy players."""
        self._deferred_update_stage_join()
        self._import_done = True

        # Populate player file with player names from imported games.
        self._allow_task = False
        self._task_name = "copy players"
        self.quit_event.clear()
        self.du_task = DeferredUpdateProcess(
            self.database,
            alldu.do_players_deferred_update,
            self.deferred_update_module.DatabaseSU,
            self.report_queue,
            self.quit_event,
            self.increases,
            self.home_directory,
            self.pgn_directory,
            filespec.PLAYER_FILE_DEF,
        )
        self.du_task.process.start()
        quit_thread = multiprocessing.dummy.DummyProcess(
            target=self._deferred_update_copy_players_join
        )
        quit_thread.start()

    def _deferred_update_copy_players_join(self):
        """Delegate to _deferred_update_stage_join then copy events."""
        self._deferred_update_stage_join()

        # Populate player file with event names from imported games.
        self._allow_task = False
        self._task_name = "copy events"
        self.quit_event.clear()
        self.du_task = DeferredUpdateProcess(
            self.database,
            alldu.do_events_deferred_update,
            self.deferred_update_module.DatabaseSU,
            self.report_queue,
            self.quit_event,
            self.increases,
            self.home_directory,
            self.pgn_directory,
            filespec.EVENT_FILE_DEF,
        )
        self.du_task.process.start()
        quit_thread = multiprocessing.dummy.DummyProcess(
            target=self._deferred_update_copy_events_join
        )
        quit_thread.start()

    def _deferred_update_copy_events_join(self):
        """Delegate to _deferred_update_stage_join then copy time limits."""
        self._deferred_update_stage_join()

        # Populate player file with time limit names from imported games.
        self._allow_task = False
        self._task_name = "copy time limits"
        self.quit_event.clear()
        self.du_task = DeferredUpdateProcess(
            self.database,
            alldu.do_time_controls_deferred_update,
            self.deferred_update_module.DatabaseSU,
            self.report_queue,
            self.quit_event,
            self.increases,
            self.home_directory,
            self.pgn_directory,
            filespec.TIME_FILE_DEF,
        )
        self.du_task.process.start()
        quit_thread = multiprocessing.dummy.DummyProcess(
            target=self._deferred_update_copy_time_controls_join
        )
        quit_thread.start()

    def _deferred_update_copy_time_controls_join(self):
        """Delegate to _deferred_update_stage_join then copy terminations."""
        self._deferred_update_stage_join()

        # Populate player file with mode names from imported games.
        self._allow_task = False
        self._task_name = "copy terminations"
        self.quit_event.clear()
        self.du_task = DeferredUpdateProcess(
            self.database,
            alldu.do_terminations_deferred_update,
            self.deferred_update_module.DatabaseSU,
            self.report_queue,
            self.quit_event,
            self.increases,
            self.home_directory,
            self.pgn_directory,
            filespec.TERMINATION_FILE_DEF,
        )
        self.du_task.process.start()
        quit_thread = multiprocessing.dummy.DummyProcess(
            target=self._deferred_update_copy_terminations_join
        )
        quit_thread.start()

    def _deferred_update_copy_terminations_join(self):
        """Delegate to _deferred_update_stage_join then copy player types."""
        self._deferred_update_stage_join()

        # Populate player file with mode names from imported games.
        self._allow_task = False
        self._task_name = "copy player types"
        self.quit_event.clear()
        self.du_task = DeferredUpdateProcess(
            self.database,
            alldu.do_player_types_deferred_update,
            self.deferred_update_module.DatabaseSU,
            self.report_queue,
            self.quit_event,
            self.increases,
            self.home_directory,
            self.pgn_directory,
            filespec.PLAYERTYPE_FILE_DEF,
        )
        self.du_task.process.start()
        quit_thread = multiprocessing.dummy.DummyProcess(
            target=self._deferred_update_copy_player_types_join
        )
        quit_thread.start()

    def _deferred_update_copy_player_types_join(self):
        """Delegate to _deferred_update_stage_join then copy modes."""
        self._deferred_update_stage_join()

        # Populate player file with mode names from imported games.
        self._allow_task = False
        self._task_name = "copy modes"
        self.quit_event.clear()
        self.du_task = DeferredUpdateProcess(
            self.database,
            alldu.do_modes_deferred_update,
            self.deferred_update_module.DatabaseSU,
            self.report_queue,
            self.quit_event,
            self.increases,
            self.home_directory,
            self.pgn_directory,
            filespec.MODE_FILE_DEF,
        )
        self.du_task.process.start()
        quit_thread = multiprocessing.dummy.DummyProcess(
            target=self._deferred_update_copy_modes_join
        )
        quit_thread.start()

    def _deferred_update_copy_modes_join(self):
        """Delegate to _deferred_update_stage_join.

        Copy playing modes is final deferred update copy action.

        """
        self._deferred_update_stage_join()

    def _increase_data(self, event=None):
        """Run Increase Data Size process."""
        del event
        if not self._allow_task:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Increase Data",
                message="".join(
                    (
                        "Cannot start increase data because a task is in ",
                        "progress.\n\nThe current task must be allowed to ",
                        "finish, or be stopped, before starting task.",
                    )
                ),
            )
            return
        if self._import_done:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Increase Data",
                message="".join(
                    (
                        "The import has been done.",
                        "\n\nIncrease data is intended for before import.",
                    )
                ),
            )
            return
        self._allow_task = False
        self._task_name = "increase data"
        self.quit_event.clear()
        self.du_task = IncreaseDataProcess(
            self.database,
            self.report_queue,
            self.quit_event,
        )
        self.du_task.process.start()
        self.quit_thread = multiprocessing.dummy.DummyProcess(
            target=self._deferred_update_stage_join
        )
        self.quit_thread.start()

    def _increase_index(self, event=None):
        """Run Increase Index Size process."""
        del event
        if not self._allow_task:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Increase Index",
                message="".join(
                    (
                        "Cannot start increase index because a task is in ",
                        "progress.\n\nThe current task must be allowed to ",
                        "finish, or be stopped, before starting task.",
                    )
                ),
            )
            return
        if self._import_done:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Increase Index",
                message="".join(
                    (
                        "The import has been done.",
                        "\n\nIncrease index is intended for before import.",
                    )
                ),
            )
            return
        self._allow_task = False
        self._task_name = "increase index"
        self.quit_event.clear()
        self.du_task = IncreaseIndexProcess(
            self.database,
            self.report_queue,
            self.quit_event,
        )
        self.du_task.process.start()
        self.quit_thread = multiprocessing.dummy.DummyProcess(
            target=self._deferred_update_stage_join
        )
        self.quit_thread.start()

    def _do_import(self, event=None):
        """Run import process if allowed and not already run.

        event is ignored and is present for compatibility between button click
        and keypress.

        """
        del event
        if not self._allow_task:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Import",
                message="".join(
                    (
                        "Cannot start import because a task is in progress",
                        ".\n\nThe current task must be allowed to finish, ",
                        "or be stopped, before starting task.",
                    )
                ),
            )
            return
        if self._import_done:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Import",
                message="".join(
                    (
                        "The import has been done.",
                        "\n\nDismiss Log and start again to repeat it or ",
                        "do another one.",
                    )
                ),
            )
            return
        if not tkinter.messagebox.askokcancel(
            parent=self.root,
            title="Import",
            message="".join(("Please confirm the import is to be started.",)),
        ):
            return

        # Import games from a directory tree containing PGN files.
        self._allow_task = False
        self._task_name = "import"
        self.quit_event.clear()
        self.du_task = DeferredUpdateProcess(
            self.database,
            alldu.do_deferred_update,
            self.deferred_update_module.Database,
            self.report_queue,
            self.quit_event,
            self.increases,
            self.home_directory,
            self.pgn_directory,
            filespec.GAME_FILE_DEF,
        )
        self.du_task.process.start()
        self.quit_thread = multiprocessing.dummy.DummyProcess(
            target=self._deferred_update_import_join
        )
        self.quit_thread.start()

    def _stop_task(self, event=None):
        """Stop task.

        event is ignored and is present for compatibility between button click
        and keypress.

        """
        del event
        if self._allow_task:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Stop",
                message="No task running to be stopped.",
            )
            return
        if not tkinter.messagebox.askokcancel(
            parent=self.root,
            title="Stop",
            message=self._task_name.join(
                ("Please confirm the ", " task is to be stopped.")
            ),
        ):
            return
        self.quit_event.set()

    def _dismiss_import_log(self, event=None):
        """Dismiss log display and quit process.

        event is ignored and is present for compatibility between button click
        and keypress.

        """
        del event
        if not self._allow_task:
            tkinter.messagebox.showinfo(
                parent=self.root,
                title="Dismiss",
                message="".join(
                    (
                        "Cannot dismiss because a task is in progress",
                        ".\n\nThe current task must be allowed to finish, ",
                        "or be stopped, before dismissing.",
                    )
                ),
            )
            return
        if tkinter.messagebox.askyesno(
            parent=self.root,
            title="Dismiss",
            message="".join(
                (
                    "Do you want to dismiss the import log?\n\n",
                    "The log will be saved in\n'ImportLog_<time stamp>'\n",
                    "on dismissal.",
                )
            ),
        ):
            directory = os.path.join(self.home_directory, REPORT_DIRECTORY)
            if not os.path.isdir(directory):
                tkinter.messagebox.showinfo(
                    parent=self.root,
                    title="Dismiss",
                    message="".join(
                        (
                            directory,
                            " is not a directory or does not exist\n\n",
                            "Please create this directory",
                        )
                    ),
                )
            while True:
                log_file = os.path.join(
                    directory,
                    "_".join(
                        (
                            "ImportLog",
                            datetime.datetime.now().isoformat(
                                sep="_", timespec="seconds"
                            ),
                        )
                    ),
                )
                if os.path.exists(log_file):
                    tkinter.messagebox.showinfo(
                        parent=self.root,
                        title="Dismiss",
                        message="".join(
                            (
                                os.path.basename(log_file),
                                " exists\n\nPlease try again",
                                " to get a new timestamp",
                            )
                        ),
                    )
                    continue
                with open(log_file, mode="w", encoding="utf-8") as logfile:
                    logfile.write(self.report.get("1.0", tkinter.END))
                break
            self.root.destroy()
