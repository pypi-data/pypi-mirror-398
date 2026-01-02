# reportmirror.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Display report on verification and morring of imported identities."""

import tkinter

from . import report


class ReportMirror(report.Report):
    """Define widget to display report on mirroring of identities."""

    def __init__(self, master, database):
        """Create the report widget."""
        super().__init__(
            master,
            database,
            "Actions or Problems for Mirroring",
        )

    def populate(self, reportdata):
        """Populate the apply identities report widget from reportdata."""
        identity_report = self._report
        end = tkinter.END
        identity_report.configure(state=tkinter.NORMAL)
        identity_report.delete("1.0", tkinter.END)
        if reportdata.messages_exist:
            identity_report.insert(
                end,
                "".join(
                    (
                        "The update has not been applied: ",
                        "reasons follow the content summary.",
                    )
                ),
            )
        else:
            identity_report.insert(
                end,
                "".join(
                    (
                        "The update has been applied: ",
                        "details of changes follow the content summary.",
                    )
                ),
            )
        identity_report.insert(end, "\n\n")
        self._summary_in_import(reportdata)
        identity_report.insert(end, "\n")
        self._summary_not_on_database(reportdata)
        self._summary_not_identified(reportdata)
        self._summary_identified_as_primary(reportdata)
        self._summary_identified_as_alias(reportdata)
        identity_report.insert(end, "\n")
        for identity in reportdata:
            self.add_identity_detail_to_report(
                identity, reportdata.messages_exist
            )
        identity_report.insert(end, "Report completed.")
        identity_report.insert(end, "\n")
        identity_report.configure(state=tkinter.DISABLED)

    def _summary_in_import(self, reportdata):
        """Populate report widget with not on database summary."""
        identity_report = self._report
        end = tkinter.END
        count = len(reportdata)
        if count == 1:
            identity_report.insert(
                end,
                "There is 1 identity in import.",
            )
        else:
            identity_report.insert(
                end,
                str(count).join(
                    (
                        "There are ",
                        " identities in import.",
                    )
                ),
            )
        identity_report.insert(end, "\n")

    def _summary_not_on_database(self, reportdata):
        """Populate report widget with not on database summary."""
        identity_report = self._report
        end = tkinter.END
        count = len([None for ns in reportdata if ns.not_on_database])
        if count == 1:
            identity_report.insert(
                end,
                "There is 1 identity in import not on database.",
            )
        elif count > 1:
            identity_report.insert(
                end,
                str(count).join(
                    (
                        "There are ",
                        " identities in import not on database.",
                    )
                ),
            )
        else:
            identity_report.insert(
                end,
                "All identities in import are on database.",
            )
        identity_report.insert(end, "\n")

    def _summary_not_identified(self, reportdata):
        """Populate report widget with not identified on database summary."""
        identity_report = self._report
        end = tkinter.END
        count = len([None for ns in reportdata if ns.not_identified])
        if count == 1:
            identity_report.insert(
                end,
                "There is 1 identity in import not identified on database.",
            )
        elif count > 1:
            identity_report.insert(
                end,
                str(count).join(
                    (
                        "There are ",
                        " identities in import not identified on database.",
                    )
                ),
            )
        else:
            identity_report.insert(
                end,
                "All identities in import are identified on database.",
            )
        identity_report.insert(end, "\n")

    def _summary_identified_as_primary(self, reportdata):
        """Populate report widget with without aliases on database summary."""
        identity_report = self._report
        end = tkinter.END
        count = len([None for ns in reportdata if ns.identified_primary])
        if count == 1:
            identity_report.insert(
                end,
                " ".join(
                    (
                        "There is 1 identity in import",
                        "identified on database as primary link.",
                    )
                ),
            )
        elif count > 1:
            identity_report.insert(
                end,
                str(count).join(
                    (
                        "There are ",
                        " ".join(
                            (
                                " identities in import",
                                "identified on database as primary link.",
                            )
                        ),
                    )
                ),
            )
        else:
            identity_report.insert(
                end,
                " ".join(
                    (
                        "There are no identities in import",
                        "identified on database as primary link.",
                    )
                ),
            )
        identity_report.insert(end, "\n")

    def _summary_identified_as_alias(self, reportdata):
        """Populate report widget with aliases only on database summary."""
        identity_report = self._report
        end = tkinter.END
        count = len([None for ns in reportdata if ns.identified_alias])
        if count == 1:
            identity_report.insert(
                end,
                " ".join(
                    (
                        "There is 1 identity in import",
                        "identified on database as alias link.",
                    )
                ),
            )
        elif count > 1:
            identity_report.insert(
                end,
                str(count).join(
                    (
                        "There are ",
                        " ".join(
                            (
                                " identities in import",
                                "identified on database as alias link.",
                            )
                        ),
                    )
                ),
            )
        else:
            identity_report.insert(
                end,
                " ".join(
                    (
                        "There are no identities in import",
                        "identified on database as alias link.",
                    )
                ),
            )
        identity_report.insert(end, "\n")

    def add_identity_detail_to_report(self, identity, errors_exist):
        """Add action or error detail for identity to report."""
        identity_report = self._report
        end = tkinter.END
        if errors_exist:
            if identity.message is None:
                return
            identity_report.insert(end, identity.message)
            identity_report.insert(end, "\n")
            # name is a tuple and gets interpreted by Tcl (I think).
            # The effect looks ok in the Text widget, though 'Python-eyes'
            # wonder why some items look a bit like 'repr(set(...))'.
            identity_report.insert(end, identity.name)
            identity_report.insert(end, "\n")
            identity_report.insert(end, "\n")
            return
        if not identity.identified_alias:
            return
        identity_report.insert(end, "Name becomes aliased identity.")
        identity_report.insert(end, "\n")
        for namemap in identity.identified_alias.values():
            for name in namemap.keys():
                # name is a tuple and gets interpreted by Tcl (I think).
                # The effect looks ok in the Text widget, though 'Python-eyes'
                # wonder why some items look a bit like 'repr(set(...))'.
                identity_report.insert(end, name)
                identity_report.insert(end, "\n")
        identity_report.insert(end, "\n")
