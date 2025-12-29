#!/usr/bin/env python3
from __future__ import annotations

import logging
import os
from collections.abc import Iterable

from babel.support import Translations

module_logger = logging.getLogger(__name__)

# .po file names
# Messages to user
CLI_DOMAIN = "cli_messages"
"What the .po files containing the CLI messages are called"

FUNCTION_DOMAIN = "cli_functions"
"What the .po files with function and parameter names and keywords are called"

TYPE_DOMAIN = "cli_types"
"What the .po files containing the types are called"

DOMAIN_LIST = [CLI_DOMAIN, FUNCTION_DOMAIN, TYPE_DOMAIN]
"List of all domains that are needed to localise localecli"

DEFAULT_LOCALE_DIR = "locale"
"Directory of .po files"


_translations = Translations()
_language = ''


def get_translations():
    return _translations


def get_language() -> str:
    """
    Get language the cli is in.

    In practice, this is the language code that *was asked for*.
    If the corresponding files don't exist, this language differs from that of the messages.
    """
    return _language


def setup_translations(
    languages: list[str],
    localedir: str = DEFAULT_LOCALE_DIR,
    additional_domains: Iterable[str] = [],
) -> None:
    """Check if translations are enabled, else initialise them.

    The domains initialised are the localecmd domains only.

    If the given languages can't be loaded, the fallback is initialised.
    To explicitly setup for fallback language, use empty language ('').

    :param languages: Which language (with fallbacks) to initialise
    :type languages: list[str]
    :param localedir: Where to find the translation files, defaults to DEFAULT_LOCALE_DIR
    :type localedir: str, optional
    :param additional_domains: Domains to setup in addition to the internal ones.

    """
    domains = DOMAIN_LIST + list(additional_domains)
    msg = f"Switching domains {domains} to language {languages}"
    module_logger.debug(msg)
    global _translations, _language

    if languages == ['']:
        _translations = Translations()
        _language = ''

    for domain in domains:
        module_logger.debug(domain)
        # Silently returns NullTranslations if file can't be found
        translation = Translations.load(localedir, languages, domain)
        if not isinstance(translation, Translations) and languages != ['']:
            msg = f"Did not load file for domain {domain} in language {languages}"
            module_logger.warning(msg)
        # Of some reason mypy doesn't like that translation can be NULLTranslations?
        _translations.merge(translation)  # type: ignore[arg-type]

    # Set language to the first chosen language
    _language = languages[0]


def language_list(
    localedir=DEFAULT_LOCALE_DIR,
    *,
    include_fallback: bool = False,
    force_dir: bool = True,
) -> list[str]:
    """Get list of languages that can be used

    The displayable languages are those which have an own folder in locale.

    :param str localedir: Where to find the translation files. Default is 'locale'
    :param bool fallback: If True, the fallback language is included
    in into the list. Default is False.
    :return: list of language codes
    :rtype: list[str]

    """
    if os.path.isdir(localedir):
        codes = [code.name for code in os.scandir(localedir) if code.is_dir()]
        codes.sort()
    else:
        msg = f"Locale directory {localedir!r} is missing."
        module_logger.debug(msg)
        codes = []

    msg = "Available languages: {codes}"
    module_logger.debug(msg)

    if include_fallback:
        codes.insert(0, "")

    return codes


def _(msgid: str) -> str:
    "Gettext for CLI domain ."
    return _translations.dgettext(CLI_DOMAIN, msgid)


def N_(message: str) -> str:
    """Return input string untouched

    Useful for marking strings for translation that are called now, but
    should be translated later.
    """
    return message


def d_(msgid: str) -> str:
    "Gettext for type domain"
    return _translations.dgettext(TYPE_DOMAIN, msgid)


def f_(context: str, msgid: str) -> str:
    "Gettext for function domain"
    # String converstion if for mypy. Apparently babel gcn return object here????
    return str(_translations.dpgettext(FUNCTION_DOMAIN, context, msgid))
