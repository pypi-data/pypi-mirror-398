# task.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Provide Task class which run a method in the current, or a new, thread.

Most supported database engines accept running database methods in a new
thread, but some do not.  The Task class runs a method according to the
value of a class attribute of the Database instance driving the engine.

"""
from multiprocessing import dummy


class Task:
    """Run a method directly or in a new thread, depending on database.

    database is an instance of the Database class for the database engine.
    target is the method to run.
    args is a tuple of the target method's arguments.
    join_loop is the method which will wait for the target method to finish.

    database is often, but not necessarely, in args.

    """

    def __init__(self, database, target, args, join_loop):
        """Set method and arguments."""
        self._target = target
        self._args = args
        self._join_loop = join_loop
        self._run_thread = database.__class__.can_use_thread

    def start_and_join(self):
        """Run self._target in new thread if self._run_thread is True."""
        if not self._run_thread:
            self._target(*self._args)
            return
        thread = dummy.DummyProcess(target=self._target, args=self._args)
        thread.start()
        self._join_loop(thread)
