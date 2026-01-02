# calculate.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""This module provides functions to calculate player performances."""

import copy

from . import eventrecord
from . import gamerecord
from . import moderecord
from . import playerrecord
from . import timecontrolrecord
from . import filespec
from . import utilities
from . import population
from . import person


def calculate(
    database,
    rule,
    player_identity,
    from_date,
    to_date,
    time_control_identity,
    mode_identity,
    event_list,
):
    """Calculate player performances from games on database.

    Return True if performances calculated and False otherwise.

    """
    if not database:
        return None
    if not rule:
        return None
    if (player_identity and event_list) or (
        not player_identity and not event_list
    ):
        return None
    if (from_date and not to_date) or (not from_date and to_date):
        return None
    appsysdate = utilities.AppSysDate()
    if from_date:
        if appsysdate.parse_date(from_date) != len(from_date):
            return None
        from_date = appsysdate.iso_format_date().replace("-", ".")
    if to_date:
        if appsysdate.parse_date(to_date) != len(to_date):
            return None
        to_date = appsysdate.iso_format_date().replace("-", ".")
    del appsysdate
    calculation = Calculate(
        database,
        rule,
        player_identity,
        from_date,
        to_date,
        time_control_identity,
        mode_identity,
        event_list,
    )
    database.start_transaction()
    try:
        date_games = calculation.get_games_in_date_range()
        time_control_games = calculation.get_games_for_time_control()
        mode_games = calculation.get_games_for_mode()
        event_games = calculation.get_games_for_events()
        calculation.set_selected_games(
            date_games & time_control_games & mode_games & event_games
        )
        date_games.close()
        time_control_games.close()
        mode_games.close()
        event_games.close()
        if calculation.deduce_player_population:
            calculation.set_player_population_from_selected_player()
        else:
            calculation.set_players_from_selected_games()
            calculation.set_player_populations_from_selected_games()
        calculation.check_convergent_calculation_possible()
        for convergent, playerset in zip(
            calculation.convergent, calculation.playersets
        ):
            player_population = population.Population(
                database, playerset, calculation.selected_games
            )
            if convergent:
                calculation.populations.append(player_population)
            elif _all_cycle_patches_are_equivalent(player_population):
                calculation.non_convergent_populations.append(
                    player_population
                )
            else:
                calculation.non_calculable_populations.append(
                    player_population
                )
        calculation.playersets.clear()
        for player_population in calculation.populations:
            player_population.do_iterations_until_stable()
            player_population.set_high_performance()
        for player_population in calculation.non_convergent_populations:
            arbitrary_player = next(iter(player_population.persons.values()))
            apply_cycle_patch_for_calculation(
                player_population, arbitrary_player
            )
            player_population.do_iterations_until_stable()
            player_population.set_high_performance()
            remove_cycle_patch_for_calculation(
                player_population, arbitrary_player
            )
    except CalculateError:
        database.backout()
        return None
    except:  # pycodestyle E722: pylint is happy with following 'raise'.
        database.backout()
        raise
    database.commit()
    return calculation


class CalculateError(Exception):
    """Raise exception when player performances cannot be calculated.

    The expected action for this exception is transaction backout.
    """


