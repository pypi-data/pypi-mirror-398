# filespec.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Files and fields for Chess Performance Calculation database."""

from solentware_base.core.constants import (
    PRIMARY,
    SECONDARY,
    # DEFER,
    BTOD_FACTOR,
    DEFAULT_RECORDS,
    DEFAULT_INCREASE_FACTOR,
    BTOD_CONSTANT,
    DDNAME,
    FILE,
    # FOLDER,
    FIELDS,
    FILEDESC,
    # FLT,
    INV,
    # UAE,
    ORD,
    # ONM,
    # SPT,
    # EO,
    RRN,
    # BSIZE,
    BRECPPG,
    # BRESERVE,
    # BREUSE,
    # DSIZE,
    # DRESERVE,
    # DPGSRES,
    FILEORG,
    DPT_PRIMARY_FIELD_LENGTH,
)
import solentware_base.core.filespec

# Names used to refer to files fields and indexes in Python code.
# The file description name is used as the primary field name.

# Workaround 21 November 2023.
# <..._FILE_DEF> and <..._FIELD_DEF> values should be <value>.title() for
# DPT compatibility.  Or the values in the <SECONDARY> dicts should be
# fld(<...FIELD_DEF>) to fit the keys in the <FIELDS> dicts.
# This is the scheme chosen for naming things for simplicity in non-DPT
# databases while meeting the DPT naming conventions for files and fields.
# The implementation of Fast Load in DPT converts all field names to
# upper case, breaking both DPT field naming consistency and the scheme
# for naming things in FuleSpecs.
# An extension of FileSpec in dpt sub-package forces all <..._FILE_DEF> and
# <..._FIELD_DEF> values used as key or value in <SECONDARY> and <FIELDS>
# dicts to upper case to avoid any Fast Load accidents.  There is no point
# now to the keys of <FIELDS> dict being fld(<...FIELD_DEF>) except this
# transform generates the <SECONDARY> dicts values if given as None in the
# FileSpec.
# Workaround moved to solentware_base.core._dpt.Database.__init__() method.

# File description names.
GAME_FILE_DEF = "game"
PLAYER_FILE_DEF = "player"
IDENTITY_FILE_DEF = "identity"
SELECTION_FILE_DEF = "selection"
EVENT_FILE_DEF = "event"
TIME_FILE_DEF = "time"
MODE_FILE_DEF = "mode"
TERMINATION_FILE_DEF = "termination"
PLAYERTYPE_FILE_DEF = "playertype"

# game file fields.
GAME_FIELD_DEF = GAME_FILE_DEF
GAME_PGNFILE_FIELD_DEF = "gamepgnfile"
GAME_NUMBER_FIELD_DEF = "gamenumber"
GAME_DATE_FIELD_DEF = "gamedate"
GAME_TIMECONTROL_FIELD_DEF = "gametimecontrol"
GAME_MODE_FIELD_DEF = "gamemode"
GAME_PLAYER_FIELD_DEF = "gameplayer"
GAME_EVENT_FIELD_DEF = "gameevent"
GAME_PERSON_FIELD_DEF = "gameperson"
GAME_NAME_FIELD_DEF = "gamename"
GAME_TERMINATION_FIELD_DEF = "gametermination"
GAME_PLAYERTYPE_FIELD_DEF = "gameplayertype"

# player file fields.
PLAYER_FIELD_DEF = PLAYER_FILE_DEF
PLAYER_IDENTIFIER_FIELD_DEF = "playeridentifier"
PLAYER_KNOWN_FIELD_DEF = "playerknown"
PLAYER_LINKS_FIELD_DEF = "playerlinks"
PLAYER_ALIAS_FIELD_DEF = "playeralias"
PERSON_ALIAS_FIELD_DEF = "personalias"
PLAYER_NAME_FIELD_DEF = "playername"
PERSON_NAME_FIELD_DEF = "personname"

# identity file fields.
IDENTITY_FIELD_DEF = IDENTITY_FILE_DEF
IDENTITY_TYPE_FIELD_DEF = "identitytype"

# selection file fields.
SELECTION_FIELD_DEF = SELECTION_FILE_DEF
RULE_FIELD_DEF = "rule"

