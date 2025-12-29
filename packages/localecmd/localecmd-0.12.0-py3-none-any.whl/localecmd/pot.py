"""
Functions to generate .pot file with translation template strings of functions
and parameters in the CLI.
"""

from __future__ import annotations

import inspect
import logging
import os
from types import UnionType
from typing import Any, Union, get_args, get_origin

from babel.messages.catalog import Catalog
from babel.messages.extract import extract_from_dir
from babel.messages.pofile import write_po

from localecmd.func import Function
from localecmd.localisation import (
    CLI_DOMAIN,
    DEFAULT_LOCALE_DIR,
    FUNCTION_DOMAIN,
    TYPE_DOMAIN,
)
from localecmd.parsing import KEYWORD, KEYWORDS

module_logger = logging.getLogger("pot")


def _save_catalog(catalog: Catalog, domain: str, localedir: str = DEFAULT_LOCALE_DIR) -> None:
    """
    Save messages catalog to a file

    :param Catalog catalog: babel messages Catalog containing the messages
    :param str domain: Domain of catalog
    :param str localedir: Directory of the message catalogs,
    defaults to 'locale' (relative to current path)

    """
    filename = os.path.join(localedir, domain + ".pot")
    module_logger.info("Save {domain}.pot file into folder " + localedir)

    with open(filename, "wb") as po:
        write_po(po, catalog)


def create_functions_pot(
    function_list: list[Function],
    localedir: str,
    project_name: str = "",
    version: str = "0.1.0",
    address: str = "user@example.com or gitserver.com/exampleuser/issues",
) -> None:
    """
    Save function and parameter names of currently loaded functions into a cli_functions.pot file

    :param list[Function] function_list: List of functions which should be translated.
    :param str localedir: Into which folder to save the pot file
    :param str project_name: Name of project for .pot file header.
    :param str version: Current version of project for .pot file header.
    :param str address: Where to report problems with translation.
    """
    function_catalog = Catalog(
        project=project_name,
        version=version,
        msgid_bugs_address=address,
    )
    module_logger.info("Creating .pot file of loaded functions")

    for kw in KEYWORDS.values():
        uc = [
            'boolean value',
            "Remember to check accordance with builtins.Bool doc translation",
        ]
        function_catalog.add(kw, context=KEYWORD, user_comments=uc)

    for f in function_list:
        msg = f"Found function {f.name} from module {f.modulename}"
        module_logger.debug(msg)

        # User comments
        uc = ["Function", f.oneliner]
        function_catalog.add(f.name, context=f.modulename, user_comments=uc)

        for param in f.parameters:
            msg = f"Found function parameter {param} from function {f.name}"
            module_logger.debug(msg)

            ctxt = f"{f.modulename}.{f.name}"
            comments = ["Parameter"]  # Insert also parameter docstring here
            function_catalog.add(param, context=ctxt, user_comments=comments)

    _save_catalog(function_catalog, FUNCTION_DOMAIN, localedir)


def create_types_pot(
    function_list: list[Function],
    localedir: str,
    project_name: str = "",
    version: str = "0.1.0",
    address: str = "user@example.com or gitserver.com/exampleuser/issues",
) -> None:
    """
    Save types of currently loaded functions into a cli_types.pot file

    :param list[Function] function_list: List of functions which should be translated.
    :param str localedir: Into which folder to save the pot file
    :param str project_name: Name of project for .pot file header.
    :param str version: Current version of project for .pot file header.
    :param str address: Where to report problems with translation.
    """
    type_catalog = Catalog(
        project=project_name,
        version=version,
        msgid_bugs_address=address,
    )
    # typelist = {}
    module_logger.info("Creating .pot file of parameter types")

    for f in function_list:
        msg = f"Found function {f.name} from module {f.modulename}"
        module_logger.debug(msg)

        sig = inspect.signature(f)

        for param in sig.parameters.values():
            annotation = f.annotations.get(param.name, Any)

            if get_origin(annotation) is Union or get_origin(annotation) is UnionType:
                types = [typ.__name__ for typ in get_args(annotation)]
            else:
                types = [annotation.__name__]
            for typ in types:
                # typelist.add(str(typ))
                line = inspect.getsourcelines(f)[1]
                # autopep8: off
                filename = inspect.getmodule(f.func).__name__  # type: ignore[union-attr]
                # autopep8: on
                type_catalog.add(typ, locations=[(filename, line)])
                msg = f"Found type {typ} in function {f.name}"
                module_logger.debug(msg)

    _save_catalog(type_catalog, TYPE_DOMAIN, localedir)


def create_messages_pot(
    localedir: str,
    project_name: str = "",
    version: str = "0.1.0",
    address: str = "user@example.com or gitserver.com/exampleuser/issues",
) -> None:
    """
    Save messages from the `localecmd` package into cli_messages.pot file

    :param str localedir: Into which folder to save the pot file
    :param str project_name: Name of project for .pot file header.
    :param str version: Current version of project for .pot file header.
    :param str address: Where to report problems with translation.
    """
    folder = os.path.split(__file__)[0]

    catalog = Catalog(
        project=project_name,
        version=version,
        msgid_bugs_address=address,
    )
    for filename, line, message, comments, _context in extract_from_dir(folder):
        loc = (os.path.join('localecmd', filename), line)
        catalog.add(message, locations=[loc], user_comments=comments)
    _save_catalog(catalog, CLI_DOMAIN, localedir)
