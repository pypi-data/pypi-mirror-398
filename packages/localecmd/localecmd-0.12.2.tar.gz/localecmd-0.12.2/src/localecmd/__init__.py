"""
Module with the typically needed functions which are available as from localecmd import *.

More advanced stuff must be imported directly.
"""

import logging
from typing import Iterable

from localecmd import builtins, pot
from localecmd.cli import CLI, printout
from localecmd.func import Function, programfunction
from localecmd.localisation import N_
from localecmd.module import Module

module_logger = logging.getLogger("localecmd")

__all__ = [
    "start_cli",
    "stop_cli",
    "cmdloop",
    "create_pot",
    "Function",
    "programfunction",
    "printout",
    "Module",
]


def start_cli(
    modules: list,
    language: str = "",
    prompt: str = N_("¤ "),
    greeting: str = "",
    localedir: str = "locale",
    gettext_domains: Iterable[str] = [],
) -> CLI:
    """
    Start command line interface with builtin functions.

    Loads correctly decorated function from within the modules. Modules must be
    prepared [as described](#add-functions-to-cli).

    Help and quit functions are built in to the CLI, but may be overwritten.

    :param list modules: List of modules to load functions from.
    :param str language: What language the console is in.
    :param str prompt: What to show when querying for input. Defaults to
    the generic currency sign "¤ " which also is a translatable string.
    :param str greeting: Message to show when starting the CLI
    :param str localedir: Directory where translation files for
    the program are.
    :param Iterable[str] gettext_domains: Gettext domains that are used
    in addition to those provided by localecmd.
    Their language will be changed along with the localecmd domains.
    """

    # Remove double modules
    module_set = set(modules)
    # Add builtins
    module_set.add(builtins)
    cli = CLI(
        list(module_set),
        language,
        prompt,
        greeting,
        localedir,
        gettext_domains=gettext_domains,
    )
    return cli


def stop_cli() -> None:
    """
    Stop CLI from running and turn it off.

    If no CLI is running, this function does nothing.

    You may also use {py:meth}`cli.close`
    """
    if CLI.running:
        cli: CLI = CLI.get_cli()
        cli.close()


def cmdloop() -> None:
    """
    Start a loop querying user for commands.

    The loop stops when python builtin `input` raises `EOFError` or
    when a function raises `SystemExit`.

    You may also use {py:meth}`cli.cmdloop`

    """
    cli: CLI = CLI.get_cli()
    cli.cmdloop()


def create_pot(
    modules: list,
    localedir: str = 'locale',
    *,
    project: str = "",
    version: str = "0.1.0",
    address: str = "user@example.com",
    include_builtins: bool = True,
) -> None:
    """
    Generate alle three pot files for translating localecmd programs.

    File are exported to local 'locale' folder.

    :param list modules: List of modules to load functions from. Names of functions, parameters and
    types in these modules are used to generate the translation files.
    :param str, optional localedir: In which directory to save the .pot file. Default is 'locale'
    :param str, optional project: Project name, defaults to ""
    :param str, optional version: Project version, defaults to "0.1.0"
    :param str, optional address: Where to report translation problems,
    defaults to "user@example.com"
    :param bool, optional include_builtins: If builtin functions (module localecmd.builtins) should
    be added to module list. Defaults to True.

    """
    # Remove double modules
    module_set = set(modules)
    # Add builtins
    if include_builtins:
        module_set.add(builtins)
    CLI(list(module_set), localedir=localedir)
    function_list = list(CLI.functions.values())
    pot.create_functions_pot(function_list, localedir, project, version, address)
    pot.create_messages_pot(localedir, project, version, address)
    pot.create_types_pot(function_list, localedir, project, version, address)
    stop_cli()
