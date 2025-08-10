import logging

from gi.repository import Adw, Gio, Gtk

from lexi import enums, shared
from lexi.logging.logger import logger
from lexi.ui.TypeRow import TypeRow
from lexi.utils import backup

gtc = Gtk.Template.Child  # pylint: disable=invalid-name


@Gtk.Template(resource_path=shared.PREFIX + "/gtk/ui/Preferences.ui")
class LexiPreferences(Adw.PreferencesDialog):
    """Lexi preferences dialog"""

    __gtype_name__ = "LexiPreferences"

    save_on_exit_switch_row: Adw.SwitchRow = gtc()
    import_confirmation_dialog: Adw.AlertDialog = gtc()
    available_word_types_scrolled_window: Gtk.ScrolledWindow = gtc()
    available_word_types_list_box: Gtk.ListBox = gtc()
    use_debug_log_switch_row: Adw.SwitchRow = gtc()
    use_accent_insensitive_search_switch_row: Adw.SwitchRow = gtc()

    opened: bool = False

    def __init__(self) -> None:
        super().__init__()
        self.__class__.opened = True
        self.connect("closed", lambda *_: self.set_opened(False))

        shared.schema.bind(
            "use-debug-log",
            self.use_debug_log_switch_row,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )
        shared.schema.bind(
            "save-on-exit",
            self.save_on_exit_switch_row,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )
        shared.schema.bind(
            "accent-insensitive-search",
            self.use_accent_insensitive_search_switch_row,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )

        self.use_debug_log_switch_row.connect(
            "notify::active", self.__set_use_debug_log
        )

        self.gen_word_types()

    @Gtk.Template.Callback()
    def on_export_button_clicked(self, *_args) -> None:
        """
        Handle the export button click event

        Opens a file dialog to save the database backup
        """
        logger.debug("Showing export database dialog")
        dialog = Gtk.FileDialog(initial_name="lexi_backup.zip")
        dialog.save(shared.win, None, self.on_export_database)

    def on_export_database(self, file_dialog: Gtk.FileDialog, result: Gio.Task) -> None:
        """
        Export the database to the selected file path

        Parameters
        ----------
        file_dialog : Gtk.FileDialog
            The file dialog used for selecting the export location
        result : Gio.Task
            The result of the file dialog operation
        """
        path = file_dialog.save_finish(result).get_path()
        logger.info("Exporting database to “%s”", path)
        backup.export_database(path)
        self.close()

    @Gtk.Template.Callback()
    def on_import_button_clicked(self, *_args) -> None:
        """
        Handle the import button click event

        Presents a confirmation dialog before importing a database
        """
        logger.debug("Showing import confirmation dialog")
        self.import_confirmation_dialog.present(shared.win)

    @Gtk.Template.Callback()
    def on_import_confirmation_dialog_response(
        self, _alert_dialog: Adw.AlertDialog, response: str
    ) -> None:
        """
        Handle the response from the import confirmation dialog

        Parameters
        ----------
        _alert_dialog : Adw.AlertDialog
            The alert dialog that emitted this method
        response : str
            The response ID from the dialog
        """
        if response == "import":
            logger.debug("Showing import database dialog")
            dialog = Gtk.FileDialog(
                default_filter=Gtk.FileFilter(mime_types=["application/zip"])
            )
            dialog.open(shared.win, None, self.on_import_database)
        else:
            logger.debug("Import cancelled")

    def on_import_database(self, file_dialog: Gtk.FileDialog, result: Gio.Task) -> None:
        """
        Import the database from the selected file path

        Parameters
        ----------
        file_dialog : Gtk.FileDialog
            The file dialog used for selecting the import file
        result : Gio.Task
            The result of the file dialog operation
        """
        path = file_dialog.open_finish(result).get_path()
        logger.info("Importing database from “%s”", path)
        backup.import_database(path)
        self.close()

    @Gtk.Template.Callback()
    def add_new_word_type(self, entry_row: Adw.EntryRow) -> None:
        """Add a new word type to the list of available word types on Enter press

        Parameters
        ----------
        entry_row : Adw.EntryRow
            Adw.EntryRow to get new word type from
        """
        if (
            not entry_row.get_text() in shared.config["word-types"]
            and entry_row.get_text() != ""
        ):
            logger.info("Adding new word type: %s", entry_row.get_text())
            shared.config["word-types"].append(entry_row.get_text())
            shared.config["word-types"].sort()
            self.gen_word_types()
            entry_row.set_text("")

    @Gtk.Template.Callback()
    def on_export_memorado_button_clicked(self, *_args) -> None:
        logger.debug("Showing export database to Memorado dialog")
        dialog = Gtk.FileDialog(initial_name="lexi_database.db")
        dialog.save(shared.win, None, self.on_export_memorado_database)

    def on_export_memorado_database(
        self, file_dialog: Gtk.FileDialog, result: Gio.Task
    ) -> None:
        path = file_dialog.save_finish(result).get_path()
        logger.info("Exporting database to “%s” as Memorado database", path)
        backup.export_memorado_database(path)
        self.close()

    def __set_use_debug_log(self, *_args) -> None:
        logger.info(
            "Setting logger profile to %s",
            "DEBUG" if self.use_debug_log_switch_row.get_active() else "INFO",
        )
        logger.setLevel(
            logging.DEBUG
            if self.use_debug_log_switch_row.get_active()
            else logging.INFO
        )

    def gen_word_types(self) -> None:
        """Generate the word types list and populate the list box"""
        self.available_word_types_list_box.remove_all()
        if len(shared.config["word-types"]) != 0:
            for word_type in shared.config["word-types"]:
                self.available_word_types_list_box.append(TypeRow(word_type))
            self.available_word_types_scrolled_window.set_child(
                self.available_word_types_list_box
            )
        else:
            self.available_word_types_scrolled_window.set_child(
                Adw.StatusPage(
                    title=_("No word types created yet"),
                    description=_("Add a new word type to get started"),
                    icon_name=enums.Icon.NO_FOUND,
                )
            )

    def set_opened(self, opened: bool) -> None:
        """Allows the existance of only one Preferences dialog at once

        Parameters
        ----------
        opened : bool
            state for the __class__.opened variable
        """
        self.__class__.opened = opened
