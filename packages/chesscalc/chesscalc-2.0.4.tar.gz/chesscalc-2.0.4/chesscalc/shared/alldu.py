# alldu.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions, and Alldu class for methods, used by most database interfaces.

'Most' means all database interfaces except DPT.
"""
import os

from solentware_base.core.segmentsize import SegmentSize
from solentware_base.core.constants import FILEDESC, DPT_SYSFUL_FOLDER

from ..core.filespec import FileSpec
from ..core import eventrecord
from ..core import gamerecord
from ..core import moderecord
from ..core import playerrecord
from ..core import playertyperecord
from ..core import selectorrecord
from ..core import terminationrecord
from ..core import timecontrolrecord
from .. import ERROR_LOG, write_error_to_log
from ..core import pgnheaders


def du_import(
    cdb,
    pgn_directory,
    indexing=True,
    file=None,
    reporter=None,
    quit_event=None,
    increases=None,
):
    """Import games from files in pgn_directory into open database cdb.

    cdb         Database instance which does the deferred updates.
    pgn_directory   Name of directory containing PGN game scores to be
                imported.  Sub-directories are searched recursively.
    indexing    True means do import within set_defer_update block,
                False means do import within start_transaction block.
                Not passed to importer instance's <import> method because
                the commit() and start_transaction() calls at segment
                boundaries in deferred update mode do the right thing with
                the current database engine choices.
    file        name of table in database to be updated.
    reporter    None or an object with append_text and append_text_only
                methods taking a str argument.
    quit_event  passed to the importer instance's <import> method.
                None or an Event instance.
    increases   <obsolete>? <for DPT only> <pre-import table size increases>
                intention is increase data and index sizes during import,
                especially if it is possible to recover from Table D full
                conditions simply by increasing the index size and repeating
                the import without adding any records (and re-applying any
                left over deferred index updates).
                Increase during import is allowed only if no recordsets,
                cursors, and so forth, are open on the table (DPT file)
                being updated.

    """
    importer = gamerecord.GameDBImporter()
    for key in cdb.table.keys():
        if key == file:
            # if hasattr(cdb.__class__, "segment_size_bytes"):
            #    #if increases is None:
            #    #    counts = [0, 0]
            #    #else:
            #    #    counts = [increases[0], increases[1]]
            #    #cdb.increase_database_record_capacity(files={key: counts})
            #    #_du_report_increases(reporter, key, counts)
            #    if reporter is not None:
            #        reporter.append_text_only("")
            #        reporter.append_text(
            #            "Count games (for file sizing) started."
            #        )
            #    count = importer.count_pgn_games(
            #        cdb,
            #        pgn_directory,
            #        reporter=reporter,
            #        quit_event=quit_event,
            #    )
            #    if reporter is not None:
            #        reporter.append_text(str(count) + " games found.")
            #    table = cdb.table[file]
            #    bpages_needed = table.get_pages_for_record_counts(
            #        counts=(count, 0)
            #    )[0]
            #    parameter = table.get_file_parameters(cdb.dbenv)
            #    bfree = parameter["BSIZE"] - max(0, parameter["BHIGHPG"])
            #    if bpages_needed * 2 > bfree:
            #        table.opencontext.Increase(bpages_needed * 2, False)
            #        if reporter is not None:
            #            reporter.append_text(
            #                "Data size increased to hold nominal extra " +
            #                str(count*2) + " games."
            #            )
            break
    else:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                repr(file).join(
                    ("Unable to import to '", "': not found in database.")
                )
            )
            reporter.append_text_only("")
        return
    if reporter is not None:
        reporter.append_text_only("")
        reporter.append_text("Import started.")
    if indexing:
        cdb.set_defer_update()
    else:
        cdb.start_transaction()
    try:
        if not importer.import_pgn_headers(
            cdb,
            pgn_directory,
            reporter=reporter,
            quit_event=quit_event,
        ):
            cdb.backout()
            return
        if reporter is not None:
            reporter.append_text("Finishing extract: please wait.")
            reporter.append_text_only("")
        if indexing:
            cdb.do_final_segment_deferred_updates()
    except Exception as exc:
        _report_exception(cdb, reporter, exc)
        raise

    # DPT database engine needs the test for empty queue because all the
    # deferred index updates are applied in the Close() method called when
    # closing the file on completion of the task (well after exit from
    # du_import), in particular the C++ code in the dptapi extension, so the
    # queued reports have to be processed before entering that code to avoid
    # an unresponsive GUI; and no indication of progress.
    # The other database engines do not cause the GUI to become unresponsive
    # in the absence of the test for an empty queue.
    if indexing:
        dsize = _pre_unset_defer_update_reports(cdb, file, reporter)
        cdb.unset_defer_update()
        _post_unset_defer_update_reports(cdb, file, reporter, dsize)
        if reporter is not None:
            while not reporter.empty():
                pass
    else:
        if reporter is not None:
            while not reporter.empty():
                pass
        cdb.commit()


# DPT database engine specific.
# Maybe will have to go into solentwre_base, but do not want the reporter
# code there.
# Non-DPT code has get_database_table_sizes() return {}.
# Problem is DPT does things in unset_defer_update which need before and
# after reports, while other engines do different things which do not
# need reports at all.
def _pre_unset_defer_update_reports(database, file, reporter):
    """Generate reports relevant to database engine before completion."""
    if reporter is None:
        return None
    for name, sizes in database.get_database_table_sizes(
        files=set((file,))
    ).items():
        reporter.append_text(
            "".join(("Data import for ", name, " completed."))
        )
        dsize = sizes["DSIZE"]
        reporter.append_text_only(
            "Data area size after import: " + str(sizes["BSIZE"])
        )
        reporter.append_text_only(
            "".join(
                (
                    "Data pages used in import: ",
                    str(
                        sizes["BHIGHPG"]
                        - database.table[name].table_b_pages_used
                    ),
                )
            )
        )
        reporter.append_text_only(
            "Index area size before import: " + str(dsize)
        )
        reporter.append_text_only("")
        return dsize


# DPT database engine specific.
# Maybe will have to go into solentwre_base, but do not want the reporter
# code there.
# Non-DPT code has get_database_table_sizes() return {}.
# Problem is DPT does things in unset_defer_update which need before and
# after reports, while other engines do different things which do not
# need reports at all.
def _post_unset_defer_update_reports(database, file, reporter, dsize):
    """Generate reports relevant to database engine after completion."""
    if reporter is None:
        return
    for name, sizes in database.get_database_table_sizes(
        files=set((file,))
    ).items():
        reporter.append_text("".join(("Index size status for ", name, ".")))
        new_dsize = sizes["DSIZE"]
        reporter.append_text_only("Index area size: " + str(new_dsize))
        reporter.append_text_only(
            "".join(
                (
                    "Index area size increase: ",
                    str(new_dsize - dsize),
                )
            )
        )
        reporter.append_text_only(
            "".join(
                (
                    "Index area free: ",
                    str(new_dsize - sizes["DPGSUSED"]),
                )
            )
        )
        reporter.append_text_only("")
        reporter.append_text(
            "".join(("Applying Index update for ", name, ": please wait."))
        )
        reporter.append_text_only("")


def do_deferred_update(dbpath, dbclass, *args, file=None, **kwargs):
    """Open database, delegate to du_import, and close database."""
    cdb = dbclass(dbpath, allowcreate=True)
    cdb.open_database()
    du_import(cdb, *args, file=file, **kwargs)
    cdb.close_database()


def do_su_deferred_update(
    dbpath, dbclass, pgn_directory, *args, file=None, **kwargs
):
    """Open database, delegate to games_du_copy, and close database.

    Argument pgn_directory is supplied but not used in the games_du_copy()
    call.

    Not implemented: assume du_import() is the relevant function but with
    DatabaseSU as dbclass.

    """


def do_games_deferred_update(
    dbpath, dbclass, pgn_directory, *args, file=None, **kwargs
):
    """Open database, delegate to games_du_copy, and close database.

    Argument pgn_directory is supplied but not used in the games_du_copy()
    call.

    Not implemented: assume games_du_copy() is the relevant function with
    DatabaseSU as dbclass.

    """


def players_du_copy(
    cdb,
    file=None,
    reporter=None,
    quit_event=None,
    increases=None,
):
    """Import games from files in pgn_directory into open database cdb."""
    importer = playerrecord.PlayerDBImporter()
    for key in cdb.table.keys():
        if key == file:
            if increases is None:
                counts = [0, 0]
            else:
                counts = [increases[0], increases[1]]
            cdb.increase_database_record_capacity(files={key: counts})
            _du_report_increases(reporter, key, counts)
            break
    else:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                repr(file).join(
                    ("Unable to copy to '", "': not found in database.")
                )
            )
            reporter.append_text_only("")
        return
    # cdb.set_defer_update()
    cdb.start_transaction()
    try:
        if not importer.copy_player_names_from_games(
            cdb,
            reporter=reporter,
            quit_event=quit_event,
        ):
            cdb.backout()
            return
        if reporter is not None:
            reporter.append_text("Finishing copy: please wait.")
            reporter.append_text_only("")
        # cdb.do_final_segment_deferred_updates()
    except Exception as exc:
        _report_exception(cdb, reporter, exc)
        raise
    # cdb.unset_defer_update()
    cdb.commit()


def do_players_deferred_update(
    dbpath, dbclass, pgn_directory, *args, file=None, **kwargs
):
    """Open database, delegate to players_du_copy, and close database.

    Argument pgn_directory is supplied but not used in the players_du_copy()
    call.

    """
    cdb = _create_database_sysful(dbpath, dbclass)
    cdb.open_database()
    players_du_copy(cdb, *args, file=file, **kwargs)
    cdb.close_database()


def events_du_copy(
    cdb,
    file=None,
    reporter=None,
    quit_event=None,
    increases=None,
):
    """Import games from files in pgn_directory into open database cdb."""
    importer = eventrecord.EventDBImporter()
    for key in cdb.table.keys():
        if key == file:
            if increases is None:
                counts = [0, 0]
            else:
                counts = [increases[0], increases[1]]
            cdb.increase_database_record_capacity(files={key: counts})
            _du_report_increases(reporter, key, counts)
            break
    else:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                repr(file).join(
                    ("Unable to copy to '", "': not found in database.")
                )
            )
            reporter.append_text_only("")
        return
    # cdb.set_defer_update()
    cdb.start_transaction()
    try:
        if not importer.copy_event_names_from_games(
            cdb,
            reporter=reporter,
            quit_event=quit_event,
        ):
            cdb.backout()
            return
        if reporter is not None:
            reporter.append_text("Finishing copy: please wait.")
            reporter.append_text_only("")
        # cdb.do_final_segment_deferred_updates()
    except Exception as exc:
        _report_exception(cdb, reporter, exc)
        raise
    # cdb.unset_defer_update()
    cdb.commit()


def do_events_deferred_update(
    dbpath, dbclass, pgn_directory, *args, file=None, **kwargs
):
    """Open database, delegate to events_du_copy, and close database.

    Argument pgn_directory is supplied but not used in the events_du_copy()
    call.

    """
    cdb = _create_database_sysful(dbpath, dbclass)
    cdb.open_database()
    events_du_copy(cdb, *args, file=file, **kwargs)
    cdb.close_database()


def time_controls_du_copy(
    cdb,
    file=None,
    reporter=None,
    quit_event=None,
    increases=None,
):
    """Import games from files in pgn_directory into open database cdb."""
    importer = timecontrolrecord.TimeControlDBImporter()
    for key in cdb.table.keys():
        if key == file:
            if increases is None:
                counts = [0, 0]
            else:
                counts = [increases[0], increases[1]]
            cdb.increase_database_record_capacity(files={key: counts})
            _du_report_increases(reporter, key, counts)
            break
    else:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                repr(file).join(
                    ("Unable to copy to '", "': not found in database.")
                )
            )
            reporter.append_text_only("")
        return
    # cdb.set_defer_update()
    cdb.start_transaction()
    try:
        if not importer.copy_time_control_names_from_games(
            cdb,
            reporter=reporter,
            quit_event=quit_event,
        ):
            cdb.backout()
            return
        if reporter is not None:
            reporter.append_text("Finishing copy: please wait.")
            reporter.append_text_only("")
        # cdb.do_final_segment_deferred_updates()
    except Exception as exc:
        _report_exception(cdb, reporter, exc)
        raise
    # cdb.unset_defer_update()
    cdb.commit()


def do_time_controls_deferred_update(
    dbpath, dbclass, pgn_directory, *args, file=None, **kwargs
):
    """Open database, delegate to time_controls_du_copy, and close database.

    Argument pgn_directory is supplied but not used in the
    time_controls_du_copy() call.

    """
    cdb = _create_database_sysful(dbpath, dbclass)
    cdb.open_database()
    time_controls_du_copy(cdb, *args, file=file, **kwargs)
    cdb.close_database()


def modes_du_copy(
    cdb,
    file=None,
    reporter=None,
    quit_event=None,
    increases=None,
):
    """Import games from files in pgn_directory into open database cdb."""
    importer = moderecord.ModeDBImporter()
    for key in cdb.table.keys():
        if key == file:
            if increases is None:
                counts = [0, 0]
            else:
                counts = [increases[0], increases[1]]
            cdb.increase_database_record_capacity(files={key: counts})
            _du_report_increases(reporter, key, counts)
            break
    else:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                repr(file).join(
                    ("Unable to copy to '", "': not found in database.")
                )
            )
            reporter.append_text_only("")
        return
    # cdb.set_defer_update()
    cdb.start_transaction()
    try:
        if not importer.copy_mode_names_from_games(
            cdb,
            reporter=reporter,
            quit_event=quit_event,
        ):
            cdb.backout()
            return
        if reporter is not None:
            reporter.append_text("Finishing copy: please wait.")
            reporter.append_text_only("")
        # cdb.do_final_segment_deferred_updates()
    except Exception as exc:
        _report_exception(cdb, reporter, exc)
        raise
    # cdb.unset_defer_update()
    cdb.commit()


def do_modes_deferred_update(
    dbpath,
    dbclass,
    pgn_directory,
    *args,
    reporter=None,
    file=None,
    **kwargs,
):
    """Open database, delegate to modes_du_copy, and close database.

    Argument pgn_directory is supplied but not used in the modes_du_copy()
    call.

    This is final copy stage so report finished when database is closed.

    """
    cdb = _create_database_sysful(dbpath, dbclass)
    cdb.open_database()
    modes_du_copy(cdb, *args, reporter=reporter, file=file, **kwargs)
    cdb.close_database()
    if reporter is not None:
        reporter.append_text("Import finished.")
        reporter.append_text_only("")


def terminations_du_copy(
    cdb,
    file=None,
    reporter=None,
    quit_event=None,
    increases=None,
):
    """Import games from files in pgn_directory into open database cdb."""
    importer = terminationrecord.TerminationDBImporter()
    for key in cdb.table.keys():
        if key == file:
            if increases is None:
                counts = [0, 0]
            else:
                counts = [increases[0], increases[1]]
            cdb.increase_database_record_capacity(files={key: counts})
            _du_report_increases(reporter, key, counts)
            break
    else:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                repr(file).join(
                    ("Unable to copy to '", "': not found in database.")
                )
            )
            reporter.append_text_only("")
        return
    # cdb.set_defer_update()
    cdb.start_transaction()
    try:
        if not importer.copy_termination_names_from_games(
            cdb,
            reporter=reporter,
            quit_event=quit_event,
        ):
            cdb.backout()
            return
        if reporter is not None:
            reporter.append_text("Finishing copy: please wait.")
            reporter.append_text_only("")
        # cdb.do_final_segment_deferred_updates()
    except Exception as exc:
        _report_exception(cdb, reporter, exc)
        raise
    # cdb.unset_defer_update()
    cdb.commit()


def do_terminations_deferred_update(
    dbpath, dbclass, pgn_directory, *args, file=None, **kwargs
):
    """Open database, delegate to terminations_du_copy, and close database.

    Argument pgn_directory is supplied but not used in the
    terminations_du_copy() call.

    """
    cdb = _create_database_sysful(dbpath, dbclass)
    cdb.open_database()
    terminations_du_copy(cdb, *args, file=file, **kwargs)
    cdb.close_database()


def player_types_du_copy(
    cdb,
    file=None,
    reporter=None,
    quit_event=None,
    increases=None,
):
    """Import games from files in pgn_directory into open database cdb."""
    importer = playertyperecord.PlayerTypeDBImporter()
    for key in cdb.table.keys():
        if key == file:
            if increases is None:
                counts = [0, 0]
            else:
                counts = [increases[0], increases[1]]
            cdb.increase_database_record_capacity(files={key: counts})
            _du_report_increases(reporter, key, counts)
            break
    else:
        if reporter is not None:
            reporter.append_text_only("")
            reporter.append_text(
                repr(file).join(
                    ("Unable to copy to '", "': not found in database.")
                )
            )
            reporter.append_text_only("")
        return
    # cdb.set_defer_update()
    cdb.start_transaction()
    try:
        if not importer.copy_player_type_names_from_games(
            cdb,
            reporter=reporter,
            quit_event=quit_event,
        ):
            cdb.backout()
            return
        if reporter is not None:
            reporter.append_text("Finishing copy: please wait.")
            reporter.append_text_only("")
        # cdb.do_final_segment_deferred_updates()
    except Exception as exc:
        _report_exception(cdb, reporter, exc)
        raise
    # cdb.unset_defer_update()
    cdb.commit()


def do_player_types_deferred_update(
    dbpath, dbclass, pgn_directory, *args, file=None, **kwargs
):
    """Open database, delegate to player_types_du_copy, and close database.

    Argument pgn_directory is supplied but not used in the
    player_types_du_copy() call.

    """
    cdb = _create_database_sysful(dbpath, dbclass)
    cdb.open_database()
    player_types_du_copy(cdb, *args, file=file, **kwargs)
    cdb.close_database()


def _create_database_sysful(dbpath, dbclass):
    """Return a dbclass database instance for dbpath.

    The dbclass' sysfolder argument is set to  a directory in dbpath
    whose name is defined in the DPT_SYSFUL_FOLDER constant.

    All database engines except DPT ignore the syfolder argument.

    """
    return dbclass(
        dbpath,
        allowcreate=True,
        sysfolder=os.path.join(dbpath, DPT_SYSFUL_FOLDER),
    )


def _du_report_increases(reporter, file, size_increases):
    """Report size increases for file if any and there is a reporter.

    All elements of size_increases will be 0 (zero) if explicit increase
    in file size is not supported, or if not required when it is
    supported.

    """
    if reporter is None:
        return
    if sum(size_increases) == 0:
        return
    reporter.append_text_only("")
    reporter.append_text(file.join(("Increase size of '", "' file.")))
    label = ("Data", "Index")
    for item, size in enumerate(size_increases):
        reporter.append_text_only(
            " ".join(
                (
                    "Applied increase in",
                    label[item],
                    "pages:",
                    str(size),
                )
            )
        )


def _report_exception(cdb, reporter, exception):
    """Write exception to error log file, and reporter if available."""
    errorlog_written = True
    try:
        write_error_to_log(cdb.home_directory)
    except Exception:
        errorlog_written = False
    if reporter is not None:
        reporter.append_text("An exception has occured during import:")
        reporter.append_text_only("")
        reporter.append_text_only(str(exception))
        reporter.append_text_only("")
        if errorlog_written:
            reporter.append_text_only(
                "".join(
                    (
                        "detail appended to ",
                        os.path.join(cdb.home_directory, ERROR_LOG),
                        " file.",
                    )
                )
            )
        else:
            reporter.append_text_only(
                "".join(
                    (
                        "attempt to append detail to ",
                        os.path.join(cdb.home_directory, ERROR_LOG),
                        " file failed.",
                    )
                )
            )
        reporter.append_text_only("")
        reporter.append_text(
            "Import abandonned in way depending on database engine."
        )


def get_filespec(**kargs):
    """Return FileSpec instance with FILEDESCs removed at **kargs request.

    The FILEDESCs are deleted if allowcreate is False, the default.
    """
    names = FileSpec(**kargs)
    if not kargs.get("allowcreate", False):
        for table_name in names:
            if FILEDESC in names[table_name]:
                del names[table_name][FILEDESC]
    return names


class Alldu:
    """Provide deferred update methods shared by all interfaces.

    All the supported engines follow DPT in dividing the numeric primary
    keys into fixed-size segments.  When importing games a large amount of
    memory is required depending on number of games.  Some operating
    systems limit the memory available to a process.  The class attribute
    deferred_update_points is set when the segment size is greater than
    32768 in an attempt to avoid a MemoryError exception.
    """

    # Tag value "" may be given for use as an index value.
    # Symas LMDB is known to not support zero length bytestring keys.
    zero_length_keys_supported = True

    # The optimum chunk size is the segment size.
    # Assuming 2Gb memory:
    # A default FreeBSD user process will not cause a MemoryError exception for
    # segment sizes up to 65536 records, so the optimum chunk size defined in
    # the superclass will be selected.
    # A MS Windows XP process will cause the MemoryError exeption which selects
    # the 32768 game chunk size.
    # A default OpenBSD user process will cause the MemoryError exception which
    # selects the 16384 game chunk size.
    # The error log problem fixed at chesstab-0.41.9 obscured what was actually
    # happening: OpenBSD gives a MemoryError exception but MS Windows XP heads
    # for thrashing swap space in some runs with a 65536 chunk size (depending
    # on order of processing indexes I think). Windows 10 Task Manager display
    # made this obvious.
    # The MemoryError exception or swap space thrashing will likely not occur
    # for a default OpenBSD user process or a MS Windows XP process with
    # segment sizes up to 32768 records. Monitoring with Top and Task Manager
    # suggests it gets close with OpenBSD.

    # pylint comparison-with-callable report is false positive.
    # Perhaps because db_segment_size is a property and the last statement
    # in segmentsize module is 'SegmentSize = SegmentSize()'.
    if SegmentSize.db_segment_size > 32768:
        for f, m in ((4, 700000000), (2, 1400000000)):
            try:
                b" " * m
            except MemoryError:
                # Override the value in the superclass.
                deferred_update_points = frozenset(
                    i
                    for i in range(
                        65536 // f - 1,
                        SegmentSize.db_segment_size,
                        65536 // f,
                    )
                )

                break
        del f, m
