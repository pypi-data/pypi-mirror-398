# selectorrecord.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Record definition classes chesscalc performance queries.

Named records store the identity references for a player or a set of events,
plus optional identity references for a time control, a terminationreason,
a playing mode, and a player type.  An option date range compared with the
PGN tag Date value is also stored.

"""

from solentware_base.core.record import KeyData
from solentware_base.core.record import ValueList
from solentware_base.core.record import Record

from . import filespec


class SelectorDBkey(KeyData):
    """Primary key of game selector."""


class SelectorDBvalue(ValueList):
    """Game Selector data."""

    attributes = {
        "name": None,
        "from_date": None,
        "to_date": None,
        "person_identity": None,
        "event_identities": None,
        "time_control_identity": None,
        "mode_identity": None,
        "termination_identity": None,
        "player_type_identity": None,
    }
    _attribute_order = (
        "person_identity",
        "name",
        "from_date",
        "to_date",
        "event_identities",
        "time_control_identity",
        "mode_identity",
        "termination_identity",
        "player_type_identity",
    )
    assert set(_attribute_order) == set(attributes)

    def __init__(self):
        """Customise ValueList for identity data."""
        super().__init__()
        self.name = None
        self.from_date = None
        self.to_date = None
        self.person_identity = None
        self.time_control_identity = None
        self.mode_identity = None
        self.termination_identity = None
        self.player_type_identity = None
        self.event_identities = []

    def empty(self):
        """(Re)Initialize value attribute."""
        self.name = None
        self.from_date = None
        self.to_date = None
        self.person_identity = None
        self.time_control_identity = None
        self.mode_identity = None
        self.termination_identity = None
        self.player_type_identity = None
        self.event_identities = []

    def pack(self):
        """Generate game selector record and index data."""
        val = super().pack()
        index = val[1]
        index[filespec.RULE_FIELD_DEF] = [self.name]
        return val


class SelectorDBrecord(Record):
    """Customise Record with SelectorDBkey and SelectorDBvalue by default."""

    def __init__(self, keyclass=SelectorDBkey, valueclass=SelectorDBvalue):
        """Delegate with keyclass and valueclass arguments."""
        super().__init__(keyclass, valueclass)

    def get_keys(self, datasource=None, partial=None):
        """Override, return [(key, value)] for datasource or []."""
        try:
            if partial is not None:
                return []
            srkey = datasource.dbhome.encode_record_number(self.key.pack())
            if datasource.primary:
                return [(srkey, self.srvalue)]
            dbname = datasource.dbname
            if dbname == filespec.RULE_FIELD_DEF:
                return [(self.value.name, srkey)]
            return []
        except:  # pycodestyle E722: pylint is happy with following 'raise'.
            if datasource is None:
                return []
            raise
