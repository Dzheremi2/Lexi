from typing import TextIO

import yaml
from gi.repository import Adw, Gtk

from lexi import shared


@Gtk.Template(resource_path=shared.PREFIX + "/gtk/ui/LexiconRow.ui")
class LexiconRow(Gtk.Box):
    """Lexicon row widget

    Parameters
    ----------
    file : TextIO
        The file to load the lexicon from.
    """

    __gtype_name__ = "LexiconRow"

    add_word_dialog: Adw.Dialog = Gtk.Template.Child()
    word_entry_row: Adw.EntryRow = Gtk.Template.Child()
    translation_entry_row: Adw.EntryRow = Gtk.Template.Child()
    example_entry_row: Adw.EntryRow = Gtk.Template.Child()

    title: Gtk.Label = Gtk.Template.Child()

    def __init__(self, file: TextIO) -> None:
        super().__init__()
        self.file: TextIO = open(file, "r+")
        self.data: dict = yaml.safe_load(self.file)
        self.title.set_label(self.data["name"])

    def save_lexicon(self) -> None:
        """Save the lexicon to the file."""
        self.file.seek(0)
        self.file.truncate(0)
        yaml.dump(
            self.data, self.file, sort_keys=False, encoding=None, allow_unicode=True
        )

    def show_add_word_dialog(self) -> None:
        """Shows the add word dialog"""
        self.word_entry_row.set_text("")
        self.word_entry_row.remove_css_class("error")
        self.translation_entry_row.set_text("")
        self.example_entry_row.set_text("")
        self.add_word_dialog.present(shared.win)
        self.add_word_dialog.grab_focus()

    @Gtk.Template.Callback()
    def add_word(self, *_args) -> None:
        """Adds a new word to the lexicon

        Raises
        ------
        AttributeError
            Raised if the `Word` field is empty
        """
        word = self.word_entry_row.get_text()
        translation = self.translation_entry_row.get_text()
        example = self.example_entry_row.get_text()

        if len(word) == 0:
            raise AttributeError("Word cannot be empty")

        if len(translation) == 0:
            translation = []

        if len(example) == 0:
            example = []

        new_word = {
            "id": max((word["id"] for word in self.data["words"]), default=0) + 1,
            "word": word,
            "translations": [translation],
            "pronunciation": "",
            "types": [],
            "examples": example if example == [] else [example],
            "references": [],
        }
        self.data["words"].append(new_word)
        self.save_lexicon()
        shared.win.lexicon_list_box.append(WordRow(new_word, self))
        shared.win.lexicon_scrolled_window.set_child(shared.win.lexicon_list_box)
        shared.win.words_bottom_bar_revealer.set_reveal_child(True)
        self.add_word_dialog.close()

    @Gtk.Template.Callback()
    def check_if_word_is_empty(self, row: Adw.EntryRow) -> None:
        """Applies `error` CSS class to the `Word` row if the field is empty

        Parameters
        ----------
        row : Adw.EntryRow
            Adw.EntryRow to set CSS to
        """
        if len(row.get_text()) == 0:
            row.add_css_class("error")
        else:
            row.remove_css_class("error")

    @property
    def name(self) -> str:
        return self.data["name"]

    @name.setter
    def name(self, name: str) -> None:
        if len(name) == 0:
            raise AttributeError("Lexicon name cannot be empty")

        self.data["name"] = name
        self.save_lexicon()
        self.title.set_label(name)


