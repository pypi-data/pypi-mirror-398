# identify_person.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions to update player identification on database.

The functions support identifying a new player as an existing or new
person on the database, and undoing these identifications too.

"""
from . import playerrecord
from . import filespec
from . import identify_item

_RECORDS_PER_TRANSACTION = 10000


class PersonToPlayer(Exception):
    """Raise if unable to do split action on identified person."""


class PlayerToPerson(Exception):
    """Raise if unable to allocation player identity code."""


class PersonIdentity(Exception):
    """Raise if unable to change alias used as identified person."""


def identify_players_as_person(database, players, person):
    """Make new players aliases of identified person on database.

    If person is a new player rather than an identified person it is
    turned into an identified person.

    All players become aliases of person.

    The changes are applied to database.

    """
    database.start_transaction()
    try:
        gamelist = database.recordlist_nil(filespec.GAME_FILE_DEF)
        recordlist = database.recordlist_record_number(
            filespec.PLAYER_FILE_DEF, key=person[0][1]
        )
        count = recordlist.count_records()
        if count == 0:
            raise PlayerToPerson(
                repr(person[0]).join(("Person record ", " does not exist"))
            )
        primary_record = identify_item.get_first_item_on_recordlist(
            database, recordlist, filespec.PLAYER_FILE_DEF
        )
        player_record = playerrecord.PlayerDBrecord()
        player_record.load_record(primary_record)
        alias = player_record.value.alias
        selector = database.encode_record_selector(
            player_record.value.alias_index_key()
        )

        # May be adding aliases to an existing known player.
        current_gamelist = database.recordlist_key(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PERSON_FIELD_DEF,
            key=database.encode_record_selector(alias),
        )

        if current_gamelist is not None:
            gamelist |= current_gamelist
        current_gamelist.close()
        gamelist |= database.recordlist_key(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PLAYER_FIELD_DEF,
            key=selector,
        )
        recordlist = database.recordlist_key(
            filespec.PLAYER_FILE_DEF,
            filespec.PERSON_ALIAS_FIELD_DEF,
            key=selector,
        )
        count = recordlist.count_records()
        if (
            count
            + database.recordlist_key(
                filespec.PLAYER_FILE_DEF,
                filespec.PLAYER_ALIAS_FIELD_DEF,
                key=selector,
            ).count_records()
            != 1
        ):
            if count:
                raise PlayerToPerson("Duplicate references for person")
            raise PlayerToPerson(
                repr(person[0]).join(
                    ("Player reference for ", " does not exist")
                )
            )
        if count == 0:
            person_record = playerrecord.PlayerDBrecord(
                valueclass=playerrecord.PersonDBvalue
            )
            person_record.load_record(primary_record)

            # None is safe because self.srkey == new_record.srkey.
            # filespec.PLAYER_ALIAS_FIELD_DEF is correct value otherwise
            # because of how argument is used in edit_record().
            player_record.edit_record(
                database, filespec.PLAYER_FILE_DEF, None, person_record
            )

        for player in players:
            recordlist = database.recordlist_record_number(
                filespec.PLAYER_FILE_DEF, key=player[1]
            )
            count = recordlist.count_records()
            if count == 0:
                raise PlayerToPerson(
                    repr(person[0]).join(("Player record ", " does not exist"))
                )
            primary_record = identify_item.get_first_item_on_recordlist(
                database, recordlist, filespec.PLAYER_FILE_DEF
            )
            player_record = playerrecord.PlayerDBrecord()
            player_record.load_record(primary_record)
            gamelist |= database.recordlist_key(
                filespec.GAME_FILE_DEF,
                filespec.GAME_PLAYER_FIELD_DEF,
                key=database.encode_record_selector(
                    player_record.value.alias_index_key()
                ),
            )
            person_record = playerrecord.PlayerDBrecord(
                valueclass=playerrecord.PersonDBvalue
            )
            person_record.load_record(primary_record)
            person_record.value.alias = alias

            # None is safe because self.srkey == new_record.srkey.
            # filespec.PLAYER_ALIAS_FIELD_DEF is correct value otherwise
            # because of how argument is used in edit_record().
            player_record.edit_record(
                database, filespec.PLAYER_FILE_DEF, None, person_record
            )
        database.file_records_under(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PERSON_FIELD_DEF,
            gamelist,
            database.encode_record_selector(alias),
        )
    except:  # pycodestyle E722: pylint is happy with following 'raise'.
        database.backout()
        raise
    database.commit()


def identify_players_by_name_as_person(database, players, person):
    """Make new players aliases of identified person on database.

    Players are assumed to be the same if their names are the same.  Other
    detail contributing to the identity, such as event names, is ignored.
    If a person is given all players are assumed to be the same person even
    when their names differ.

    If person is a new player rather than an identified person it is
    turned into an identified person.

    All players become aliases of person.

    The changes are applied to database.

    """
    encode_record_selector = database.encode_record_selector
    database.start_transaction()
    try:
        gamelist = database.recordlist_nil(filespec.GAME_FILE_DEF)
        recordlist = database.recordlist_record_number(
            filespec.PLAYER_FILE_DEF, key=person[0][1]
        )
        count = recordlist.count_records()
        if count == 0:
            raise PlayerToPerson(
                repr(person[0]).join(("Person record ", " does not exist"))
            )
        primary_record = identify_item.get_first_item_on_recordlist(
            database, recordlist, filespec.PLAYER_FILE_DEF
        )
        player_record = playerrecord.PlayerDBrecord()
        player_record.load_record(primary_record)
        if player_record.value.alias != player_record.value.identity:
            # person is alias on identified players list so find known player.
            recordlist = database.recordlist_key(
                filespec.PLAYER_FILE_DEF,
                filespec.PLAYER_KNOWN_FIELD_DEF,
                key=encode_record_selector(player_record.value.alias),
            )
            count = recordlist.count_records()
            if count == 0:
                raise PlayerToPerson(
                    repr(person[0]).join(
                        ("Person record for alias ", " does not exist")
                    )
                )
            primary_record = identify_item.get_first_item_on_recordlist(
                database, recordlist, filespec.PLAYER_FILE_DEF
            )
            player_record.load_record(primary_record)
            assert player_record.value.alias == player_record.value.identity
        selector = encode_record_selector(
            player_record.value.alias_index_key()
        )

        # May be adding aliases to an existing known player.
        current_gamelist = database.recordlist_key(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PERSON_FIELD_DEF,
            key=encode_record_selector(player_record.value.alias),
        )

        if current_gamelist is not None:
            gamelist |= current_gamelist
        current_gamelist.close()
        gamelist |= database.recordlist_key(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PLAYER_FIELD_DEF,
            key=selector,
        )
        recordlist = database.recordlist_key(
            filespec.PLAYER_FILE_DEF,
            filespec.PERSON_ALIAS_FIELD_DEF,
            key=selector,
        )
        count = recordlist.count_records()
        if (
            count
            + database.recordlist_key(
                filespec.PLAYER_FILE_DEF,
                filespec.PLAYER_ALIAS_FIELD_DEF,
                key=selector,
            ).count_records()
            != 1
        ):
            if count:
                raise PlayerToPerson("Duplicate references for person")
            raise PlayerToPerson(
                repr(person[0]).join(
                    ("Player reference for ", " does not exist")
                )
            )
        if count == 0:
            # A known player was not selected so the selection on the new
            # player list becomes a known player and all the other entries
            # on the new list with the same same become aliases of it.
            # Even if entries with the same name exist on the known list.
            person_record = playerrecord.PlayerDBrecord(
                valueclass=playerrecord.PersonDBvalue
            )
            person_record.load_record(primary_record)

            # None is safe because self.srkey == new_record.srkey.
            # filespec.PLAYER_ALIAS_FIELD_DEF is correct value otherwise
            # because of how argument is used in edit_record().
            player_record.edit_record(
                database, filespec.PLAYER_FILE_DEF, None, person_record
            )
        alias = player_record.value.alias
        player_value = player_record.value
        person_record = playerrecord.PlayerDBrecord(
            valueclass=playerrecord.PersonDBvalue
        )
        for player in players:
            recordlist = database.recordlist_key(
                filespec.PLAYER_FILE_DEF,
                filespec.PLAYER_NAME_FIELD_DEF,
                key=encode_record_selector(player[0]),
            )
            count = recordlist.count_records()
            if count == 0:
                # Assume players set refered to same entry as person list.
                continue
            cursor = recordlist.create_recordsetbase_cursor()
            while True:
                record = cursor.next()
                if record is None:
                    break
                record = database.get_primary_record(
                    filespec.PLAYER_FILE_DEF, record[0]
                )
                player_record.load_record(record)
                person_record.load_record(record)
                person_record.value.alias = alias

                # None is safe because self.srkey == new_record.srkey.
                # filespec.PLAYER_ALIAS_FIELD_DEF is correct value otherwise
                # because of how argument is used in edit_record().
                player_record.edit_record(
                    database, filespec.PLAYER_FILE_DEF, None, person_record
                )

                gamelist |= database.recordlist_key(
                    filespec.GAME_FILE_DEF,
                    filespec.GAME_PLAYER_FIELD_DEF,
                    key=encode_record_selector(player_value.alias_index_key()),
                )
        database.file_records_under(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PERSON_FIELD_DEF,
            gamelist,
            database.encode_record_selector(alias),
        )
    except:  # pycodestyle E722: pylint is happy with following 'raise'.
        database.backout()
        raise
    database.commit()


def identify_all_players_by_name_as_persons(database):
    """Make new players with same aliases of same person on database.

    Players are assumed to be the same if their names are the same.  Other
    detail contributing to the identity, such as event names, is ignored.

    If there is more than one person on the database with the same name then
    the new player is left as a new player.  This method will not make a
    decision when there is a choice on what to do.

    All players become aliases of person.

    The changes are applied to database.

    """
    encode_record_selector = database.encode_record_selector
    player_record = playerrecord.PlayerDBrecord()
    person_record = playerrecord.PlayerDBrecord(
        valueclass=playerrecord.PersonDBvalue
    )
    value = player_record.value
    name_known_map = {}
    database.start_transaction()
    try:
        known = database.recordlist_all(
            filespec.PLAYER_FILE_DEF, filespec.PLAYER_LINKS_FIELD_DEF
        )
        cursor = known.create_recordsetbase_cursor()
        while True:
            record = cursor.next()
            if record is None:
                break
            record = database.get_primary_record(
                filespec.PLAYER_FILE_DEF, record[0]
            )
            player_record.load_record(record)
            name_known_map.setdefault(value.name, set()).add(value.alias)
        cursor.close()
        known.close()
        del known
        new = database.recordlist_all(
            filespec.PLAYER_FILE_DEF, filespec.PLAYER_NAME_FIELD_DEF
        )
        cursor = new.create_recordsetbase_cursor()

        # Keep transactions smallish.
        # Elsewhere 32000 is not too large just indexing records, but trying
        # to do about a million records here is too much with all the changes
        # to related records.
        counter = _RECORDS_PER_TRANSACTION

        while True:
            # first() not next() because of the new.remove_recordset(name_new)
            # call done immediately after creating the name_new list.
            # The later record updates may lead to cursor's segment pointer
            # referring to a segment that no longer exists if next() is
            # called.  This may cause an exception and backout or early exit
            # from the update and commit depending on where the underlying
            # support of cursor thinks it is located.
            # It would be safe to call next() if the current record were not
            # on the name_new list.
            record = cursor.first()

            if record is None:
                break
            if counter < 1:
                database.commit()

                # Want to do database resizing for LMDB and DPT but the
                # deferred_update_housekeeping method is only in the *_du
                # chain at present.
                # database.deferred_update_housekeeping()

                database.start_transaction()
                counter = _RECORDS_PER_TRANSACTION
            counter -= 1
            record = database.get_primary_record(
                filespec.PLAYER_FILE_DEF, record[0]
            )
            player_record.load_record(record)
            name_new = database.recordlist_key(
                filespec.PLAYER_FILE_DEF,
                filespec.PLAYER_NAME_FIELD_DEF,
                key=encode_record_selector(value.name),
            )
            new.remove_recordset(name_new)
            if value.name in name_known_map:
                if len(name_known_map[value.name]) > 1:
                    name_new.close()
                    continue
                gamelist = database.recordlist_key(
                    filespec.GAME_FILE_DEF,
                    filespec.GAME_PERSON_FIELD_DEF,
                    key=encode_record_selector(value.alias_index_key()),
                )
                alias = value.alias
                name_cursor = name_new.create_recordsetbase_cursor()
                while True:
                    record = name_cursor.next()
                    if record is None:
                        break
                    record = database.get_primary_record(
                        filespec.PLAYER_FILE_DEF, record[0]
                    )
                    player_record.load_record(record)
                    person_record.load_record(record)
                    person_record.value.alias = alias

                    # None is safe because self.srkey == new_record.srkey.
                    # filespec.PLAYER_ALIAS_FIELD_DEF is correct value
                    # otherwise because of how argument is used in
                    # edit_record().
                    player_record.edit_record(
                        database, filespec.PLAYER_FILE_DEF, None, person_record
                    )

                    gamelist |= database.recordlist_key(
                        filespec.GAME_FILE_DEF,
                        filespec.GAME_PLAYER_FIELD_DEF,
                        key=encode_record_selector(
                            player_record.value.alias_index_key()
                        ),
                    )
                database.file_records_under(
                    filespec.GAME_FILE_DEF,
                    filespec.GAME_PERSON_FIELD_DEF,
                    gamelist,
                    database.encode_record_selector(alias),
                )
                name_new.close()
                continue
            gamelist = database.recordlist_nil(filespec.GAME_FILE_DEF)
            alias = value.alias
            name_cursor = name_new.create_recordsetbase_cursor()
            while True:
                record = name_cursor.next()
                if record is None:
                    break
                record = database.get_primary_record(
                    filespec.PLAYER_FILE_DEF, record[0]
                )
                player_record.load_record(record)
                person_record.load_record(record)
                person_record.value.alias = alias

                # None is safe because self.srkey == new_record.srkey.
                # filespec.PLAYER_ALIAS_FIELD_DEF is correct value
                # otherwise because of how argument is used in
                # edit_record().
                player_record.edit_record(
                    database, filespec.PLAYER_FILE_DEF, None, person_record
                )

                gamelist |= database.recordlist_key(
                    filespec.GAME_FILE_DEF,
                    filespec.GAME_PLAYER_FIELD_DEF,
                    key=encode_record_selector(
                        player_record.value.alias_index_key()
                    ),
                )
            database.file_records_under(
                filespec.GAME_FILE_DEF,
                filespec.GAME_PERSON_FIELD_DEF,
                gamelist,
                database.encode_record_selector(alias),
            )
            name_new.close()
    except:  # pycodestyle E722: pylint is happy with following 'raise'.
        database.backout()
        raise
    database.commit()


def split_person_into_all_players(database, person, answer):
    """Split person into new player aliases on database.

    All aliases of person become separate new players.

    The changes are applied to database.

    """
    database.start_transaction()
    try:
        recordlist = database.recordlist_record_number(
            filespec.PLAYER_FILE_DEF, key=person[0][1]
        )
        count = recordlist.count_records()
        if count == 0:
            raise PersonToPlayer(
                repr(person[0]).join(("Person record ", " does not exist"))
            )
        primary_record = identify_item.get_first_item_on_recordlist(
            database, recordlist, filespec.PLAYER_FILE_DEF
        )
        person_record = playerrecord.PlayerDBrecord(
            valueclass=playerrecord.PersonDBvalue
        )
        person_record.load_record(primary_record)
        if person_record.value.identity != person_record.value.alias:
            database.backout()
            answer[
                "message"
            ] = "Cannot split: selection is not the identified person"
            return
        identity = person_record.value.alias
        recordlist = database.recordlist_key(
            filespec.PLAYER_FILE_DEF,
            filespec.PLAYER_LINKS_FIELD_DEF,
            key=database.encode_record_selector(identity),
        )
        count = recordlist.count_records()
        if count == 0:
            raise PlayerToPerson("Cannot split: no players with this identity")
        cursor = database.database_cursor(
            filespec.PLAYER_FILE_DEF,
            None,
            recordset=recordlist,
        )
        try:
            while True:
                record = cursor.next()
                if not record:
                    break
                primary_record = database.get_primary_record(
                    filespec.PLAYER_FILE_DEF, record[0]
                )
                alias_record = playerrecord.PlayerDBrecord(
                    valueclass=playerrecord.PersonDBvalue
                )
                alias_record.load_record(primary_record)
                if identity != alias_record.value.alias:
                    database.backout()
                    answer[
                        "message"
                    ] = "Cannot split: selection is not for identified person"
                    return
                player_record = playerrecord.PlayerDBrecord()
                player_record.load_record(primary_record)
                player_record.value.alias = player_record.value.identity

                # None is safe because self.srkey == new_record.srkey.
                # filespec.PLAYER_LINKS_FIELD_DEF is correct value otherwise
                # because of how argument is used in edit_record().
                alias_record.edit_record(
                    database, filespec.PLAYER_FILE_DEF, None, player_record
                )
        finally:
            cursor.close()
        database.unfile_records_under(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PERSON_FIELD_DEF,
            database.encode_record_selector(identity),
        )
    except:  # pycodestyle E722: pylint is happy with following 'raise'.
        database.backout()
        raise
    database.commit()
    return


def break_person_into_picked_players(database, person, aliases, answer):
    """Break aliases of person into new player aliases on database.

    The aliases of person become separate new players.

    The changes are applied to database.

    """
    database.start_transaction()
    try:
        recordlist = database.recordlist_record_number(
            filespec.PLAYER_FILE_DEF, key=person[0][1]
        )
        count = recordlist.count_records()
        if count == 0:
            raise PersonToPlayer(
                repr(person[0]).join(("Person record ", " does not exist"))
            )
        primary_record = identify_item.get_first_item_on_recordlist(
            database, recordlist, filespec.PLAYER_FILE_DEF
        )
        person_record = playerrecord.PlayerDBrecord(
            valueclass=playerrecord.PersonDBvalue
        )
        person_record.load_record(primary_record)
        if person_record.value.identity != person_record.value.alias:
            database.backout()
            answer[
                "message"
            ] = "Cannot break: selection is not the identified person"
            return
        identity = person_record.value.identity
        gamelist = database.recordlist_key(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PERSON_FIELD_DEF,
            key=database.encode_record_selector(identity),
        )
        for alias in aliases:
            recordlist = database.recordlist_record_number(
                filespec.PLAYER_FILE_DEF, key=alias[1]
            )
            count = recordlist.count_records()
            if count == 0:
                raise PersonToPlayer(
                    repr(alias[0]).join(
                        ("Cannot break: alias record ", " does not exist")
                    )
                )
            primary_record = identify_item.get_first_item_on_recordlist(
                database,
                recordlist,
                filespec.PLAYER_FILE_DEF,
            )
            player_record = playerrecord.PlayerDBrecord()
            player_record.load_record(primary_record)
            if identity != player_record.value.alias:
                database.backout()
                answer["message"] = "".join(
                    (
                        "One of the bookmarked players is not aliased ",
                        "to same player as selection player ",
                        "so no changes done",
                    )
                )
                return
            gamelist.remove_recordset(
                database.recordlist_key(
                    filespec.GAME_FILE_DEF,
                    filespec.GAME_PLAYER_FIELD_DEF,
                    key=database.encode_record_selector(
                        player_record.value.alias_index_key()
                    ),
                )
            )
            alias_record = playerrecord.PlayerDBrecord(
                valueclass=playerrecord.PersonDBvalue
            )
            alias_record.load_record(primary_record)
            player_record.value.alias = player_record.value.identity

            # None is safe because self.srkey == new_record.srkey.
            # filespec.PLAYER_ALIAS_FIELD_DEF is correct value otherwise
            # because of how argument is used in edit_record().
            alias_record.edit_record(
                database, filespec.PLAYER_FILE_DEF, None, player_record
            )
        database.file_records_under(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PERSON_FIELD_DEF,
            gamelist,
            database.encode_record_selector(identity),
        )
    except:  # pycodestyle E722: pylint is happy with following 'raise'.
        database.backout()
        raise
    database.commit()
    return


def change_identified_person(database, player, answer):
    """Change identified person to player on database.

    All aliases of player have their alias changed to player identity.

    The changes are applied to database.

    """
    database.start_transaction()
    try:
        recordlist = database.recordlist_record_number(
            filespec.PLAYER_FILE_DEF, key=player[0][1]
        )
        count = recordlist.count_records()
        if count == 0:
            raise PersonIdentity(
                repr(player[0]).join(("Person record ", " does not exist"))
            )
        primary_record = identify_item.get_first_item_on_recordlist(
            database, recordlist, filespec.PLAYER_FILE_DEF
        )
        selection_record = playerrecord.PlayerDBrecord(
            valueclass=playerrecord.PersonDBvalue
        )
        selection_record.load_record(primary_record)
        if selection_record.value.identity == selection_record.value.alias:
            database.backout()
            answer[
                "message"
            ] = "Not changed: selection is already the identified person"
            return
        recordlist = database.recordlist_key(
            filespec.PLAYER_FILE_DEF,
            filespec.PLAYER_LINKS_FIELD_DEF,
            key=database.encode_record_selector(selection_record.value.alias),
        )
        count = recordlist.count_records()
        if count == 0:
            raise PersonIdentity(
                "Cannot change: no players with this identity"
            )
        gamelist = database.recordlist_key(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PERSON_FIELD_DEF,
            key=database.encode_record_selector(selection_record.value.alias),
        )
        cursor = database.database_cursor(
            filespec.PLAYER_FILE_DEF,
            None,
            recordset=recordlist,
        )
        try:
            while True:
                record = cursor.next()
                if not record:
                    break
                alias_record = playerrecord.PlayerDBrecord(
                    valueclass=playerrecord.PersonDBvalue
                )
                alias_record.load_record(
                    database.get_primary_record(
                        filespec.PLAYER_FILE_DEF, record[0]
                    )
                )
                if selection_record.value.alias != alias_record.value.alias:
                    database.backout()
                    answer[
                        "message"
                    ] = "Cannot change: alias is not for identified person"
                    return
                clone_record = alias_record.clone()
                clone_record.value.alias = selection_record.value.identity
                assert alias_record.srkey == clone_record.srkey
                alias_record.edit_record(
                    database, filespec.PLAYER_FILE_DEF, None, clone_record
                )
        finally:
            cursor.close()
        database.unfile_records_under(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PERSON_FIELD_DEF,
            database.encode_record_selector(selection_record.value.alias),
        )
        database.file_records_under(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PERSON_FIELD_DEF,
            gamelist,
            database.encode_record_selector(selection_record.value.identity),
        )
    except:  # pycodestyle E722: pylint is happy with following 'raise'.
        database.backout()
        raise
    database.commit()
    return
