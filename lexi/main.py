import os
import sys

import gi
import yaml

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# pylint: disable=wrong-import-position, wrong-import-order
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from lexi import enums, shared
from lexi.logging.logger import log_filename, log_system_info, logger, prev_log_filename
from lexi.utils.backend import LexiconController
from lexi.window import LexiWindow


class LexiApplication(Adw.Application):
    """Application class"""

    win: LexiWindow

    def __init__(self) -> None:
        super().__init__(
            application_id=shared.APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )
        theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        theme.add_resource_path(shared.PREFIX + "/data/icons")

    # pylint: disable=unused-variable
    def do_activate(self) -> None:  # pylint: disable=arguments-differ
        """Action emitted on app launch"""

        logger.info("Creating application window")
        win = self.props.active_window  # pylint: disable=no-member
        if not win:
            shared.win = LexiWindow(application=self)
            # generate_table()

        self.create_actions(
            {
                # fmt: off
                ("quit", ("<primary>q","<primary>w",),),
                ("toggle_sidebar", ("F9",), shared.win),
                ("show_preferences", ("<primary>comma",), shared.win),
                ("add_word", ("<primary>n",), shared.win),
                ("search", ("<primary>f",), shared.win),
                ("reload_words_list", ("F5",), shared.win),
                ("about", )
                # fmt: on
            }
        )
        self.set_accels_for_action("win.show-help-overlay", ("<primary>question",))

        sort_method = Gio.SimpleAction.new_stateful(
            "sort_method",
            GLib.VariantType.new("s"),
            sorting_method := GLib.Variant(
                "s", shared.state_schema.get_string("sort-method")
            ),
        )
        sort_method.connect("activate", shared.win.on_sorting_method_changed)
        shared.win.add_action(sort_method)

        sort_type = Gio.SimpleAction.new_stateful(
            "sort_type",
            GLib.VariantType.new("s"),
            sorting_type := GLib.Variant(
                "s", shared.state_schema.get_string("sort-type")
            ),
        )
        sort_type.connect("activate", shared.win.on_sorting_type_changed)
        shared.win.add_action(sort_type)

        shared.state_schema.bind(
            "window-width", shared.win, "default-width", Gio.SettingsBindFlags.DEFAULT
        )
        shared.state_schema.bind(
            "window-height", shared.win, "default-height", Gio.SettingsBindFlags.DEFAULT
        )
        shared.state_schema.bind(
            "window-maximized", shared.win, "maximized", Gio.SettingsBindFlags.DEFAULT
        )

        shared.win.present()

    def on_quit_action(self, *_args) -> None:
        self.quit()

    def do_shutdown(self):  # pylint: disable=arguments-differ
        """Action emitted on app close"""
        logger.info("Saving config file before exit")
        shared.config_file.seek(0)
        shared.config_file.truncate(0)
        yaml.dump(
            shared.config,
            shared.config_file,
            sort_keys=False,
            encoding=None,
            allow_unicode=True,
        )
        if enums.Schema.SAVE_ON_EXIT():
            logger.info("Saving Lexicons on exit")
            for lexicon in shared.lexictrl:
                lexicon._save()  # pylint: disable=protected-access

    def create_actions(self, actions: set) -> None:
        """Creates actions for provided scope with provided accels

        Args:
            actions (set): Actions in format ("name", ("accels",), scope)

            accels, scope: optional
        """
        for action in actions:
            simple_action = Gio.SimpleAction.new(action[0], None)

            scope = action[2] if action[2:3] else self
            simple_action.connect("activate", getattr(scope, f"on_{action[0]}_action"))

            if action[1:2]:
                self.set_accels_for_action(
                    f"app.{action[0]}" if scope == self else f"win.{action[0]}",
                    action[1],
                )
            logger.debug(
                "Adding action %s with accels %s",
                action[0],
                action[1] if action[1:2] else None,
            )
            scope.add_action(simple_action)

    def on_about_action(self, *_args) -> None:
        """Generates an app about dialog"""

        def get_debug_info() -> str:
            """Get debug info"""
            prev_log = ""
            current_log = open(log_filename, "r", encoding="utf-8").read()
            if os.path.exists(prev_log_filename):
                with open(prev_log_filename, "r", encoding="utf-8") as f:
                    prev_log = f.read()

            return f"PREVIOUS RUN LOG\n\n{prev_log}\n\nCURRENT RUN LOG\n\n{current_log}"

        dialog = Adw.AboutDialog.new_from_appdata(
            shared.PREFIX + "/" + shared.APP_ID + ".metainfo.xml", shared.VERSION
        )
        dialog.set_developers(
            (
                "Dzheremi https://github.com/Dzheremi2",
                "JoseBritto https://github.com/JoseBritto",
            )
        )
        dialog.set_designers(("Dzheremi https://github.com/Dzheremi2",))
        # Translators: Add Your Name, Your Name <your.email@example.com>, or Your Name https://your-site.com for it to show up in the About dialog. PLEASE, DON'T DELETE PREVIOUS TRANSLATORS CREDITS AND SEPARATE YOURSELF BY NEWLINE `\n` METASYMBOL
        dialog.set_translator_credits(_("translator-credits"))
        dialog.set_copyright("© 2025 Dzheremi")
        dialog.add_acknowledgement_section(
            _("Inspiration"),
            ("heliguy4599 (Warehouse) https://github.com/flattool/warehouse",),
        )
        dialog.add_credit_section(
            "Others", ("Memorado https://github.com/wbernard/Memorado",)
        )
        dialog.add_acknowledgement_section(
            _("Advisers"),
            (
                "rezatester94 https://github.com/rezatester94",
                "hellpe https://github.com/hellpe",
            ),
        )
        dialog.add_other_app(
            "io.github.dzheremi2.lrcmake-gtk",
            # Translators: This is the name of the another app https://flathub.org/apps/io.github.dzheremi2.lrcmake-gtk
            _("Chronograph"),
            # Translators: This is the summary of the another app https://flathub.org/apps/io.github.dzheremi2.lrcmake-gtk
            _("Sync lyrics of your loved songs"),
        )
        dialog.set_debug_info(get_debug_info())
        dialog.set_debug_info_filename("lexi.log")
        if shared.PREFIX.endswith("Devel"):
            dialog.set_version("Devel")

        logger.debug("Showing about dialog")
        dialog.present(shared.win)