class Calculate:
    """Collate players and calculate performances from games on database."""

    def __init__(
        self,
        database,
        rule,
        player_identity,
        from_date,
        to_date,
        time_control_identity,
        mode_identity,
        event_list,
    ):
        """Set initial state."""
        self._database = database
        self._rule = rule
        self._player_identity = player_identity
        self._from_date = from_date
        self._to_date = to_date
        self._time_control_identity = time_control_identity
        self._mode_identity = mode_identity
        self._event_list = event_list
        self.selected_games = None
        self.selected_players = None
        self.playersets = []
        self.convergent = []
        self.populations = []
        self.non_convergent_populations = []
        self.non_calculable_populations = []

    def __del__(self):
        """Tidy up on deletion of object."""
        if self.selected_games is not None:
            self.selected_games.close()
            self.selected_games = None
        if self.selected_players is not None:
            self.selected_players.close()
            self.selected_players = None

    @property
    def deduce_player_population(self):
        """Return True if playerset expands to include opponents.

        Return True if a known player identity is in the calculation rule.

        Return False if event identities are in the calculation rule.

        """
        assert bool(self._player_identity) != bool(self._event_list)
        return bool(self._player_identity)

    def get_games_in_date_range(self):
        """Return recordset of games dated between from and to dates.

        Dates are in self._from_date and self._to_date.  Both are present
        or both are absent, where absence means all games.  Games dated on
        the two dates are included in the range.

        """
        if self._from_date or self._to_date:
            return self._database.recordlist_key_range(
                filespec.GAME_FILE_DEF,
                filespec.GAME_DATE_FIELD_DEF,
                ge=self._database.encode_record_selector(self._from_date),
                le=self._database.encode_record_selector(self._to_date),
            )
        return self._database.recordlist_ebm(filespec.GAME_FILE_DEF)

    def get_games_for_time_control(self):
        """Return recordset of games played at a time control.

        The recordset contains all games if no tim contros are specified
        in the calculation rule.

        The time controls will likely be used to distinguish ranges of
        rates of play: such as standard, rapidplay, and blitz.

        """
        return _get_games_for_identity(
            self._database,
            self._time_control_identity,
            filespec.TIME_FILE_DEF,
            filespec.TIME_IDENTITY_FIELD_DEF,
            timecontrolrecord.TimeControlDBrecord,
            filespec.GAME_TIMECONTROL_FIELD_DEF,
        )

    def get_games_for_mode(self):
        """Return recordset of games played in a mode.

        The recordset contains all games if no modes are specified in the
        calculation rule.

        The modes will likely be used to distinguish playing conditions:
        such as over-the-board, online, and crrrespondence.

        """
        return _get_games_for_identity(
            self._database,
            self._mode_identity,
            filespec.MODE_FILE_DEF,
            filespec.MODE_IDENTITY_FIELD_DEF,
            moderecord.ModeDBrecord,
            filespec.GAME_MODE_FIELD_DEF,
        )

    def get_games_for_events(self):
        """Return recordset of games played in events.

        The recordset contains all games if no events are specified in the
        calculation rule.

        Each event may have a number of alternative names.

        """
        games = self._database.recordlist_nil(filespec.GAME_FILE_DEF)
        if not self._event_list:
            return self._database.recordlist_ebm(filespec.GAME_FILE_DEF)
        for identity in self._event_list:
            event_games = _get_games_for_identity(
                self._database,
                identity,
                filespec.EVENT_FILE_DEF,
                filespec.EVENT_IDENTITY_FIELD_DEF,
                eventrecord.EventDBrecord,
                filespec.GAME_EVENT_FIELD_DEF,
            )
            games |= event_games
            event_games.close()
        return games

    def set_selected_games(self, selected_games):
        """Bind self.selected_games to selected_games.

        Usually selected_games will be the __and__ of games found for a
        date range, time control, mode, and list of events.

        """
        self.selected_games = selected_games

    def set_players_from_selected_games(self):
        """Bind self.selected_players to players in self.selected_games."""
        database = self._database
        person_list = database.recordlist_nil(filespec.PLAYER_FILE_DEF)
        game = gamerecord.GameDBrecord()
        player = playerrecord.PlayerDBrecord()
        cursor = self.selected_games.create_recordsetbase_cursor()
        while True:
            record = cursor.next()
            if record is None:
                break
            game.load_record(record)
            for key in game.value.black_key(), game.value.white_key():
                player_list = database.recordlist_key(
                    filespec.PLAYER_FILE_DEF,
                    filespec.PERSON_ALIAS_FIELD_DEF,
                    key=database.encode_record_selector(key),
                )
                player_cursor = player_list.create_recordsetbase_cursor()
                try:
                    record = player_cursor.first()
                    if record is None:
                        continue
                    player.load_record(record)
                    if player.value.identity != player.value.alias:
                        alias_list = database.recordlist_key(
                            filespec.PLAYER_FILE_DEF,
                            filespec.PLAYER_KNOWN_FIELD_DEF,
                            key=database.encode_record_selector(
                                player.value.alias
                            ),
                        )
                        record = (
                            alias_list.create_recordsetbase_cursor().first()
                        )
                        if record is None:
                            continue
                        player.load_record(record)
                    person_list.place_record_number(player.key.pack())
                finally:
                    player_cursor.close()
        self.selected_players = person_list

    def set_player_populations_from_selected_games(self):
        """Bind self.player_populations to list of sets of connected players.

        Each set is a connected graph with nodes representing players and
        edges representing one or more games between two players.

        Just self.selected_players and self.selected_games are considered
        if these players and games produce a single connected graph.

        A single connected graph is guaranteed if the players and games
        were selected by specifying a player.

        More than one connected graph is possible if the players and games
        were selected by specifying a list of events.  The following steps
        are done in an attempt to combine these into a single connected
        graph.

        Games between players in self.selected_players which are not in
        self.selected_games are considered when more than one connected
        graph was generated without them.  These additional games must have
        been played the dates of the earliest and latest games in
        self.selected_games.

        Just these additional games are considered if a single connected
        graph is produced.

        Games between additional players and those in self.selected_players
        are considered for each additional provided that additional player
        plays games against players in more than one of the connected
        graphs.

        If the games from these additional players do not allow production
        of a single connected graph the existence of several playersets of
        players is accepted.

        """
        database = self._database
        encode_record_selector = database.encode_record_selector
        recordlist_key = database.recordlist_key
        recordlist_nil = database.recordlist_nil
        if self.selected_games is None and self.selected_players is None:
            self.playersets = None
            return
        selected_games = self.selected_games
        person_record = playerrecord.PlayerDBrecord()
        game_record = gamerecord.GameDBrecord()
        person_cursor = self.selected_players.create_recordsetbase_cursor()
        while True:
            record = person_cursor.next()
            if record is None:
                break
            person_record.load_record(record)
            person_connected = recordlist_nil(filespec.PLAYER_FILE_DEF)
            person_connected.place_record_number(person_record.key.pack())
            alias_index_key = person_record.value.alias_index_key()
            person_games = recordlist_key(
                filespec.GAME_FILE_DEF,
                filespec.GAME_PERSON_FIELD_DEF,
                key=encode_record_selector(person_record.value.identity),
            )
            person_games &= selected_games
            game_cursor = person_games.create_recordsetbase_cursor()
            while True:
                record = game_cursor.next()
                if record is None:
                    break
                game_record.load_record(record)
                for game_player in (
                    game_record.value.black_key(),
                    game_record.value.white_key(),
                ):
                    if game_player == alias_index_key:
                        continue
                    person_opponent = recordlist_key(
                        filespec.PLAYER_FILE_DEF,
                        filespec.PERSON_ALIAS_FIELD_DEF,
                        key=encode_record_selector(game_player),
                    )
                    opponent_cursor = (
                        person_opponent.create_recordsetbase_cursor()
                    )
                    record = opponent_cursor.first()
                    if record is None:
                        continue
                    person_record.load_record(record)
                    if (
                        person_record.value.alias
                        != person_record.value.identity
                    ):
                        person_opponent.close()
                        person_opponent = recordlist_key(
                            filespec.PLAYER_FILE_DEF,
                            filespec.PLAYER_KNOWN_FIELD_DEF,
                            key=encode_record_selector(
                                person_record.value.alias
                            ),
                        )
                    person_connected |= person_opponent
                    person_opponent.close()
            self.add_player_and_opponents_to_population(person_connected)
            person_connected.close()
            person_games.close()

    def set_player_population_from_selected_player(self):
        """Bind self.player_populations to list of sets of connected players.

        The list will contain one set representing the connected graph with
        nodes representing players and edges representing one or more games
        between two players.

        The set in the list is derived by including all the opponents of a
        player in the games in self.selected_games recursively.

        """
        selected_games = self.selected_games
        person_record = playerrecord.PlayerDBrecord()
        game_record = gamerecord.GameDBrecord()
        database = self._database
        encode_record_selector = database.encode_record_selector
        recordlist_key = database.recordlist_key
        recordlist_nil = database.recordlist_nil
        person_list = recordlist_key(
            filespec.PLAYER_FILE_DEF,
            filespec.PLAYER_LINKS_FIELD_DEF,
            key=encode_record_selector(self._player_identity),
        )
        cursor = person_list.create_recordsetbase_cursor()
        person_record.load_record(cursor.first())

        # Create list again based on alias, which is sometimes same as
        # identity, to fit loop that builds the playerset.
        cursor.close()
        person_list = recordlist_key(
            filespec.PLAYER_FILE_DEF,
            filespec.PLAYER_LINKS_FIELD_DEF,
            key=encode_record_selector(person_record.value.alias),
        )

        playerset = recordlist_nil(filespec.PLAYER_FILE_DEF)
        while True:
            if not person_list.count_records():
                break
            playerset |= person_list
            person_connected = recordlist_nil(filespec.PLAYER_FILE_DEF)
            person_cursor = person_list.create_recordsetbase_cursor()
            while True:
                record = person_cursor.next()
                if record is None:
                    break
                person_record.load_record(record)
                alias_index_key = person_record.value.alias_index_key()
                person_games = recordlist_key(
                    filespec.GAME_FILE_DEF,
                    filespec.GAME_PERSON_FIELD_DEF,
                    key=encode_record_selector(person_record.value.identity),
                )
                person_games &= selected_games
                game_cursor = person_games.create_recordsetbase_cursor()
                while True:
                    record = game_cursor.next()
                    if record is None:
                        break
                    game_record.load_record(record)
                    for game_player in (
                        game_record.value.black_key(),
                        game_record.value.white_key(),
                    ):
                        if game_player == alias_index_key:
                            continue
                        person_opponent = recordlist_key(
                            filespec.PLAYER_FILE_DEF,
                            filespec.PERSON_ALIAS_FIELD_DEF,
                            key=encode_record_selector(game_player),
                        )
                        opponent_cursor = (
                            person_opponent.create_recordsetbase_cursor()
                        )
                        record = opponent_cursor.first()
                        if record is None:
                            continue
                        person_record.load_record(record)
                        if (
                            person_record.value.alias
                            != person_record.value.identity
                        ):
                            person_opponent.close()
                            person_opponent = recordlist_key(
                                filespec.PLAYER_FILE_DEF,
                                filespec.PLAYER_KNOWN_FIELD_DEF,
                                key=encode_record_selector(
                                    person_record.value.alias
                                ),
                            )
                        person_connected |= person_opponent
                        person_opponent.close()
            person_cursor.close()
            person_list = recordlist_nil(filespec.PLAYER_FILE_DEF)
            person_list |= person_connected
            person_list.remove_recordset(playerset)
            person_connected.close()
        self.playersets = [playerset]
        self.selected_players = self._database.recordlist_nil(
            filespec.PLAYER_FILE_DEF
        )
        self.selected_players |= playerset

    def add_player_and_opponents_to_population(self, player_and_opponents):
        """Merge player_and_opponents into self.playersets.

        The player_and_opponents recordlist is expected to contain one
        player and some, usually all, of the player's opponenents.

        This recordlist thus represents a connected graph with one central
        node and edges to the other nodes.

        It is assumed this method will be called for all selected players,
        but the result may not be a single connected graph with all
        selected players as nodes.  Other methods may be able to extend
        the games considered to achieve this goal.

        """
        merged = []
        not_merged = []
        playersets = self.playersets
        while playersets:
            playerset = playersets.pop()
            if (playerset & player_and_opponents).count_records():
                playerset |= player_and_opponents
                merged.append(playerset)
            else:
                not_merged.append(playerset)
        if merged:
            playerset = merged.pop()
            while merged:
                playerset |= merged.pop()
            playersets.append(playerset)
        else:
            clone = self._database.recordlist_nil(filespec.PLAYER_FILE_DEF)
            clone |= player_and_opponents
            not_merged.append(clone)
        playersets.extend(not_merged)
        if not playersets:
            playersets.append(
                self._database.recordlist_nil(filespec.PLAYER_FILE_DEF)
            )
            playersets[0] |= player_and_opponents

    def check_convergent_calculation_possible(self):
        """Note state of playersets for performance calculation.

        Each playerset is assumed to be a connected graph.

        It is assumed the iteration on each playerset will cause each
        player's performance number to converge on some value which is a
        function of the player's results if and only if at least one set
        of games, represented by edges in the graph, exist such that three
        players play each other at least once  (games A-B, B-C, and C-A,
        being sufficient).

        This author is not aware of a proof, but modelling suggests the
        condition is sound.  Games A-B, B-C, C-D, and D-A, do not give a
        calculation which converges on a single value for each player;
        and neither does a connected graph which is a tree.

        It seems the non-convergent calcuations are stable, with each
        player's performance number orbiting around two values with a
        decreasing gap to the values.

        """
        selected_games = self.selected_games
        person_record = playerrecord.PlayerDBrecord()
        game_record = gamerecord.GameDBrecord()
        database = self._database
        encode_record_selector = database.encode_record_selector
        recordlist_key = database.recordlist_key
        recordlist_nil = database.recordlist_nil
        helpers = (
            person_record,
            game_record,
            recordlist_key,
            encode_record_selector,
        )
        for playerset in self.playersets:
            convergent = False
            person_cursor = playerset.create_recordsetbase_cursor()
            while True:
                if convergent:
                    break
                person_opponents = recordlist_nil(filespec.PLAYER_FILE_DEF)
                record = person_cursor.next()
                if record is None:
                    break
                person_record.load_record(record)
                alias_index_key = person_record.value.alias_index_key()
                person_alias = person_record.value.alias
                person_games = (
                    database.recordlist_key(
                        filespec.GAME_FILE_DEF,
                        filespec.GAME_PERSON_FIELD_DEF,
                        key=encode_record_selector(person_record.value.alias),
                    )
                    & selected_games
                )
                _add_opponents_of_person_in_games_to_players(
                    person_opponents,
                    person_games,
                    alias_index_key,
                    person_alias,
                    helpers,
                )
                opponent_cursor = (
                    person_opponents.create_recordsetbase_cursor()
                )
                while True:
                    if convergent:
                        break
                    opponent_opponents = recordlist_nil(
                        filespec.PLAYER_FILE_DEF
                    )
                    record = opponent_cursor.next()
                    if record is None:
                        break
                    person_record.load_record(record)
                    alias_index_key = person_record.value.alias_index_key()
                    person_alias = person_record.value.alias
                    opponent_games = (
                        database.recordlist_key(
                            filespec.GAME_FILE_DEF,
                            filespec.GAME_PERSON_FIELD_DEF,
                            key=encode_record_selector(
                                person_record.value.alias
                            ),
                        )
                        & selected_games
                    )
                    _add_opponents_of_person_in_games_to_players(
                        opponent_opponents,
                        opponent_games,
                        alias_index_key,
                        person_alias,
                        helpers,
                    )
                    if (person_opponents & opponent_opponents).count_records():
                        convergent = True
                        break
            self.convergent.append(convergent)


