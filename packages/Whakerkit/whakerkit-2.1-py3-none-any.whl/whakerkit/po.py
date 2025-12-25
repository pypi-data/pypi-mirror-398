"""
:filename: whakerkit.po.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The WhakerKit gettext manager for a multi-lingual website.

Copyright (C) 2024-2025 Brigitte Bigi, CNRS
Laboratoire Parole et Langage, Aix-en-Provence, France

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This banner notice must not be removed.

"""

import gettext
import logging
import os

# ---------------------------------------------------------------------------
# Dummy fallback (English by default)
_translation = gettext.NullTranslations()

# ---------------------------------------------------------------------------


def set_language(lang_code):
    """Set the active language for gettext translations."""
    global _translation
    try:
        localedir = os.path.join(os.path.dirname(__file__), "statics", "locale")
        _translation = gettext.translation(
            domain="whakerkit",
            localedir=localedir,
            languages=[lang_code],
            fallback=True
        )
        _translation.install(names=["gettext"])
    except Exception as e:
        logging.error(f"Warning: Failed to load translation for '{lang_code}': {e}")
        _translation = gettext.NullTranslations()
        _translation.install(names=["gettext"])

# ---------------------------------------------------------------------------


# This function will be used as `_()`
def _(text):
    return _translation.gettext(text)

# ---------------------------------------------------------------------------


def get_msg(entry, lang=None):
    """Return the translated message.

    If `lang` is specified, temporarily switch to that language
    for the duration of this translation, then revert to the previous one.

    """
    from whakerkit import sg, set_language, _

    if lang and lang != sg.lang:
        original_lang = sg.lang
        set_language(lang)
        translated = _(entry)
        set_language(original_lang)
        return translated

    return _(entry)
