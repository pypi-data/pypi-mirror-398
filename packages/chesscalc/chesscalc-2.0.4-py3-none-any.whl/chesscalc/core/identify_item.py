# identify_item.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Functions to update item identification on database.

The event, time control, and mode, items have the same functions to manage
identification: but the data manipulated differs.

The functions in this module provide the operations on the data passed from
functions in the modules for each item type.

"""


class ItemIdentity(Exception):
    """Raise if unable to perform an operation on the item."""


def identify(
    database,
    bookmarks,
    selection,
    valueclass,
    recordclass,
    file,
    primary_field,
    alias_field,
    identity_field,
    item_name,
):
    """Make bookmarked items aliases of selection item.

    The bookmarked items must not be aliases already.

    The selection item can be aliased already.

    The changes are applied to database.

    """
    del primary_field, identity_field
    value = valueclass()
    value.load_alias_index_key(selection[0][0])
    selector = database.encode_record_selector(value.alias_index_key())
    database.start_transaction()
    try:
        recordlist = database.recordlist_key(file, alias_field, key=selector)
        count = recordlist.count_records()
        if count == 0:
            raise ItemIdentity(
                item_name.join(("Cannot identify: ", " record does not exist"))
            )
        if count > 1:
            raise ItemIdentity(
                item_name.join(("Cannot identify: ", " record duplicated"))
            )
        primary_record = get_first_item_on_recordlist(
            database, recordlist, file
        )
        selection_record = recordclass()
        selection_record.load_record(primary_record)
        for bookmark in bookmarks:
            value.load_alias_index_key(bookmark[0])
            selector = database.encode_record_selector(value.alias_index_key())
            recordlist = database.recordlist_key(
                file, alias_field, key=selector
            )
            count = recordlist.count_records()
            if count > 1:
                raise ItemIdentity(
                    item_name.join(
                        ("Cannot identify: ", " alias record duplicated")
                    )
                )
            if count == 0:
                raise ItemIdentity(
                    item_name.join(
                        ("Cannot identify: ", " alias record does not exist")
                    )
                )
            primary_record = get_first_item_on_recordlist(
                database, recordlist, file
            )
            item_record = recordclass()
            item_record.load_record(primary_record)
            if item_record.value.alias != item_record.value.identity:
                database.backout()
                return "".join(
                    (
                        "One of the bookmarked ",
                        item_name,
                        "s is already aliased so no changes done",
                    )
                )
            clone_record = item_record.clone()
            clone_record.value.alias = selection_record.value.alias
            assert item_record.srkey == clone_record.srkey
            item_record.edit_record(database, file, None, clone_record)
    except:  # pycodestyle E722: pylint is happy with following 'raise'.
        database.backout()
        raise
    database.commit()
    return None


def break_bookmarked_aliases(
    database,
    bookmarks,
    selection,
    valueclass,
    recordclass,
    file,
    primary_field,
    alias_field,
    identity_field,
    item_name,
):
    """Break aliases of selection item in bookmarks.

    The bookmarked aliases of selection become separate items.

    The changes are applied to database.

    """
    del primary_field, identity_field
    value = valueclass()
    value.load_alias_index_key(selection[0][0])
    selector = database.encode_record_selector(value.alias_index_key())
    database.start_transaction()
    try:
        recordlist = database.recordlist_key(file, alias_field, key=selector)
        count = recordlist.count_records()
        if count == 0:
            raise ItemIdentity(
                item_name.join(("Cannot break: ", " record does not exist"))
            )
        if count > 1:
            raise ItemIdentity(
                item_name.join(("Cannot break: ", " record duplicated"))
            )
        primary_record = get_first_item_on_recordlist(
            database, recordlist, file
        )
        selection_record = recordclass()
        selection_record.load_record(primary_record)
        if selection_record.value.identity != selection_record.value.alias:
            database.backout()
            return " ".join(
                ("Cannot break: selection is not the identified", item_name)
            )
        identity = selection_record.value.identity
        for bookmark in bookmarks:
            value.load_alias_index_key(bookmark[0])
            selector = database.encode_record_selector(value.alias_index_key())
            recordlist = database.recordlist_key(
                file, alias_field, key=selector
            )
            count = recordlist.count_records()
            if count > 1:
                raise ItemIdentity(
                    item_name.join(
                        ("Cannot break: ", " alias record duplicated")
                    )
                )
            if count == 0:
                raise ItemIdentity(
                    item_name.join(
                        ("Cannot break: ", " alias record does not exist")
                    )
                )
            primary_record = get_first_item_on_recordlist(
                database, recordlist, file
            )
            item_record = recordclass()
            item_record.load_record(primary_record)
            if item_record.value.alias != identity:
                database.backout()
                return "".join(
                    (
                        "One of the bookmarked ",
                        item_name,
                        "s is not aliased to same ",
                        item_name,
                        " as selection ",
                        item_name,
                        " so no changes done",
                    )
                )
            clone_record = item_record.clone()
            clone_record.value.alias = clone_record.value.identity
            assert item_record.srkey == clone_record.srkey
            item_record.edit_record(database, file, None, clone_record)
    except:  # pycodestyle E722: pylint is happy with following 'raise'.
        database.backout()
        raise
    database.commit()
    return None


def split_aliases(
    database,
    selection,
    valueclass,
    recordclass,
    file,
    primary_field,
    alias_field,
    identity_field,
    item_name,
):
    """Split aliases of selection item into separate items.

    The changes are applied to database.

    """
    del primary_field
    value = valueclass()
    value.load_alias_index_key(selection[0][0])
    selector = database.encode_record_selector(value.alias_index_key())
    database.start_transaction()
    try:
        recordlist = database.recordlist_key(file, alias_field, key=selector)
        count = recordlist.count_records()
        if count == 0:
            raise ItemIdentity(
                item_name.join(("Cannot split: ", " record does not exist"))
            )
        if count > 1:
            raise ItemIdentity(
                item_name.join(("Cannot split: ", " record duplicated"))
            )
        primary_record = get_first_item_on_recordlist(
            database, recordlist, file
        )
        selection_record = recordclass()
        selection_record.load_record(primary_record)
        if selection_record.value.identity != selection_record.value.alias:
            database.backout()
            return " ".join(
                ("Cannot split: selection is not the identified", item_name)
            )
        recordlist = database.recordlist_key(
            file,
            identity_field,
            key=database.encode_record_selector(selection_record.value.alias),
        )
        count = recordlist.count_records()
        if count == 0:
            raise ItemIdentity(
                item_name.join(("Cannot split: no ", "s with this identity"))
            )
        cursor = database.database_cursor(file, None, recordset=recordlist)
        try:
            while True:
                record = cursor.next()
                if not record:
                    break
                item_record = recordclass()
                item_record.load_record(
                    database.get_primary_record(file, record[0])
                )
                if item_record.value.alias == item_record.value.identity:
                    continue
                clone_record = item_record.clone()
                clone_record.value.alias = clone_record.value.identity
                assert item_record.srkey == clone_record.srkey
                item_record.edit_record(database, file, None, clone_record)
        finally:
            cursor.close()
    except:  # pycodestyle E722: pylint is happy with following 'raise'.
        database.backout()
        raise
    database.commit()
    return None


def change_aliases(
    database,
    selection,
    valueclass,
    recordclass,
    file,
    primary_field,
    alias_field,
    identity_field,
    item_name,
):
    """Change alias of all items with same alias as selection.

    All items with same alias as selection have their alias changed to
    identity of selection item.

    The changes are applied to database.

    """
    del primary_field
    value = valueclass()
    value.load_alias_index_key(selection[0][0])
    selector = database.encode_record_selector(value.alias_index_key())
    database.start_transaction()
    try:
        recordlist = database.recordlist_key(file, alias_field, key=selector)
        count = recordlist.count_records()
        if count == 0:
            raise ItemIdentity(
                item_name.join(("Cannot change: ", " record does not exist"))
            )
        if count > 1:
            raise ItemIdentity(
                item_name.join(("Cannot change: ", " record duplicated"))
            )
        primary_record = get_first_item_on_recordlist(
            database, recordlist, file
        )
        selection_record = recordclass()
        selection_record.load_record(primary_record)
        if selection_record.value.identity == selection_record.value.alias:
            database.backout()
            return "".join(
                (
                    "Not changed: selection is already the identified ",
                    item_name,
                )
            )
        recordlist = database.recordlist_key(
            file,
            identity_field,
            key=database.encode_record_selector(selection_record.value.alias),
        )
        count = recordlist.count_records()
        if count == 0:
            raise ItemIdentity(
                item_name.join(("Cannot change: no ", "s with this identity"))
            )
        cursor = database.database_cursor(
            file,
            None,
            recordset=recordlist,
        )
        try:
            while True:
                record = cursor.next()
                if not record:
                    break
                item_record = recordclass()
                item_record.load_record(
                    database.get_primary_record(file, record[0])
                )
                if selection_record.value.alias != item_record.value.alias:
                    database.backout()
                    return " ".join(
                        (
                            "Cannot change: alias is not for identified ",
                            item_name,
                        )
                    )
                clone_record = item_record.clone()
                clone_record.value.alias = selection_record.value.identity
                assert item_record.srkey == clone_record.srkey
                item_record.edit_record(database, file, None, clone_record)
        finally:
            cursor.close()
    except:  # pycodestyle E722: pylint is happy with following 'raise'.
        database.backout()
        raise
    database.commit()
    return None


def get_first_item_on_recordlist(database, recordlist, file):
    """Return item record on recordlist.

    Normally there will be only one record on recordlist: if more there
    may be a problem in the design of the database.  It is not wrong for
    there to be more than one record on a recordlist, but using this
    function is likely inappropriate in these cases.

    """
    cursor = database.database_cursor(file, None, recordset=recordlist)
    record = cursor.first()
    if record is None:
        return None
    return database.get_primary_record(file, record[0])


def get_identity_item_on_recordlist(valueclass, database, recordlist, file):
    """Return item record on recordlist where identity is also alias.

    Normally there will be only one record on recordlist fitting this
    condition because it is assumed there is only one alias value in the
    records on recordlist: if more there may be a problem in the design
    of the database.

    """
    value = valueclass()
    cursor = database.database_cursor(file, None, recordset=recordlist)
    while True:
        record = cursor.next()
        if record is None:
            return None
        primary_record = database.get_primary_record(file, record[0])
        if primary_record is None:
            continue
        value.load(primary_record[1])
        if value.alias == value.identity:
            return primary_record