def _add_opponents_of_person_in_games_to_players(
    players, games, person_index_key, person_alias, helpers
):
    """Add opponents of person in games to players."""
    (
        person_record,
        game_record,
        recordlist_key,
        encode_record_selector,
    ) = helpers
    cursor = games.create_recordsetbase_cursor()
    while True:
        record = cursor.next()
        if record is None:
            break
        game_record.load_record(record)
        for game_player in (
            game_record.value.black_key(),
            game_record.value.white_key(),
        ):
            if game_player == person_index_key:
                continue
            game_opponent = recordlist_key(
                filespec.PLAYER_FILE_DEF,
                filespec.PERSON_ALIAS_FIELD_DEF,
                key=encode_record_selector(game_player),
            )
            game_opponent_cursor = game_opponent.create_recordsetbase_cursor()
            record = game_opponent_cursor.first()
            if record is None:
                continue
            person_record.load_record(record)
            if person_record.value.alias == person_alias:
                continue
            game_opponent = recordlist_key(
                filespec.PLAYER_FILE_DEF,
                filespec.PLAYER_KNOWN_FIELD_DEF,
                key=encode_record_selector(person_record.value.alias),
            )
            players |= game_opponent


def _get_games_for_identity(
    database,
    identity,
    file,
    alias_field,
    recordclass,
    game_field,
):
    """Return recordset of games played filtered by identity.

    The recordset contains all games if bool(identity) evaluates False.

    """
    if not identity:
        return database.recordlist_ebm(filespec.GAME_FILE_DEF)
    recordlist = database.recordlist_key(
        file,
        alias_field,
        key=database.encode_record_selector(identity),
    )
    cursor = recordlist.create_recordsetbase_cursor()
    games = database.recordlist_nil(filespec.GAME_FILE_DEF)
    try:
        while True:
            record = cursor.next()
            if not record:
                break
            item_record = recordclass()
            item_record.load_record(
                database.get_primary_record(file, record[0])
            )
            item_games = database.recordlist_key(
                filespec.GAME_FILE_DEF,
                game_field,
                key=database.encode_record_selector(
                    item_record.value.alias_index_key()
                ),
            )
            games |= item_games
            item_games.close()
    finally:
        cursor.close()
    return games


