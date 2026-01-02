# mirror_identities.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""This module provides functions to verify and mirror player identities.

Identities exported from a performance calculation database are verified
for consistency and the identities on a database are adjusted to fit if
consistent.

The exported identities are those with alias value the same as identity
value.  The alias values on the import database are adjusted to be the
identity value of the corresponding imported identity, but only if the
database identity is on the 'known' list.

"""

from . import playerrecord
from . import filespec


class _MirrorIdentitiesReport(list):
    """Report the outcome of verifying and applying player identities."""

    def __init__(self):
        """Define the initial report which also means no problems found."""
        self.messages_exist = False

    def append(self, identity):
        """Delegate and note if identity has a message."""
        super().append(identity)
        if identity.message is not None:
            self.messages_exist = True


class _NameStatus:
    """Classify names by representation on database.

    A name may: not exist, be new, be identified as primary, or an alias
    of a primary.
    """

    def __init__(self, name):
        """Initialise buckets for names."""
        self.name = name
        self.not_on_database = set()
        self.not_identified = {}
        self.identified_primary = {}
        self.identified_alias = {}
        self.chosen_name = None
        self.message = None

    def classify_names(self, database):
        """Put each name in the appropriate bucket."""
        not_on_database = self.not_on_database
        not_identified = self.not_identified
        identified_primary = self.identified_primary
        identified_alias = self.identified_alias
        value = playerrecord.PersonValue()
        person_record = playerrecord.PlayerDBrecord(
            valueclass=playerrecord.PersonDBvalue
        )
        encode_record_selector = database.encode_record_selector
        name = self.name
        value.load_alias_index_key(repr(name))
        personlist = database.recordlist_key(
            filespec.PLAYER_FILE_DEF,
            filespec.PLAYER_ALIAS_FIELD_DEF,
            key=encode_record_selector(value.alias_index_key()),
        )
        count = personlist.count_records()
        if count > 1:
            self.message = "Player by name record is not unique."
            return
        record = personlist.create_recordsetbase_cursor(
            internalcursor=True
        ).first()
        if record:
            not_identified[name] = record
            self.message = "Player by name is not on known player list."
            return
        personlist = database.recordlist_key(
            filespec.PLAYER_FILE_DEF,
            filespec.PERSON_ALIAS_FIELD_DEF,
            key=encode_record_selector(value.alias_index_key()),
        )
        count = personlist.count_records()
        if count > 1:
            self.message = "Person by name record is not unique."
            return
        record = personlist.create_recordsetbase_cursor(
            internalcursor=True
        ).first()
        if record:
            person_record.load_record(record)
            alias = person_record.value.alias
            if alias == person_record.value.identity:
                if alias not in identified_primary:
                    identified_primary[alias] = {name: record}
                else:
                    identified_primary[alias][name] = record
                return
            if alias not in identified_alias:
                identified_alias[alias] = {name: record}
            else:
                identified_alias[alias][name] = record
            return
        not_on_database.add(name)

    def identify_names(self, database):
        """Make name an alias of an identified name.

        The name in identified_primary or derived from identified_alias
        will be the identified name if available.

        Otherwise one of the names in not_identified is picked and noted
        in chosen_name.

        """
        person_record = playerrecord.PlayerDBrecord(
            valueclass=playerrecord.PersonDBvalue
        )
        encode_record_selector = database.encode_record_selector
        chosen_alias, name = list(self.identified_alias.items())[0]
        person_record.load_record(list(name.values())[0])
        persongames = database.recordlist_key(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PERSON_FIELD_DEF,
            key=encode_record_selector(person_record.value.alias),
        )
        database.unfile_records_under(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PERSON_FIELD_DEF,
            encode_record_selector(person_record.value.alias),
        )
        database.file_records_under(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PERSON_FIELD_DEF,
            persongames,
            key=encode_record_selector(person_record.value.identity),
        )
        value = playerrecord.PersonValue()
        player_record = playerrecord.PlayerDBrecord(
            valueclass=playerrecord.PersonDBvalue
        )
        for namemap in self.identified_alias.values():
            for name, record in namemap.items():
                # value should be PlayerDBvalue but while PersonDBvalue gives
                # the same answer there is no need to change it.
                value.load_alias_index_key(repr(name))
                player_record.load_record(record)
                personaliases = database.recordlist_key(
                    filespec.PLAYER_FILE_DEF,
                    filespec.PLAYER_LINKS_FIELD_DEF,
                    key=encode_record_selector(chosen_alias),
                )
                person_alias = player_record.value.identity
                cursor = personaliases.create_recordsetbase_cursor(
                    internalcursor=True
                )
                while True:
                    record = cursor.next()
                    if record is None:
                        break
                    player_record.load_record(record)
                    person_record.load_record(record)
                    person_record.value.alias = person_alias

                    # None is safe because self.srkey == new_record.srkey.
                    # filespec.PLAYER_ALIAS_FIELD_DEF is correct value normally
                    # because of how argument is used in edit_record().
                    player_record.edit_record(
                        database, filespec.PLAYER_FILE_DEF, None, person_record
                    )

                break
            break


def verify_and_mirror_identities(database, identities):
    """Return None if identities applied or a message for display if not."""
    if not database:
        return None
    if not identities:
        return None
    commit_flag = True
    report = _MirrorIdentitiesReport()
    database.start_transaction()
    try:
        for identity in identities:
            name = _NameStatus(identity)
            report.append(name)
            name.classify_names(database)
            if name.message is not None:
                report.messages_exist = True
                commit_flag = False
                continue
            if (
                len(set(name.identified_primary).union(name.identified_alias))
                > 1
            ):
                name.message = "More than one database person is referenced."
                report.messages_exist = True
                commit_flag = False
                continue
        if not commit_flag:
            return report
        for identity in report:
            if not identity.identified_alias:
                continue
            identity.identify_names(database)
        # For testing report what has been found.
        # if commit_flag:
        #     commit_flag = False
    finally:
        if commit_flag:
            database.commit()
        else:
            database.backout()
    return report
