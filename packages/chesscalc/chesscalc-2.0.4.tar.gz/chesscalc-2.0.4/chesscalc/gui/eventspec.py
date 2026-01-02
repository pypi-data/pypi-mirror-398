# eventspec.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess Performance Calculation event name and tk(inter) event values."""


class EventSpec:
    """Event detail values for ChessTab keyboard and pointer actions."""

    # ButtonPress event definitions.
    control_buttonpress_1 = ("<Control-ButtonPress-1>", "", "")
    control_buttonpress_3 = ("<Control-ButtonPress-3>", "", "")
    shift_buttonpress_1 = ("<Shift-ButtonPress-1>", "", "")
    shift_buttonpress_3 = ("<Shift-ButtonPress-3>", "", "")
    alt_buttonpress_1 = ("<Alt-ButtonPress-1>", "", "")
    alt_buttonpress_3 = ("<Alt-ButtonPress-3>", "", "")
    buttonpress_1 = ("<ButtonPress-1>", "", "")
    buttonpress_3 = ("<ButtonPress-3>", "", "")

    # Menubar event definitions.
    # F10 in any window invokes the first menu (probably Database).
    # Alt-x invokes the corresponding menu in the menubar, where x is the
    # underlined character.
    menu_database_open = ("", "Open", "", 0)
    menu_database_new = ("", "New", "", 0)
    menu_database_close = ("", "Close", "", 0)
    menu_database_import = ("", "Import", "", 0)
    menu_database_apply_aliases = ("", "Apply Aliases", "", 0)
    menu_database_export_identities = ("", "Export Identities", "", 0)
    menu_database_mirror_identities = ("", "Mirror Identities", "", 0)
    menu_database_remove_games = ("", "Remove Games", "", 0)
    menu_database_delete = ("", "Delete", "", 0)
    menu_database_quit = ("", "Quit", "", 0)
    menu_player_identify = ("", "Identify Player", "", 0)
    menu_player_name_match = ("", "Player Name Match", "", 0)
    menu_match_players_by_name = ("", "Match Players by Name", "", 0)
    menu_player_break = ("", "Break Selected", "", 0)
    menu_player_split = ("", "Split All", "", 0)
    menu_player_change = ("", "Change Person", "", 0)
    menu_player_export = ("", "Export Person Aliases", "", 0)
    menu_other_event_identify = ("", "Identify Event", "", 0)
    menu_other_event_break = ("", "Break Selected Event", "", 0)
    menu_other_event_split = ("", "Split All Events", "", 0)
    menu_other_event_change = ("", "Change Event Name", "", 0)
    menu_other_event_export_persons = (
        "",
        "Export Event Persons Aliases",
        "",
        0,
    )
    menu_other_time_identify = ("", "Identify Time Control", "", 0)
    menu_other_time_break = ("", "Break Selected", "", 0)
    menu_other_time_split = ("", "Split All", "", 0)
    menu_other_time_change = ("", "Change Time Control Name", "", 0)
    menu_other_mode_identify = ("", "Identify Mode", "", 0)
    menu_other_mode_break = ("", "Break Selected", "", 0)
    menu_other_mode_split = ("", "Split All", "", 0)
    menu_other_mode_change = ("", "Change Mode Name", "", 0)
    menu_other_termination_identify = ("", "Identify Termination", "", 0)
    menu_other_termination_break = ("", "Break Selected", "", 0)
    menu_other_termination_split = ("", "Split All", "", 0)
    menu_other_termination_change = ("", "Change Termination Name", "", 0)
    menu_other_playertype_identify = ("", "Identify Player Type", "", 0)
    menu_other_playertype_break = ("", "Break Selected", "", 0)
    menu_other_playertype_split = ("", "Split All", "", 0)
    menu_other_playertype_change = ("", "Change Player Type Name", "", 0)
    menu_selectors_new = ("", "New Rule", "", 0)
    menu_selectors_show = ("", "Show Rule", "", 0)
    menu_selectors_edit = ("", "Edit Rule", "", 0)
    menu_selectors_insert = ("", "Insert Rule", "", 0)
    menu_selectors_update = ("", "Update Rule", "", 0)
    menu_selectors_delete = ("", "Delete Rule", "", 0)
    menu_selectors_close = ("", "Close Rule", "", 0)
    menu_calculate_calculate = ("", "Calculate", "", 0)
    menu_calculate_save = ("", "Save Calculation", "", 0)
    menu_report_save = ("", "Save Report", "", 0)
    menu_report_close = ("", "Close Report", "", 0)
    menu_help_widget = ("", "Help", "", 0)