def _all_cycle_patches_are_equivalent(player_population):
    """Return True if cycle patch to each node gives equivalent answer.

    The cycle patch assumes a set of three drawn games between imaginary
    players: 'a-b', 'b-c', and 'c-a'.  The patch is applied to each node
    in player_population in turn by a single drawn game 'node-a' and the
    performances are calculated.

    The calculations are equivalent if the normalized performances of the
    non-imaginary players are the same in all calculations, and the
    normalized performances of the imaginary players are the same as the
    normalized performance of the node in the game 'node-a' in each
    calculation.

    This author is not aware of a proof that True will be returned in
    all cases.  The existence of such a proof would make this method
    redundant.

    """
    cycle = []
    for player in player_population.persons.values():
        cycle_population = copy.deepcopy(player_population, {})
        apply_cycle_patch_for_calculation(cycle_population, player)
        cycle_population.do_iterations_until_stable()
        cycle_population.set_high_performance()
        high = cycle_population.high_performance
        normal = {
            alias.code: alias.normal_performance(high)
            for alias in cycle_population.persons.values()
        }
        if not normal["a"] == normal["b"] == normal["c"]:
            return False
        if normal["a"] != normal[player.code]:
            return False
        del normal["a"]
        del normal["b"]
        del normal["c"]
        cycle.append(normal)
    if not cycle:
        return False
    base = cycle.pop()
    while cycle:
        item = cycle.pop()
        if base != item:
            return False
    return True