# event file fields.
EVENT_FIELD_DEF = EVENT_FILE_DEF
EVENT_IDENTITY_FIELD_DEF = "eventidentity"
EVENT_ALIAS_FIELD_DEF = "eventalias"
EVENT_NAME_FIELD_DEF = "eventname"

# time (limit/control) file fields.
TIME_FIELD_DEF = TIME_FILE_DEF
TIME_IDENTITY_FIELD_DEF = "timeidentity"
TIME_ALIAS_FIELD_DEF = "timealias"

# mode (OTB, Online, ...) file fields.
MODE_FIELD_DEF = MODE_FILE_DEF
MODE_IDENTITY_FIELD_DEF = "modeidentity"
MODE_ALIAS_FIELD_DEF = "modealias"

# termination (Default, Bye, ...) file fields.
TERMINATION_FIELD_DEF = TERMINATION_FILE_DEF
TERMINATION_IDENTITY_FIELD_DEF = "terminationidentity"
TERMINATION_ALIAS_FIELD_DEF = "terminationalias"

# playertype (human, computer, ...) file fields.
PLAYERTYPE_FIELD_DEF = PLAYERTYPE_FILE_DEF
PLAYERTYPE_IDENTITY_FIELD_DEF = "playertypeidentity"
PLAYERTYPE_ALIAS_FIELD_DEF = "playertypealias"


