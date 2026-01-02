# reportapply.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Display report on verification and application of imported identities."""

import tkinter

from . import report


class ReportApply(report.Report):
    """Define widget to display report on application of identities."""

    def __init__(self, master, database):
        """Create the report widget."""
        super().__init__(
            master,
            database,
            "Actions or Problems for Identifications",
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
        self._summary_all_names_identified(reportdata)
        self._summary_at_least_one_name_not_identified(reportdata)
        self._summary_identified_as_primary_and_alias(reportdata)
        self._summary_identified_as_primary_only(reportdata)
        self._summary_identified_as_aliases_only(reportdata)
        self._summary_no_names_identified_by_primary_or_aliases(reportdata)
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
                "There is 1 set of identities in import.",
            )
        else:
            identity_report.insert(
                end,
                str(count).join(
                    (
                        "There are ",
                        " sets of identities in import.",
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
                "".join(
                    (
                        "There is 1 set of identities in import with ",
                        "no names on database.",
                    )
                ),
            )
        elif count > 1:
            identity_report.insert(
                end,
                str(count).join(
                    (
                        "There are ",
                        "".join(
                            (
                                " sets of identities in import with ",
                                "no names on database.",
                            )
                        ),
                    )
                ),
            )
        else:
            identity_report.insert(
                end,
                "".join(
                    (
                        "All sets of identities in import have at ",
                        "least one name on database.",
                    )
                ),
            )
        identity_report.insert(end, "\n")

    def _summary_all_names_identified(self, reportdata):
        """Populate report widget with not identified on database summary."""
        identity_report = self._report
        end = tkinter.END
        count = len([None for ns in reportdata if not ns.not_identified])
        if count == 1:
            identity_report.insert(
                end,
                " ".join(
                    (
                        "There is 1 set of identities in import",
                        "with all names identified on database.",
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
                                " sets of identities in import",
                                "with all names identified on database.",
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
                        "There are no sets of identities in import with",
                        "all names identified on database.",
                    )
                ),
            )
        identity_report.insert(end, "\n")

    def _summary_at_least_one_name_not_identified(self, reportdata):
        """Populate report widget with not identified on database summary."""
        identity_report = self._report
        end = tkinter.END
        count = len([None for ns in reportdata if ns.not_identified])
        if count == 1:
            identity_report.insert(
                end,
                " ".join(
                    (
                        "There is 1 set of identities in import with",
                        "at least one name not identified on database.",
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
                                " sets of identities in import with at",
                                "least one name not identified on database.",
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
                        "There are no sets of identities in import with",
                        "at least one name identified on database.",
                    )
                ),
            )
        identity_report.insert(end, "\n")

    def _summary_identified_as_primary_and_alias(self, reportdata):
        """Populate report widget with not identified on database summary."""
        identity_report = self._report
        end = tkinter.END
        count = len(
            [
                None
                for ns in reportdata
                if ns.not_identified
                and ns.identified_primary
                and ns.identified_alias
            ]
        )
        if count == 1:
            identity_report.insert(
                end,
                " ".join(
                    (
                        "There is 1 set of identities in import with at",
                        "least one name not identified on database where",
                        "both primary and alias links exist.",
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
                                " sets of identities in import with at",
                                "least one name not identified on database ",
                                "where both primary and alias links exist.",
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
                        "There are no sets of identities in import with at",
                        "least one name not identified on database where",
                        "both primary and alias links exist.",
                    )
                ),
            )
        identity_report.insert(end, "\n")

    def _summary_identified_as_primary_only(self, reportdata):
        """Populate report widget with without aliases on database summary."""
        identity_report = self._report
        end = tkinter.END
        count = len(
            [
                None
                for ns in reportdata
                if ns.not_identified
                and ns.identified_primary
                and not ns.identified_alias
            ]
        )
        if count == 1:
            identity_report.insert(
                end,
                " ".join(
                    (
                        "There is 1 set of identities in import with at",
                        "least one name not identified on database where",
                        "the primary link exists.",
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
                                " sets of identities in import with at",
                                "least one name not identified on database ",
                                "where the primary link exists.",
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
                        "There are no sets of identities in import with at",
                        "least one name not identified on database where",
                        "the primary link exists.",
                    )
                ),
            )
        identity_report.insert(end, "\n")

    def _summary_identified_as_aliases_only(self, reportdata):
        """Populate report widget with aliases only on database summary."""
        identity_report = self._report
        end = tkinter.END
        count = len(
            [
                None
                for ns in reportdata
                if ns.not_identified
                and not ns.identified_primary
                and ns.identified_alias
            ]
        )
        if count == 1:
            identity_report.insert(
                end,
                " ".join(
                    (
                        "There is 1 set of identities in import with at",
                        "least one name not identified on database where",
                        "an alias link exists.",
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
                                " sets of identities in import with at",
                                "least one name not identified on database ",
                                "where an alias link exists.",
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
                        "There are no sets of identities in import with at",
                        "least one name not identified on database where",
                        "an alias link exists.",
                    )
                ),
            )
        identity_report.insert(end, "\n")

    def _summary_no_names_identified_by_primary_or_aliases(self, reportdata):
        """Populate report widget with both on database summary."""
        identity_report = self._report
        end = tkinter.END
        count = len(
            [
                None
                for ns in reportdata
                if ns.not_identified
                and not ns.identified_primary
                and not ns.identified_alias
            ]
        )
        if count == 1:
            identity_report.insert(
                end,
                " ".join(
                    (
                        "There is 1 set of identities in import",
                        "with all names not identified on database.",
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
                                " sets of identities in import with all",
                                "names not identified on database.",
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
                        "There are no sets of identities in import with",
                        "all names not identified on database.",
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
            for name in identity.names:
                # name is a tuple and gets interpreted by Tcl (I think).
                # The effect looks ok in the Text widget, though 'Python-eyes'
                # wonder why some items look a bit like 'repr(set(...))'.
                identity_report.insert(end, name)
                identity_report.insert(end, "\n")
            identity_report.insert(end, "\n")
            return
        if not identity.not_identified:
            return
        if identity.identified_primary:
            identity_report.insert(end, "Names become aliases directly.")
        elif identity.identified_alias:
            identity_report.insert(end, "Names become aliases indirectly.")
        else:
            identity_report.insert(end, "Names become aliases of new person.")
        identity_report.insert(end, "\n")
        for name in identity.not_identified:
            # name is a tuple and gets interpreted by Tcl (I think).
            # The effect looks ok in the Text widget, though 'Python-eyes'
            # wonder why some items look a bit like 'repr(set(...))'.
            identity_report.insert(end, name)
            identity_report.insert(end, "\n")
        identity_report.insert(end, "\n")