def apply_cycle_patch_for_calculation(player_population, player):
    """Apply cycle patch to player in player_population.

    The cycle patch assumes a set of three drawn games between imaginary
    players: 'a-b', 'b-c', and 'c-a'.  The patch is applied to player in
    player_population by a single drawn game 'player-a'.

    This author is not aware of a proof the calculation will converge in
    all cases, but no contrary case has yet been seen.  Converge means
    each player performance number orbits a single limit, rather than
    two limits without the patch, and the orbit never expands.

    """
    persons = player_population.persons
    persons["a"] = person.Person("a", "")
    persons["a"].score = 1.5
    persons["a"].opponents = ["b", "c", player.code]
    persons["b"] = person.Person("b", "")
    persons["b"].score = 1
    persons["b"].opponents = ["c", "a"]
    persons["c"] = person.Person("c", "")
    persons["c"].score = 1
    persons["c"].opponents = ["a", "b"]
    persons[player.code].opponents.append("a")
    persons[player.code].score += 0.5


def remove_cycle_patch_for_calculation(player_population, player):
    """Remove cycle patch to player in player_population.

    Do nothing if the patch is not present.

    """
    persons = player_population.persons
    for code in "abc":
        if code in persons:
            del persons[code]
    if player.code in persons:
        if "a" in persons[player.code].opponents:
            persons[player.code].score -= 0.5
            persons[player.code].opponents.remove("a")