class FileSpec(solentware_base.core.filespec.FileSpec):
    """Specify the results database."""

    def __init__(
        self, use_specification_items=None, dpt_records=None, **kargs
    ):
        """Define Chess Performance Calculation database and delegate."""
        dptfn = FileSpec.dpt_dsn
        fld = FileSpec.field_name

        super().__init__(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
            **{
                GAME_FILE_DEF: {
                    DDNAME: "GAME",
                    FILE: dptfn(GAME_FILE_DEF),
                    FILEDESC: {
                        BRECPPG: 15,
                        FILEORG: RRN,
                    },
                    BTOD_FACTOR: 1,
                    BTOD_CONSTANT: 30,
                    DEFAULT_RECORDS: 40000,
                    DEFAULT_INCREASE_FACTOR: 0.01,
                    PRIMARY: fld(GAME_FIELD_DEF),
                    SECONDARY: {
                        GAME_PGNFILE_FIELD_DEF: None,
                        GAME_NUMBER_FIELD_DEF: None,
                        GAME_DATE_FIELD_DEF: None,
                        GAME_TIMECONTROL_FIELD_DEF: None,
                        GAME_MODE_FIELD_DEF: None,
                        GAME_PLAYER_FIELD_DEF: None,
                        GAME_EVENT_FIELD_DEF: None,
                        GAME_PERSON_FIELD_DEF: None,
                        GAME_NAME_FIELD_DEF: None,
                        GAME_TERMINATION_FIELD_DEF: None,
                        GAME_PLAYERTYPE_FIELD_DEF: None,
                    },
                    FIELDS: {
                        fld(GAME_FIELD_DEF): None,
                        fld(GAME_PGNFILE_FIELD_DEF): {INV: True, ORD: True},
                        fld(GAME_NUMBER_FIELD_DEF): {INV: True, ORD: True},
                        fld(GAME_DATE_FIELD_DEF): {INV: True, ORD: True},
                        fld(GAME_TIMECONTROL_FIELD_DEF): {
                            INV: True,
                            ORD: True,
                        },
                        fld(GAME_MODE_FIELD_DEF): {INV: True, ORD: True},
                        fld(GAME_PLAYER_FIELD_DEF): {INV: True, ORD: True},
                        fld(GAME_EVENT_FIELD_DEF): {INV: True, ORD: True},
                        fld(GAME_PERSON_FIELD_DEF): {INV: True, ORD: True},
                        fld(GAME_NAME_FIELD_DEF): {INV: True, ORD: True},
                        fld(GAME_TERMINATION_FIELD_DEF): {
                            INV: True,
                            ORD: True,
                        },
                        fld(GAME_PLAYERTYPE_FIELD_DEF): {INV: True, ORD: True},
                    },
                },
                PLAYER_FILE_DEF: {
                    DDNAME: "PLAYER",
                    FILE: dptfn(PLAYER_FILE_DEF),
                    FILEDESC: {
                        BRECPPG: 80,
                        FILEORG: RRN,
                    },
                    BTOD_FACTOR: 2.0,
                    BTOD_CONSTANT: 50,
                    DEFAULT_RECORDS: 200000,
                    DEFAULT_INCREASE_FACTOR: 0.01,
                    PRIMARY: fld(PLAYER_FIELD_DEF),
                    SECONDARY: {
                        PLAYER_IDENTIFIER_FIELD_DEF: None,
                        PLAYER_KNOWN_FIELD_DEF: None,
                        PLAYER_LINKS_FIELD_DEF: None,
                        PLAYER_ALIAS_FIELD_DEF: None,
                        PERSON_ALIAS_FIELD_DEF: None,
                        PLAYER_NAME_FIELD_DEF: None,
                        PERSON_NAME_FIELD_DEF: None,
                    },
                    FIELDS: {
                        fld(PLAYER_FIELD_DEF): None,
                        fld(PLAYER_IDENTIFIER_FIELD_DEF): {
                            INV: True,
                            ORD: True,
                        },
                        fld(PLAYER_KNOWN_FIELD_DEF): {INV: True, ORD: True},
                        fld(PLAYER_LINKS_FIELD_DEF): {INV: True, ORD: True},
                        fld(PLAYER_ALIAS_FIELD_DEF): {INV: True, ORD: True},
                        fld(PERSON_ALIAS_FIELD_DEF): {INV: True, ORD: True},
                        fld(PLAYER_NAME_FIELD_DEF): {INV: True, ORD: True},
                        fld(PERSON_NAME_FIELD_DEF): {INV: True, ORD: True},
                    },
                },
                IDENTITY_FILE_DEF: {
                    DDNAME: "IDENTITY",
                    FILE: dptfn(IDENTITY_FILE_DEF),
                    FILEDESC: {
                        BRECPPG: 80,
                        FILEORG: RRN,
                    },
                    BTOD_FACTOR: 2.0,
                    BTOD_CONSTANT: 50,
                    DEFAULT_RECORDS: 400,
                    DEFAULT_INCREASE_FACTOR: 0.01,
                    PRIMARY: fld(IDENTITY_FIELD_DEF),
                    SECONDARY: {
                        IDENTITY_TYPE_FIELD_DEF: None,
                    },
                    FIELDS: {
                        fld(IDENTITY_FIELD_DEF): None,
                        fld(IDENTITY_TYPE_FIELD_DEF): {INV: True, ORD: True},
                    },
                },
                SELECTION_FILE_DEF: {
                    DDNAME: "SLCTRULE",
                    FILE: dptfn(SELECTION_FILE_DEF),
                    FILEDESC: {
                        BRECPPG: 20,
                        FILEORG: RRN,
                    },
                    BTOD_FACTOR: 1,  # a guess
                    BTOD_CONSTANT: 100,  # a guess
                    DEFAULT_RECORDS: 100,
                    DEFAULT_INCREASE_FACTOR: 0.5,
                    PRIMARY: fld(SELECTION_FIELD_DEF),
                    DPT_PRIMARY_FIELD_LENGTH: 127,
                    SECONDARY: {
                        RULE_FIELD_DEF: None,
                    },
                    FIELDS: {
                        fld(SELECTION_FIELD_DEF): None,
                        fld(RULE_FIELD_DEF): {INV: True, ORD: True},
                    },
                },
                EVENT_FILE_DEF: {
                    DDNAME: "EVENT",
                    FILE: dptfn(EVENT_FILE_DEF),
                    FILEDESC: {
                        BRECPPG: 60,
                        FILEORG: RRN,
                    },
                    BTOD_FACTOR: 2.0,
                    BTOD_CONSTANT: 50,
                    DEFAULT_RECORDS: 10000,
                    DEFAULT_INCREASE_FACTOR: 0.01,
                    PRIMARY: fld(EVENT_FIELD_DEF),
                    SECONDARY: {
                        EVENT_IDENTITY_FIELD_DEF: None,
                        EVENT_ALIAS_FIELD_DEF: None,
                        EVENT_NAME_FIELD_DEF: None,
                    },
                    FIELDS: {
                        fld(EVENT_FIELD_DEF): None,
                        fld(EVENT_IDENTITY_FIELD_DEF): {INV: True, ORD: True},
                        fld(EVENT_ALIAS_FIELD_DEF): {INV: True, ORD: True},
                        fld(EVENT_NAME_FIELD_DEF): {INV: True, ORD: True},
                    },
                },
                TIME_FILE_DEF: {
                    DDNAME: "TIME",
                    FILE: dptfn(TIME_FILE_DEF),
                    FILEDESC: {
                        BRECPPG: 80,
                        FILEORG: RRN,
                    },
                    BTOD_FACTOR: 2.0,
                    BTOD_CONSTANT: 50,
                    DEFAULT_RECORDS: 1000,
                    DEFAULT_INCREASE_FACTOR: 0.01,
                    PRIMARY: fld(TIME_FIELD_DEF),
                    SECONDARY: {
                        TIME_IDENTITY_FIELD_DEF: None,
                        TIME_ALIAS_FIELD_DEF: None,
                    },
                    FIELDS: {
                        fld(TIME_FIELD_DEF): None,
                        fld(TIME_IDENTITY_FIELD_DEF): {INV: True, ORD: True},
                        fld(TIME_ALIAS_FIELD_DEF): {INV: True, ORD: True},
                    },
                },
                MODE_FILE_DEF: {
                    DDNAME: "MODE",
                    FILE: dptfn(MODE_FILE_DEF),
                    FILEDESC: {
                        BRECPPG: 80,
                        FILEORG: RRN,
                    },
                    BTOD_FACTOR: 2.0,
                    BTOD_CONSTANT: 50,
                    DEFAULT_RECORDS: 400,
                    DEFAULT_INCREASE_FACTOR: 0.01,
                    PRIMARY: fld(MODE_FIELD_DEF),
                    SECONDARY: {
                        MODE_IDENTITY_FIELD_DEF: None,
                        MODE_ALIAS_FIELD_DEF: None,
                    },
                    FIELDS: {
                        fld(MODE_FIELD_DEF): None,
                        fld(MODE_IDENTITY_FIELD_DEF): {INV: True, ORD: True},
                        fld(MODE_ALIAS_FIELD_DEF): {INV: True, ORD: True},
                    },
                },
                TERMINATION_FILE_DEF: {
                    DDNAME: "TERMINTE",
                    FILE: dptfn(TERMINATION_FILE_DEF),
                    FILEDESC: {
                        BRECPPG: 80,
                        FILEORG: RRN,
                    },
                    BTOD_FACTOR: 2.0,
                    BTOD_CONSTANT: 50,
                    DEFAULT_RECORDS: 400,
                    DEFAULT_INCREASE_FACTOR: 0.01,
                    PRIMARY: fld(TERMINATION_FIELD_DEF),
                    SECONDARY: {
                        TERMINATION_IDENTITY_FIELD_DEF: None,
                        TERMINATION_ALIAS_FIELD_DEF: None,
                    },
                    FIELDS: {
                        fld(TERMINATION_FIELD_DEF): None,
                        fld(TERMINATION_IDENTITY_FIELD_DEF): {
                            INV: True,
                            ORD: True,
                        },
                        fld(TERMINATION_ALIAS_FIELD_DEF): {
                            INV: True,
                            ORD: True,
                        },
                    },
                },
                PLAYERTYPE_FILE_DEF: {
                    DDNAME: "PLAYTYPE",
                    FILE: dptfn(PLAYERTYPE_FILE_DEF),
                    FILEDESC: {
                        BRECPPG: 80,
                        FILEORG: RRN,
                    },
                    BTOD_FACTOR: 2.0,
                    BTOD_CONSTANT: 50,
                    DEFAULT_RECORDS: 400,
                    DEFAULT_INCREASE_FACTOR: 0.01,
                    PRIMARY: fld(PLAYERTYPE_FIELD_DEF),
                    SECONDARY: {
                        PLAYERTYPE_IDENTITY_FIELD_DEF: None,
                        PLAYERTYPE_ALIAS_FIELD_DEF: None,
                    },
                    FIELDS: {
                        fld(PLAYERTYPE_FIELD_DEF): None,
                        fld(PLAYERTYPE_IDENTITY_FIELD_DEF): {
                            INV: True,
                            ORD: True,
                        },
                        fld(PLAYERTYPE_ALIAS_FIELD_DEF): {
                            INV: True,
                            ORD: True,
                        },
                    },
                },
            }
        )