def main(_version):
    """App entrypint"""
    # Check if lexicons dir exists, create it if not
    try:
        log_system_info()
    except ValueError:
        pass

    if not os.path.exists(os.path.join(shared.data_dir, "lexicons")):
        logger.info("Creating lexicons directory")
        os.mkdir(os.path.join(shared.data_dir, "lexicons"))

    # Check if config.yaml exists, create it if not
    if not os.path.exists(os.path.join(shared.data_dir, "config.yaml")):
        with open(os.path.join(shared.data_dir, "config.yaml"), "x+") as f:
            logger.info("Creating config.yaml file")
            yaml.dump(
                {
                    "word-types": [],
                    "enabled-types": [],
                    "version": shared.CACHEV,
                },
                f,
                sort_keys=False,
                encoding=None,
                allow_unicode=True,
            )

    # Load config file and config dict to the shared data
    logger.info("Loading config")
    shared.config_file = open(
        os.path.join(shared.data_dir, "config.yaml"), "r+", encoding="utf-8"
    )
    shared.config = yaml.safe_load(shared.config_file)

    # Migrate config file and lexicons to newer versions if their structure has changed
    if shared.config["version"] < shared.CACHEV:
        logger.info("Migrating database version to v%s", shared.CACHEV)
        # pylint: disable=import-outside-toplevel
        from lexi.utils import migrator

        current_version = shared.config["version"]
        target_version = shared.CACHEV

        while current_version < target_version:
            next_version = current_version + 1
            migrator_function_name = f"migrate_v{next_version}"

            if hasattr(migrator, migrator_function_name):
                migrator_function = getattr(migrator, migrator_function_name)
                migrator_function()
                current_version = next_version
            else:
                raise ValueError(
                    f"Migrator function {migrator_function_name} not found"
                )

    shared.app = app = LexiApplication()
    shared.lexictrl = LexiconController()

    return app.run(sys.argv)
