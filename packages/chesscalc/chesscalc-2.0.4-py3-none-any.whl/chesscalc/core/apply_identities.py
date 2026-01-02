# apply_identities.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""This module provides functions to verify and apply player identities.

Identities exported from a performance calculation database are verified
for consistency and applied to a database if consistent.

"""

from . import playerrecord
from . import filespec


class _ApplyIdentitiesReport(list):
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

    def __init__(self, names):
        """Initialise buckets for names."""
        self.names = names
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
        for name in self.names:
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
                continue
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
                    continue
                if alias not in identified_alias:
                    identified_alias[alias] = {name: record}
                else:
                    identified_alias[alias][name] = record
                continue
            not_on_database.add(name)

    def identify_names(self, database):
        """Make each not identified name an alias of an identified name.

        The name in identified_primary or derived from identified_alias
        will be the identified name if available.

        Otherwise one of the names in not_identified is picked and noted
        in chosen_name.

        """
        value = playerrecord.PersonValue()
        packer = playerrecord.PlayerDBrecord(
            valueclass=playerrecord.PersonDBvalue
        )
        player_record = playerrecord.PlayerDBrecord()
        person_record = playerrecord.PlayerDBrecord(
            valueclass=playerrecord.PersonDBvalue
        )
        encode_record_selector = database.encode_record_selector
        names = self.not_identified.copy()
        if len(self.identified_primary):
            chosen_alias, name = list(self.identified_primary.items())[0]
            record = list(name.values())[0]
        elif len(self.identified_alias):
            chosen_alias, name = list(self.identified_alias.items())[0]
            record = list(name.values())[0]
        else:
            chosen_name, record = names.popitem()
            player_record.load_record(record)
            chosen_alias = player_record.value.alias
            self.chosen_name = chosen_name
            person_record.load_record(record)

            # None is safe because self.srkey == new_record.srkey.
            # filespec.PLAYER_ALIAS_FIELD_DEF is correct value otherwise
            # because of how argument is used in edit_record().
            player_record.edit_record(
                database, filespec.PLAYER_FILE_DEF, None, person_record
            )

        packer.load_record(record)
        person = packer.value.alias_index_key()
        persongames = database.recordlist_key(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PLAYER_FIELD_DEF,
            key=encode_record_selector(person),
        )

        while len(names):
            name, record = names.popitem()
            # value should be PlayerDBvalue but while PersonDBvalue gives
            # the same answer there is no need to change it.
            value.load_alias_index_key(repr(name))
            player_record.load_record(record)
            person_record.load_record(record)
            person_record.value.alias = chosen_alias

            # None is safe because self.srkey == new_record.srkey.
            # filespec.PLAYER_ALIAS_FIELD_DEF is correct value otherwise
            # because of how argument is used in edit_record().
            player_record.edit_record(
                database, filespec.PLAYER_FILE_DEF, None, person_record
            )

            persongames |= database.recordlist_key(
                filespec.GAME_FILE_DEF,
                filespec.GAME_PLAYER_FIELD_DEF,
                key=encode_record_selector(value.alias_index_key()),
            )
        database.file_records_under(
            filespec.GAME_FILE_DEF,
            filespec.GAME_PERSON_FIELD_DEF,
            persongames,
            encode_record_selector(person),
        )


def verify_and_apply_identities(database, identities):
    """Return None if identities applied or a message for display if not."""
    if not database:
        return None
    if not identities:
        return None
    commit_flag = True
    report = _ApplyIdentitiesReport()
    database.start_transaction()
    try:
        for identity in identities:
            name = _NameStatus(identity)
            report.append(name)
            name.classify_names(database)
            if name.message is not None:
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
            if not identity.not_identified:
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
