"""Module with methods for `invalidate_sort()` and `invalidate_filter()` methods"""

from gi.repository import Gtk

from lexi import shared
from lexi.logging.logger import logger
from lexi.ui.WordRow import WordRow

import unicodedata

# pylint: disable=no-else-return
def sort_words(row1: WordRow, row2: WordRow) -> int:
    """
    Sort words in the list box based on the selected method and type

    Parameters
    ----------
    row1 : WordRow
        The first word row to compare
    row2 : WordRow
        The second word row to compare

    Returns
    -------
    int
        -1 if row1 < row2, 1 if row1 > row2, 0 if they are equal
    """
    sortable1: str | int
    sortable2: str | int

    if shared.win.sort_type == "word":
        sortable1 = row1.word.word.lower().replace("&rtl", "")
        sortable2 = row2.word.word.lower().replace("&rtl", "")
    elif shared.win.sort_type == "first_trnslt":
        sortable1 = (
            row1.word.translations[0].lower().replace("&rtl", "")
            if row1.word.translations
            else ""
        )
        sortable2 = (
            row2.word.translations[0].lower().replace("&rtl", "")
            if row2.word.translations
            else ""
        )
    else:
        sortable1 = row1.word.ref_count
        sortable2 = row2.word.ref_count

    if shared.win.sort_method == "up":
        if sortable1 > sortable2:
            return 1
        elif sortable1 < sortable2:
            return -1
        else:
            return 0
    else:
        if sortable1 < sortable2:
            return 1
        elif sortable1 > sortable2:
            return -1
        else:
            return 0

def remove_accents(text: str) -> str:
    if shared.schema.get_boolean("accent-insensitive-search"):
        text = unicodedata.normalize("NFD", text)
        return ''.join(character for character in text if not unicodedata.combining(character))
    return text

def filter_words(row: WordRow) -> bool:
    """
    Filter words in the list box based on the search entry text and strict type filters

    Parameters
    ----------
    row : WordRow
        a sortable WordRow

    Returns
    -------
    bool
        True if the word matches both the text and type filters, False otherwise
    """
    text: str = remove_accents(shared.win.lexicon_search_entry.get_text().lower().strip())
    fits_in_filter = set(shared.config["enabled-types"]).issubset(set(row.word.types))
    if not text.startswith("#"):
        try:
            matches_text = (
                text == ""
                or text in remove_accents(row.word.word.lower().replace("&rtl", ""))
            )
            if not matches_text and row.word.translations:
                for translation in row.word.translations:
                    if text in remove_accents(translation.lower().replace("&rtl", "")):
                        matches_text = True
                        break
            logger.debug(
                "Word “%s”, is shown: %s",
                row.word.word,
                matches_text and fits_in_filter,
            )
            return matches_text and fits_in_filter

        except (AttributeError, KeyError):
            logger.debug("An error occurred while filtering word, showing")
            return True
    else:
        text = text.replace(" ", "")
        tags = set(text.split("#")[1:])
        word_tags = set(row.word.tags)
        logger.debug(
            "Word “%s”, is shown: %s",
            row.word.word,
            tags.issubset(word_tags) and fits_in_filter,
        )
        return tags.issubset(word_tags) and fits_in_filter


def filter_lexicons(row: Gtk.ListBoxRow) -> bool:
    """
    Filter lexicons in the list box based on their names

    Parameters
    ----------
    row : Gtk.ListBoxRow
        The row to filter

    Returns
    -------
    bool
        True if the row matches the filter, False otherwise
    """
    try:
        text: str = shared.win.search_entry.get_text().lower()
        filtered: bool = text != "" and not (
            text in row.get_child().lexicon.name.lower()
        )  # pylint: disable=superfluous-parens
        return not filtered
    except AttributeError:
        return True
