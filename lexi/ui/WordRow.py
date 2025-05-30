from gi.repository import Adw, Gtk

from lexi import enums, shared
from lexi.logging.logger import logger
from lexi.utils.backend import Word

gtc = Gtk.Template.Child  # pylint: disable=invalid-name


@Gtk.Template(resource_path=shared.PREFIX + "/gtk/ui/WordRow.ui")
class WordRow(Adw.ActionRow):
    """Word row class

    Parameters
    ----------
    word : Word
        a Word class object representing one word from the Lexicon
    """

    __gtype_name__ = "WordRow"

    title_label: Gtk.Label = gtc()
    subtitle_label: Gtk.Label = gtc()
    tags_box: Adw.WrapBox = gtc()
    check_button_revealer: Gtk.Revealer = gtc()
    check_button: Gtk.CheckButton = gtc()
    refs_count_label_box: Gtk.Box = gtc()
    refs_count_label: Gtk.Label = gtc()
    tag_alert_dialog: Adw.AlertDialog = gtc()
    tag_alert_dialog_entry: Gtk.Entry = gtc()

    def __init__(self, word: Word) -> "WordRow":
        super().__init__()
        self.word = word
        self.title = word.word.replace("&rtl", "")
        try:
            self.subtitle = word.translations[0].replace("&rtl", "")
        except IndexError:
            self.subtitle = _("No translation yet")

        self.__generate_tag_chips()

        self.word.connect("notify::word", self.__reactivity)
        self.word.connect("tags-changed", self.__reactivity)
        self.word.connect("translations-changed", self.__reactivity)

    @Gtk.Template.Callback()
    def on_add_tag_button_clicked(self, *_args) -> None:
        logger.debug("Showing tag addition alert dialog for “%s”", self.word.word)
        self.tag_alert_dialog_entry.set_text("")
        self.tag_alert_dialog.present(shared.win)
        self.tag_alert_dialog_entry.grab_focus()

    @Gtk.Template.Callback()
    def on_tag_alert_dialog_entry_changed(self, entry: Gtk.Entry) -> None:
        if (
            "#" in entry.get_text()
            or entry.get_text().lower() in self.word.tags
            or " " in entry.get_text().strip()
        ):
            entry.add_css_class("error")
        else:
            if "error" in entry.get_css_classes():
                entry.remove_css_class("error")

    @Gtk.Template.Callback()
    def on_tag_entry_activated(self, *_args) -> None:
        self.on_tag_alert_dialog_response(
            _alert_dialog=self.tag_alert_dialog, response="add"
        )
        self.tag_alert_dialog.close()

    @Gtk.Template.Callback()
    def on_tag_alert_dialog_response(
        self, _alert_dialog: Adw.AlertDialog, response: str
    ) -> None:
        if response == "add":
            tag = self.tag_alert_dialog_entry.get_text().lower().strip()
            if "#" in tag or " " in tag or tag == "":
                logger.warning("Tag cannot contain spaces or '#'")
                raise AttributeError("Tag cannot contain spaces or '#'")

            if tag in self.word.tags:
                logger.warning("Tag already exists")
                raise AttributeError("Tag already exists")

            self.word.add_tag(tag)
            self.__generate_tag_chips()
            logger.info("Tag “#%s” added to “%s”", tag, self.word.word)
        else:
            logger.debug("Tag addition cancelled")

    def __reactivity(self, *_args) -> None:
        self.title = self.word.word.replace("&rtl", "")
        try:
            self.subtitle = self.word.translations[0].replace("&rtl", "")
        except IndexError:
            _("No translation yet")

    def __generate_tag_chips(self) -> None:
        if self.word.tags != []:

            def __clicked(_button: Gtk.Button, tag: str) -> None:
                current_text = shared.win.lexicon_search_entry.get_text()
                if not current_text.startswith("#") and current_text != "":
                    return
                logger.info(
                    "Searching for words with tag “%s”", current_text + f"#{tag}"
                )
                shared.win.lexicon_search_entry.set_text(f"{current_text}#{tag}")

            def __rmb_clicked(
                gesture: Gtk.GestureClick,
                _n_press: int,
                _x: float,
                _y: float,
                tag: str,
            ) -> None:
                widget: Gtk.Button = gesture.get_widget()
                self.word.rm_tag(tag)
                logger.info("Tag “#%s” removed from “%s”", tag, self.word.word)
                self.tags_box.remove(widget)

            while (child := self.tags_box.get_first_child()) is not None:
                self.tags_box.remove(child)

            for tag in self.word.tags:
                button = Gtk.Button(
                    label=f"#{tag}",
                    valign=Gtk.Align.CENTER,
                    css_classes=["pill", "small"],
                    tooltip_text=_(
                        "Click LMB to search words with this tag\nClick RMB to remove this tag"
                    ),
                )
                button.connect("clicked", __clicked, tag)
                rmb = Gtk.GestureClick(button=3)
                rmb.connect("released", __rmb_clicked, tag)
                button.add_controller(rmb)
                self.tags_box.append(button)

    def do_check_button(self, *_args) -> None:
        """Toggle the visibility of the check button"""
        if not self.check_button_revealer.get_reveal_child():
            shared.win.selection_mode_toggle_button.set_active(True)
            self.check_button.set_active(True)
            logger.debug("Check button of “%s” activated", self.word.word)
        else:
            self.check_button.set_active(not self.check_button.get_active())
            logger.debug("Check button of “%s” deactivated", self.word.word)

    @Gtk.Template.Callback()
    def on_check_button_toggled(self, button: Gtk.CheckButton) -> None:
        """Handle toggling of the check button

        Parameters
        ----------
        button : Gtk.CheckButton
            The check button being toggled
        """
        if button.get_active():
            logger.debug("Adding “%s” to deleatable words", self.word.word)
            shared.win.selected_words.append(self)
        else:
            shared.win.selected_words.remove(self)
            logger.debug("Removing “%s” from deletable words", self.word.word)

    def get_ref_count(self) -> None:
        """Update the reference count label"""
        logger.debug("Updating reference count for “%s”", self.word.word)
        if self.word.ref_count > 0:
            self.refs_count_label_box.set_visible(True)
            self.refs_count_label.set_label(str(self.word.ref_count))
        else:
            self.refs_count_label_box.set_visible(False)

    def delete(self) -> None:
        self.word.parent_lexicon.rm_word(self.word.id)
        shared.win.lexicon_list_box.remove(self)
        shared.win.lexicon_list_box.select_row(None)
        if shared.win.lexicon_list_box.get_row_at_index(0) is None:
            shared.win.set_property("state", enums.WindowState.EMPTY_WORDS)

    @property
    def title(self) -> str:
        """The `self` title"""
        return self.title_label.get_label()

    @title.setter
    def title(self, word: str) -> None:
        """The `self` title"""
        self.title_label.set_label(word)

    @property
    def subtitle(self) -> str:
        """The `self` subtitle"""
        return self.subtitle_label.get_label()

    @subtitle.setter
    def subtitle(self, translation: str) -> None:
        """The `self` subtitle"""
        self.subtitle_label.set_label(translation)
