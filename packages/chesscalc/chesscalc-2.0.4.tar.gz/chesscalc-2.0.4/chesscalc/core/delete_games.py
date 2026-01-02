# delete_games.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions to delete games on database.

The functions support deleting games for a PGN file or selected games from
a PGN file.

"""
from . import filespec
from . import constants
from . import identify_item
from . import gamerecord
from . import playerrecord
from . import moderecord
from . import playertyperecord
from . import terminationrecord
from . import timecontrolrecord


def delete_selected_file_or_bookmarked_games(
    database, bookmarks, selection, tab, answer
):
    """Delete games from PGN file of selected game or bookmarked games.

    All bookmarked games must be from same PGN file.

    All items derived from any game must be: either aliases of some other
    item, or not have any aliases.

    All players derived from any game must not be on the known person index.

    """
    del answer
    database.start_read_only_transaction()
    try:
        if selection:
            gamelist = _find_games_for_selected_game_pgn_file(
                database, selection, tab
            )
        elif bookmarks:
            gamelist = _find_bookmarked_games(database, bookmarks, tab)
        else:
            tab.append_text("Deleting nothing.")
            return
        if gamelist.count_records() == 0:
            tab.append_text("No games in selection or bookmarks to delete.")
            return
    finally:
        database.end_read_only_transaction()
    database.start_transaction()
    try:
        _adjust_known_player_identities(database, gamelist, tab)
        _adjust_mode_identities(database, gamelist, tab)
        _adjust_player_type_identities(database, gamelist, tab)
        _adjust_termination_identities(database, gamelist, tab)
        _adjust_time_control_identities(database, gamelist, tab)
    except:  # pycodestyle E722: pylint is happy with following 'raise'.
        database.backout()
        raise
    database.commit()
    database.start_transaction()
    try:
        _delete_games(database, gamelist, tab)
    except:  # pycodestyle E722: pylint is happy with following 'raise'.
        database.backout()
        raise
    database.commit()
    if selection:
        tab.append_text("Games from file deleted.")
    else:
        tab.append_text("Selected games deleted.")


def _delete_player(database, tab, value, tag):
    """Delete game from games associated with player on database."""
    if _game_records_exist_for_value(database, _fields[tag], value):
        return
    for field in (
        filespec.PERSON_ALIAS_FIELD_DEF,
        filespec.PLAYER_ALIAS_FIELD_DEF,
    ):
        item = database.recordlist_key(
            filespec.PLAYER_FILE_DEF,
            field,
            key=database.encode_record_selector(value),
        )
        if item.count_records() > 0:
            if field == filespec.PLAYER_NAME_FIELD_DEF:
                person_record = playerrecord.PlayerDBrecord()
            else:
                person_record = playerrecord.PlayerDBrecord(
                    valueclass=playerrecord.PersonDBvalue
                )
            cursor = item.create_recordsetbase_cursor()
            while True:
                record = cursor.next()
                if record is None:
                    break
                person_record.load_record(
                    database.get_primary_record(
                        filespec.PLAYER_FILE_DEF, record[0]
                    )
                )
                person_record.delete_record(database, filespec.PLAYER_FILE_DEF)
            break
    else:
        return
    tab.append_text(value.join(("Player ", " deleted.\n")))


def _delete_black(database, tab, value, tag):
    """Delete game from games associated with black on database."""
    _delete_player(database, tab, value.black_key(), tag)


def _delete_white(database, tab, value, tag):
    """Delete game from games associated with white on database."""
    _delete_player(database, tab, value.white_key(), tag)


def _delete_item(database, tab, file, field, value, recordclass, name, tag):
    """Delete record with field value in file from database."""
    if _game_records_exist_for_value(database, _fields[tag], value):
        return
    item = database.recordlist_key(
        file, field, key=database.encode_record_selector(value)
    )
    item_record = recordclass()
    cursor = item.create_recordsetbase_cursor()
    while True:
        record = cursor.next()
        if record is None:
            break
        item_record.load_record(database.get_primary_record(file, record[0]))
        item_record.delete_record(database, file)
        tab.append_text("".join((name, " ", value, " deleted.\n")))


def _delete_time_control(database, tab, value, tag):
    """Delete time control value from database."""
    _delete_item(
        database,
        tab,
        filespec.TIME_FILE_DEF,
        filespec.TIME_ALIAS_FIELD_DEF,
        value.headers[tag],
        timecontrolrecord.TimeControlDBrecord,
        "Time control",
        tag,
    )


def _delete_mode(database, tab, value, tag):
    """Delete mode value from database."""
    _delete_item(
        database,
        tab,
        filespec.MODE_FILE_DEF,
        filespec.MODE_ALIAS_FIELD_DEF,
        value.headers[tag],
        moderecord.ModeDBrecord,
        "Mode",
        tag,
    )


def _delete_termination(database, tab, value, tag):
    """Delete termination value from database."""
    _delete_item(
        database,
        tab,
        filespec.TERMINATION_FILE_DEF,
        filespec.TERMINATION_ALIAS_FIELD_DEF,
        value.headers[tag],
        terminationrecord.TerminationDBrecord,
        "Termination",
        tag,
    )


def _delete_player_type(database, tab, value, tag):
    """Delete player type value from database."""
    _delete_item(
        database,
        tab,
        filespec.PLAYERTYPE_FILE_DEF,
        filespec.PLAYERTYPE_ALIAS_FIELD_DEF,
        value.headers[tag],
        playertyperecord.PlayerTypeDBrecord,
        "Player type",
        tag,
    )


def _game_records_exist_for_value(database, field, value):
    """Delete game from games associated with player type on database."""
    return bool(
        database.recordlist_key(
            filespec.GAME_FILE_DEF,
            field,
            key=database.encode_record_selector(value),
        ).count_records()
    )


_tags = {
    constants.TAG_BLACK: _delete_black,
    constants.TAG_WHITE: _delete_white,
    constants.TAG_TIMECONTROL: _delete_time_control,
    constants.TAG_MODE: _delete_mode,
    constants.TAG_TERMINATION: _delete_termination,
    constants.TAG_BLACKTYPE: _delete_player_type,
    constants.TAG_WHITETYPE: _delete_player_type,
}

_fields = {
    constants.TAG_BLACK: filespec.GAME_PLAYER_FIELD_DEF,
    constants.TAG_WHITE: filespec.GAME_PLAYER_FIELD_DEF,
    constants.TAG_TIMECONTROL: filespec.GAME_TIMECONTROL_FIELD_DEF,
    constants.TAG_MODE: filespec.GAME_MODE_FIELD_DEF,
    constants.TAG_TERMINATION: filespec.GAME_TERMINATION_FIELD_DEF,
    constants.TAG_BLACKTYPE: filespec.GAME_PLAYERTYPE_FIELD_DEF,
    constants.TAG_WHITETYPE: filespec.GAME_PLAYERTYPE_FIELD_DEF,
}


def _delete_games(database, gamelist, tab):
    """Delete games in gamelist from database."""
    game_record = gamerecord.GameDBrecord()
    game_value = game_record.value
    cursor = gamelist.create_recordsetbase_cursor()
    while True:
        record = cursor.next()
        if record is None:
            break
        record = database.get_primary_record(filespec.GAME_FILE_DEF, record[0])
        game_record.load_record(record)
        game_record.delete_record(database, filespec.GAME_FILE_DEF)
        tab.append_text(
            repr(game_value.reference).join(("Game ", " deleted.\n"))
        )
        headers = game_value.headers
        for tag, function in _tags.items():
            tag_value = headers.get(tag)
            if tag_value is None:
                continue
            function(database, tab, game_value, tag)


def _known_players_for_games(database, gamelist, tab):
    """Return known players in games in gamelist on database."""
    tab.append_text("Finding games which involve a known player.\n")
    games = (
        database.recordlist_all(
            filespec.GAME_FILE_DEF, filespec.GAME_PERSON_FIELD_DEF
        )
        & gamelist
    )
    games_count = games.count_records()
    if games_count == 0:
        tab.append_text("No games for deletion refer to known players.\n")
        return games
    tab.append_text(
        str(gamelist.count_records() - games_count)
        + " games for deletion do not refer to known players.\n",
    )
    tab.append_text(
        str(games_count) + " games for deletion refer to known players.\n",
    )
    tab.append_text("Finding known players to convert to new players.\n")
    found_players = set()
    persons_in_games = database.recordlist_nil(filespec.PLAYER_FILE_DEF)
    game_record = gamerecord.GameDBrecord()
    game_value = game_record.value
    cursor = games.create_recordsetbase_cursor()
    while True:
        record = cursor.next()
        if record is None:
            break
        record = database.get_primary_record(filespec.GAME_FILE_DEF, record[0])
        game_record.load_record(record)
        for player in (game_value.white_key(), game_value.black_key()):
            if player in found_players:
                continue
            persons_in_games |= database.recordlist_key(
                filespec.PLAYER_FILE_DEF,
                filespec.PERSON_ALIAS_FIELD_DEF,
                key=player,
            )
            found_players.add(player)
    return persons_in_games


def _adjust_known_player_identities(database, gamelist, tab):
    """Adjust player identities to be not associated with games for deletion.

    Not always possible, but if done where it is, the player identities and
    aliases associated with just the games to be deleted can be deleted too.

    """
    known_players = _known_players_for_games(database, gamelist, tab)
    person_record = playerrecord.PlayerDBrecord(
        valueclass=playerrecord.PersonDBvalue
    )
    person_value = person_record.value
    encode_record_selector = database.encode_record_selector
    cursor = known_players.create_recordsetbase_cursor()
    while True:
        record = cursor.next()
        if record is None:
            break
        person_record.load_record(
            database.get_primary_record(filespec.PLAYER_FILE_DEF, record[0])
        )
        old_identity = person_value.identity
        links = database.recordlist_key(
            filespec.PLAYER_FILE_DEF,
            filespec.PLAYER_LINKS_FIELD_DEF,
            key=encode_record_selector(old_identity),
        )
        other_links = database.recordlist_nil(filespec.PLAYER_FILE_DEF)
        other_links |= links
        other_links.remove_recordset(known_players)
        other_links_cursor = other_links.create_recordsetbase_cursor()
        other_record = other_links_cursor.next()
        if other_record:
            _adjust_known_player_identity(
                database, links, other_record, old_identity
            )
            tab.append_text(
                person_value.alias_index_key().join(
                    ("Adjust identity ", ".\n")
                )
            )


def _adjust_known_player_identity(database, links, other_record, old_identity):
    """Adjust player identity to be not associated with games for deletion.

    Not always possible, but if done where it is, the player identities and
    aliases associated with just the games to be deleted can be deleted too.

    """
    person_record = playerrecord.PlayerDBrecord(
        valueclass=playerrecord.PersonDBvalue
    )
    person_value = person_record.value
    edited_person_record = playerrecord.PlayerDBrecord(
        valueclass=playerrecord.PersonDBvalue
    )
    edited_person_value = edited_person_record.value
    encode_record_selector = database.encode_record_selector
    person_record.load_record(
        database.get_primary_record(filespec.PLAYER_FILE_DEF, other_record[0])
    )
    new_identity = person_value.identity
    gamelist = database.recordlist_key(
        filespec.GAME_FILE_DEF,
        filespec.GAME_PERSON_FIELD_DEF,
        key=encode_record_selector(old_identity),
    )
    links_cursor = links.create_recordsetbase_cursor()
    while True:
        links_record = links_cursor.next()
        if links_record is None:
            break
        links_record = database.get_primary_record(
            filespec.PLAYER_FILE_DEF, links_record[0]
        )
        person_record.load_record(links_record)
        edited_person_record.load_record(links_record)
        edited_person_value.alias = new_identity
        person_record.edit_record(
            database, filespec.PLAYER_FILE_DEF, None, edited_person_record
        )
    database.unfile_records_under(
        filespec.GAME_FILE_DEF,
        filespec.GAME_PERSON_FIELD_DEF,
        encode_record_selector(old_identity),
    )
    database.file_records_under(
        filespec.GAME_FILE_DEF,
        filespec.GAME_PERSON_FIELD_DEF,
        gamelist,
        encode_record_selector(new_identity),
    )


def _find_games_for_selected_game_pgn_file(database, selection, tab):
    """Return database records referenced via selection and report to tab."""
    tab.append_text("Attempting to delete all games for a PGN file.\n")
    primary_record = identify_item.get_first_item_on_recordlist(
        database,
        database.recordlist_record_number(
            filespec.GAME_FILE_DEF, key=selection[0][1]
        ),
        filespec.GAME_FILE_DEF,
    )
    if primary_record is None:
        tab.append_text("Record for selection not found.")
        return database.recordlist_nil(filespec.GAME_FILE_DEF)
    game_record = gamerecord.GameDBrecord()
    game_record.load_record(primary_record)
    filename = game_record.value.reference[constants.FILE]
    recordlist = database.recordlist_key(
        filespec.GAME_FILE_DEF,
        filespec.GAME_PGNFILE_FIELD_DEF,
        key=database.encode_record_selector(filename),
    )
    tab.append_text(
        "".join(
            (
                "Attempting to delete ",
                str(recordlist.count_records()),
                " games imported from '",
                filename,
                "'.\n",
            )
        )
    )
    return recordlist


def _find_bookmarked_games(database, bookmarks, tab):
    """Return database records referenced by bookmarks and report to tab."""
    tab.append_text(
        "".join(
            (
                "Attempting to delete ",
                str(len(bookmarks)),
                " bookmarked games.\n",
            )
        )
    )
    recordlist = database.recordlist_nil(filespec.GAME_FILE_DEF)
    filename_record_counts = {}
    game_record = gamerecord.GameDBrecord()
    for bookmark in bookmarks:
        gamerecordlist = database.recordlist_record_number(
            filespec.GAME_FILE_DEF, key=bookmark[1]
        )
        primary_record = identify_item.get_first_item_on_recordlist(
            database, gamerecordlist, filespec.GAME_FILE_DEF
        )
        if primary_record is None:
            tab.append_text("Record for one of bookmarks not found.")
            return recordlist
        game_record.load_record(primary_record)
        filename = game_record.value.reference[constants.FILE]
        if filename not in filename_record_counts:
            filename_record_counts[filename] = 1
        else:
            filename_record_counts[filename] += 1
        recordlist |= gamerecordlist
    for filename, count in filename_record_counts.items():
        tab.append_text(
            "".join(
                (
                    "Attempting to delete ",
                    str(count),
                    " games imported from '",
                    filename,
                    "'.\n",
                )
            )
        )
    return recordlist


def _modes_for_games(database, gamelist, tab):
    """Return modes in games in gamelist on database."""
    return _items_for_games(
        database,
        gamelist,
        tab,
        filespec.GAME_MODE_FIELD_DEF,
        filespec.MODE_FILE_DEF,
        moderecord.ModeDBrecord,
        "mode",
        (constants.TAG_MODE,),
    )


def _player_types_for_games(database, gamelist, tab):
    """Return player types in games in gamelist on database."""
    return _items_for_games(
        database,
        gamelist,
        tab,
        filespec.GAME_PLAYERTYPE_FIELD_DEF,
        filespec.PLAYERTYPE_FILE_DEF,
        playertyperecord.PlayerTypeDBrecord,
        "player type",
        (
            constants.TAG_BLACKTYPE,
            constants.TAG_WHITETYPE,
        ),
    )


def _terminations_for_games(database, gamelist, tab):
    """Return terminations in games in gamelist on database."""
    return _items_for_games(
        database,
        gamelist,
        tab,
        filespec.GAME_TERMINATION_FIELD_DEF,
        filespec.TERMINATION_FILE_DEF,
        terminationrecord.TerminationDBrecord,
        "termination",
        (constants.TAG_TERMINATION,),
    )


def _time_controls_for_games(database, gamelist, tab):
    """Return time controls in games in gamelist on database."""
    return _items_for_games(
        database,
        gamelist,
        tab,
        filespec.GAME_TIMECONTROL_FIELD_DEF,
        filespec.TIME_FILE_DEF,
        timecontrolrecord.TimeControlDBrecord,
        "time control",
        (constants.TAG_TIMECONTROL,),
    )


def _items_for_games(
    database, gamelist, tab, gamefield, file, recordclass, name, tags
):
    """Return items in games in gamelist on database."""
    tab.append_text(
        "".join(
            (
                "Finding games which declare ",
                name,
                " explicitly.\n",
            )
        )
    )
    games = (
        database.recordlist_all(filespec.GAME_FILE_DEF, gamefield) & gamelist
    )
    games_count = games.count_records()
    if games_count == 0:
        tab.append_text(
            "".join(
                (
                    "No games for deletion refer to explicit ",
                    name,
                    "s.\n",
                )
            )
        )
        return games
    tab.append_text(
        "".join(
            (
                str(gamelist.count_records() - games_count),
                " games for deletion do not refer to explicit ",
                name,
                "s.\n",
            )
        )
    )
    tab.append_text(
        "".join(
            (
                str(games_count),
                " games for deletion refer to explicit ",
                name,
                "s.\n",
            )
        )
    )
    tab.append_text(name.join(("Finding ", "s whose identity must change.\n")))
    taglist = database.recordlist_ebm(file)
    found_items = set()
    items_in_games = database.recordlist_nil(file)
    item_record = recordclass()
    cursor = games.create_recordsetbase_cursor()
    game_record = gamerecord.GameDBrecord()
    while True:
        record = cursor.next()
        if record is None:
            break
        game_record.load_record(record)
        for tag in tags:
            tagvalue = game_record.value.headers.get(tag)
            if tagvalue is None:
                continue
            tag_cursor = taglist.create_recordsetbase_cursor()
            while True:
                tag_record = tag_cursor.next()
                if tag_record is None:
                    break
                item_record.load_record(tag_record)
                item = item_record.value.name
                if tagvalue != item:
                    continue
                if item not in found_items:
                    items_in_games |= database.recordlist_record_number(
                        file, key=item_record.key.recno
                    )
                    found_items.add(item)
    return items_in_games


def _adjust_mode_identities(database, gamelist, tab):
    """Call _adjust_item_identities to adjust mode identity."""
    _adjust_item_identities(
        database,
        _modes_for_games(database, gamelist, tab),
        tab,
        filespec.MODE_FILE_DEF,
        moderecord.ModeDBrecord,
        "mode",
    )


def _adjust_player_type_identities(database, gamelist, tab):
    """Call _adjust_item_identities to adjust player type identity."""
    _adjust_item_identities(
        database,
        _player_types_for_games(database, gamelist, tab),
        tab,
        filespec.PLAYERTYPE_FILE_DEF,
        playertyperecord.PlayerTypeDBrecord,
        "player type",
    )


def _adjust_termination_identities(database, gamelist, tab):
    """Call _adjust_item_identities to adjust termination identity."""
    _adjust_item_identities(
        database,
        _terminations_for_games(database, gamelist, tab),
        tab,
        filespec.TERMINATION_FILE_DEF,
        terminationrecord.TerminationDBrecord,
        "termination",
    )


def _adjust_time_control_identities(database, gamelist, tab):
    """Call _adjust_item_identities to adjust time control identity."""
    _adjust_item_identities(
        database,
        _time_controls_for_games(database, gamelist, tab),
        tab,
        filespec.TIME_FILE_DEF,
        timecontrolrecord.TimeControlDBrecord,
        "time control",
    )


def _adjust_item_identities(database, itemlist, tab, file, recordclass, name):
    """Adjust item identities to be not associated with games for deletion.

    Not always possible, but if done where it is, the player identities and
    aliases associated with just the games to be deleted can be deleted too.

    """
    if itemlist.count_records() == 0:
        tab.append_text(name.join(("No ", "s need adjustment.\n")))
        return
    links = database.recordlist_ebm(file)
    links.remove_recordset(itemlist)
    if links.count_records() == 0:
        tab.append_text(
            name.join(("No alias ", "s exist to accept adjustments.\n"))
        )
        return
    edited_item_record = recordclass()
    edited_item_value = edited_item_record.value
    links_item_record = recordclass()
    links_item_value = links_item_record.value
    item_record = recordclass()
    item_value = item_record.value
    links_cursor = links.create_recordsetbase_cursor()
    while True:
        links_record = links_cursor.next()
        if links_record is None:
            break
        links_record = database.get_primary_record(file, links_record[0])
        links_item_record.load_record(links_record)
        cursor = itemlist.create_recordsetbase_cursor()
        adjusted_items = set()
        while True:
            record = cursor.next()
            if record is None:
                break
            record = database.get_primary_record(file, record[0])
            item_record.load_record(record)
            if item_value.name in adjusted_items:
                continue
            if links_item_value.alias == item_value.alias:
                edited_item_record.load_record(record)
                edited_item_value.alias = links_item_value.identity
                item_record.edit_record(
                    database, file, None, edited_item_record
                )
                adjusted_items.add(item_value.name)
                tab.append_text(
                    "".join(
                        (
                            name,
                            " ",
                            item_value.name,
                            " becomes an alias of ",
                            links_item_value.name,
                            ".\n",
                        )
                    )
                )
        if adjusted_items:
            edited_links_item_record = recordclass()
            edited_links_item_record.load_record(links_record)
            edited_links_item_record.value.alias = links_item_value.identity
            links_item_record.edit_record(
                database, file, None, edited_links_item_record
            )
