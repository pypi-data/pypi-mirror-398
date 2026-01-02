# constants.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Constants for Chess Performance Calculation database."""

# The PGN tag names used in identifying players and games.

# The Seven Tag Roster with comments on effect for player identification.
TAG_EVENT = "Event"  # Event name: part of player identity.
TAG_SITE = "Site"  # Ignore if possible: part of player identity.
TAG_DATE = "Date"  # Date game played.
TAG_ROUND = "Round"  # Event, section, or stage may have rounds.
TAG_WHITE = "White"  # Name index: part of player identity.
TAG_BLACK = "Black"  # Name index: part of player identity.
TAG_RESULT = "Result"  # Game result.

# Supplemental tags used in identifying players and games.
# These tags are optional but contribute if present.
# 'Open' is a typical 'Section' value.
# 'Semi-final' is a typical 'Stage' value.
TAG_EVENTDATE = "EventDate"  # Event start date: part of player identity.
TAG_SECTION = "Section"  # Playing section: part of player identity.
TAG_STAGE = "Stage"  # Stage of event: part of player identity.
TAG_TIMECONTROL = "TimeControl"  # Formatted desciption of time controls.
TAG_MODE = "Mode"  # 'OTB' for example.

# Supplemental tags which do not affect formal identification of players and
# games but may provide useful context.
TAG_WHITEELO = "WhiteElo"  # FIDE Elo rating.
TAG_BLACKELO = "BlackElo"  # FIDE Elo rating.
TAG_BOARD = "Board"  # Board number (often in round or team).

# Supplemental tags which distinguish types of chess.
TAG_WHITETYPE = "WhiteType"  # Default is "human".
TAG_BLACKTYPE = "BlackType"  # Default is 'human'.
TAG_FEN = "FEN"  # Default is start position of a normal game of chess.
TAG_TERMINATION = "Termination"  # Default is 'normal'.

# Significant values for distinguishing types of chess.
CONSULTATION = ":"  # Consultation game if in White or Black tag values.
HUMAN = "human"  # The player is human (the default) (not a computer).
NORMAL_START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# Significant values for deciding if game is ratable.
DEFAULT_TERMINATION = "default"  # The game was decided by default.
BYE_TERMINATION = "bye"  # The game was declared a bye.
UNKNOWN_VALUE = "?"  # Proper tag value is unknown.
NO_VALUE = "-"  # The tag has no proper value.

# Tags not mentioned in PGN specification but seen in real PGN files.
TAG_WHITEFIDEID = "WhiteFideId"  # FIDE Number: part of player identity.
TAG_BLACKFIDEID = "BlackFideId"  # FIDE Number: part of player identity.
TAG_WHITETEAM = "WhiteTeam"  # Team name: part of player identity.
TAG_BLACKTEAM = "BlackTeam"  # Team name: part of player identity.

# Most recently accessed database and configuation files for selecting and
# extracting game headers from PGN files.
# Some could be per database, but done per user.
RECENT_DATABASE = "database"
RECENT_PGN_DIRECTORY = "pgn_directory"
RECENT_IMPORT_DIRECTORY = "import_directory"

# PGN header values: directory names, non-tag field names and values,
# and regular expression pattern for picking tags.
PGN_TAG_PAIR = rb"".join(
    (
        rb"(?#Start Tag)\[\s*",
        rb"(?#Tag Name)([A-Za-z0-9_]+)\s*",
        rb'(?#Tag Value)"((?:[^\\"]|\\.)*)"\s*',
        rb"(?#End Tag)\]",
    )
)
PGNEXT = ".pgn"
FILE = "file"
GAME = "game"
PGNDIR = "pgn"
PGNHDRDIR = "pgnhdr"
PGNHDREXT = ".pgnhdr"
WIN_DRAW_LOSS = ("1-0", "1/2-1/2", "0-1")
UNKNOWN_RESULT = "*"

# Berkeley DB environment.
DB_ENVIRONMENT_GIGABYTES = 0
DB_ENVIRONMENT_BYTES = 1024000
DB_ENVIRONMENT_MAXLOCKS = 120000  # OpenBSD only.
DB_ENVIRONMENT_MAXOBJECTS = 120000  # OpenBSD only.

# Symas LMMD environment.
LMMD_MINIMUM_FREE_PAGES_AT_START = 20000

# Keys for identity record holding most recently allocated identity code,
PLAYER_IDENTITY_KEY = "playerkey"
EVENT_IDENTITY_KEY = "eventkey"
TIME_IDENTITY_KEY = "timekey"
MODE_IDENTITY_KEY = "modekey"
TERMINATION_IDENTITY_KEY = "terminationkey"
PLAYERTYPE_IDENTITY_KEY = "playertypekey"