@Gtk.Template(resource_path=shared.PREFIX + "/gtk/ui/WordRow.ui")
class WordRow(Adw.ActionRow):
    # pylint: disable=line-too-long
    """Word row widget
    Parameters
    ----------
    word : dict
        a dict with the word [id, word, pronunciation, translations, types, examples, references]
    """

    __gtype_name__ = "WordRow"

    check_button: Gtk.CheckButton = Gtk.Template.Child()
    check_button_revealer: Gtk.Revealer = Gtk.Template.Child()

    def __init__(self, word: dict, lexicon: LexiconRow) -> None:
        super().__init__()
        self.lexicon: LexiconRow = lexicon
        self.word_dict: dict = word
        self.set_title(self.word_dict["word"])
        try:
            self.set_subtitle(word["translations"][0])
        except IndexError:
            self.set_subtitle(_("No translation yet"))

        self.rmb_gesture = Gtk.GestureClick(button=3)
        self.long_press_gesture = Gtk.GestureLongPress()
        self.add_controller(self.rmb_gesture)
        self.add_controller(self.long_press_gesture)

        self.rmb_gesture.connect("released", self.do_check_button)
        self.long_press_gesture.connect("pressed", self.do_check_button)

    @Gtk.Template.Callback()
    def load_word(self, *_args) -> None:
        """Loads word to the window"""
        shared.win.loaded_word = self
        shared.win.translations_list_box.remove_all()
        shared.win.examples_list_box.remove_all()
        shared.win.word_entry_row.set_text(self.word)
        shared.win.pronunciation_entry_row.set_text(self.pronunciation)
        for expander_row in (
            (shared.win.translations_expander_row, "translations", _("Translation")),
            (shared.win.examples_expander_row, "examples", _("Example")),
        ):
            for item in self.word_dict[expander_row[1]]:
                row: Adw.EntryRow = Adw.EntryRow(text=item, title=expander_row[2])
                for child in row.get_child():
                    for _item in child:
                        if isinstance(_item, Gtk.Text):
                            _item.connect("changed", self.update_word)
                            _item.connect(
                                "backspace", self.remove_list_prop_on_backspace
                            )
                            break
                expander_row[0].add_row(row)
        if self.word != "":
            shared.win.word_nav_page.set_title(self.word)
        else:
            shared.win.word_nav_page.set_title(_(_msg="Word"))
            self.set_title(_("Word"))

        if shared.win.lexcion_split_view.get_collapsed():
            shared.win.lexcion_split_view.set_show_content(True)

        shared.win.set_word_rows_sensetiveness(True)

    def remove_list_prop_on_backspace(self, text: Gtk.Text) -> None:
        """Removes one line from any expandable row

        Parameters
        ----------
        text : Gtk.Text
            A Gtk.Text to get text from and to get all necessary widgets from
        """
        if text.get_text_length() > 0:
            return

        row = text.get_ancestor(Adw.EntryRow)
        expander_row = row.get_ancestor(Adw.ExpanderRow)

        for attr_name, expander in (
            (attr.replace("_expander_row", ""), getattr(shared.win, attr))
            for attr in dir(shared.win)
            if attr.endswith("_expander_row")
        ):
            if expander is expander_row:
                list_box = getattr(shared.win, attr_name + "_list_box")
                row_index = next(
                    (i for i, _row in enumerate(list_box) if row == _row), None
                )
                if row_index is not None:
                    expander_row.remove(row)
                    del self.word_dict[attr_name][row_index]
                    if shared.schema.get_boolean("word-autosave"):
                        self.lexicon.save_lexicon()
                return

    def update_word(self, text: Gtk.Text) -> None:
        """Updates `self.word_dict` on change in any line from expandable rows

        Parameters
        ----------
        text : Gtk.Text
            A Gtk.Text to get text from and to get all necessary widgets from
        """
        row = text.get_ancestor(Adw.EntryRow)
        expander_row = row.get_ancestor(Adw.ExpanderRow)

        for attr_name, expander in (
            (attr.replace("_expander_row", ""), getattr(shared.win, attr))
            for attr in dir(shared.win)
            if attr.endswith("_expander_row")
        ):
            if expander is expander_row:
                list_box = getattr(shared.win, attr_name + "_list_box")
                row_index = next(
                    (i for i, _row in enumerate(list_box) if row == _row), None
                )
                if row_index is not None:
                    self.word_dict[attr_name][row_index] = row.get_text()
                    try:
                        shared.win.loaded_word.set_subtitle(
                            self.word_dict["translations"][0]
                        )
                    except IndexError:
                        self.set_subtitle(_("No translation yet"))
                    if shared.schema.get_boolean("word-autosave"):
                        self.lexicon.save_lexicon()
                return

    def add_list_prop(self, button: Gtk.Button) -> None:
        """Adds a new line to any expandable row

        Parameters
        ----------
        button : Gtk.Button
            A Gtk.Button to get all necessery widgets from
        """
        expander_row: Adw.ExpanderRow = button.get_ancestor(Adw.ExpanderRow)

        for attr_name, expander in (
            (attr.replace("_expander_row", ""), getattr(shared.win, attr))
            for attr in dir(shared.win)
            if attr.endswith("_expander_row")
        ):
            if expander is expander_row:
                new_row: Adw.EntryRow = Adw.EntryRow(
                    title=(
                        _("Translation")
                        if attr_name == "translations"
                        else _("Example")
                    )
                )
                for child in new_row.get_child():
                    for _item in child:
                        if isinstance(_item, Gtk.Text):
                            text = _item
                            break
                expander_row.add_row(new_row)
                self.word_dict[attr_name].append("")
                text.connect("changed", self.update_word)
                text.connect("backspace", self.remove_list_prop_on_backspace)
                if shared.schema.get_boolean("word-autosave"):
                    self.lexicon.save_lexicon()
                return

    def delete(self) -> None:
        """Deletes a word from the lexicon"""
        self.lexicon.data["words"].remove(self.word_dict)
        shared.win.lexicon_list_box.remove(self)
        if shared.win.loaded_word is self:
            shared.win.word_nav_page.set_title(_("Word"))
            shared.win.word_entry_row.set_text("")
            shared.win.pronunciation_entry_row.set_text("")
            shared.win.translations_list_box.remove_all()
            shared.win.examples_list_box.remove_all()
            shared.win.references_list_box.remove_all()
        shared.win.loaded_word = None
        self.lexicon.save_lexicon()

    def do_check_button(self, *_args) -> None:
        """Toggle `self.check_button` visibility on RMB click or long press"""
        if not self.check_button_revealer.get_reveal_child():
            shared.win.selection_mode_toggle_button.set_active(True)
            self.check_button.set_active(True)
        else:
            self.check_button.set_active(not self.check_button.get_active())

    @Gtk.Template.Callback()
    def on_check_button_toggled(self, button: Gtk.CheckButton) -> None:
        """Adds `self` to the `shared.win.selected_rows` for future deletion

        Parameters
        ----------
        button : Gtk.CheckButton
            A Gtk.CheckButton to decide to remove or add
        """
        if button.get_active():
            shared.win.selected_words.append(self)
        else:
            shared.win.selected_words.remove(self)

    @property
    def word(self) -> str:
        return self.word_dict["word"]

    @word.setter
    def word(self, word: str) -> None:
        self.word_dict["word"] = word
        self.set_title(word)
        if word != "":
            shared.win.word_nav_page.set_title(word)
        else:
            shared.win.word_nav_page.set_title(_("Word"))
            self.set_title(_("Word"))

        if shared.schema.get_boolean("word-autosave"):
            self.lexicon.save_lexicon()

    @property
    def pronunciation(self) -> str:
        return self.word_dict["pronunciation"]

    @pronunciation.setter
    def pronunciation(self, pronunciation: str) -> None:
        self.word_dict["pronunciation"] = pronunciation

        if shared.schema.get_boolean("word-autosave"):
            self.lexicon.save_lexicon()
