#!/usr/bin/env python3
"""
Created.

"""

import io
import os
import tempfile

import pytest
from babel.messages.catalog import Catalog
from babel.messages.mofile import write_mo

from localecmd.cli import (
    CLI,
    change_cli_language,
    find_distributor_functions,
    printout,
    restart_cli,
    run_script,
)
from localecmd.func import Function
from localecmd.localisation import (
    CLI_DOMAIN,
    FUNCTION_DOMAIN,
    TYPE_DOMAIN,
    f_,
    get_translations,
)


def test_distributor_finding():
    flist = ["help", "list_cmds", "list_funcs"]
    assert find_distributor_functions(flist) == {"list"}

    # Distributors with more than 1 underscore not implemented
    flist = ["help", "list_cmds", "list_funcs_now", "list_func_later"]
    dist = find_distributor_functions(flist)
    assert dist == {"list"}
    assert "list_funcs" not in dist


def cli_is_off():
    assert not CLI.running
    assert CLI._instance is None
    assert len(CLI.functions) == 0
    assert len(CLI.distributors) == 0
    assert len(CLI.modules) == 0
    assert CLI.language == ""

    with pytest.raises(RuntimeError):
        CLI.get_cli()


def help(*args):  # pragma: no cover  # Placeholder. No need to test
    printout(*args)


def quit():  # pragma: no cover  # Placeholder. No need to test
    raise SystemExit


class test_module_en:
    help = Function(help, "help", f_)
    quit = Function(quit, "quit", f_)


def create_mo(domain, lang, folder):
    catalog = Catalog()
    assert lang == "de_DE"  # Bad style. Should remove lang from calling, but want to be flexible
    catalog.add("help", "hilfe", context="test_module_en", locations=[("testmodule.py", 42)])
    catalog.add(
        "quit",
        "schließen",
        context="test_module_en",
        locations=[("testmodule.py", 815)],
    )

    path = os.path.join(folder, lang, "LC_MESSAGES")
    os.makedirs(path, exist_ok=True)

    filename = os.path.join(path, domain + ".mo")
    print(filename)

    with open(filename, "wb") as mo:
        write_mo(mo, catalog)


class test_module_to:
    help = Function(help, "naʻa_ku_fehuʻ", f_)
    quit = Function(quit, "haʻu_ʻo_kai", f_)


def test_that_cli_is_unique():
    # Test that CLI is off
    cli_is_off()

    # Create temporary localisation file
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdirname = tempfile.TemporaryDirectory().name
        print(tmpdirname)
        lang = "de_DE"
        # Must have all three to enable translation
        for domain in [CLI_DOMAIN, FUNCTION_DOMAIN, TYPE_DOMAIN]:
            create_mo(domain, lang, tmpdirname)

        filename = os.path.join(tmpdirname, lang, "LC_MESSAGES", FUNCTION_DOMAIN + ".mo")
        assert os.path.isfile(filename)

        # Turn it on
        cli = CLI([test_module_en], "", localedir=tmpdirname)
        # See that it is on
        assert CLI.running

        # See that we can't start a second CLI
        assert len(CLI.functions) > 0
        with pytest.raises(RuntimeError):
            CLI([])
        # And see that CLI instance still is the same
        assert CLI._instance is cli

        assert len(CLI.functions) > 0
        assert len(CLI.distributors) >= 0  # Is zero for now
        assert CLI.language == ""

        assert "help" in CLI.functions
        assert "quit" in CLI.functions

        # Close CLI and see that it is off again
        cli.close()
        cli_is_off()

        # Start CLI once again, now in Tongan
        # Turn it on
        cli2 = CLI([test_module_to], "de_DE", localedir=tmpdirname)
        # See that it is on
        assert CLI.running
        # assert CLI._instance is cli
        assert len(CLI.functions) > 0
        assert len(CLI.distributors) >= 0  # Is zero for now
        assert CLI.language == "de_DE"
        assert "help" not in CLI.functions
        assert "quit" not in CLI.functions

        assert "naʻa_ku_fehuʻ" in CLI.functions
        assert "haʻu_ʻo_kai" in CLI.functions

        change_cli_language("")
        # Close CLI and see that it is off again
        cli2.close()
    assert not CLI.running
    cli_is_off()


def test_restart():
    assert not CLI.running
    cli_is_off()
    restart_cli([test_module_en], "")

    assert CLI.running
    assert "help" in CLI.functions
    assert "quit" in CLI.functions

    cli = restart_cli([test_module_to], "")
    assert CLI._instance == cli

    assert cli.running

    assert "help" not in CLI.functions
    assert "quit" not in CLI.functions

    assert "naʻa_ku_fehuʻ" in CLI.functions
    assert "haʻu_ʻo_kai" in CLI.functions
    cli.close()

    assert not CLI.running
    cli_is_off()


def test_runcmd(capsys):
    assert not CLI.running
    cli_is_off()
    cli = CLI([test_module_en], "")

    assert CLI.running
    assert "help" in CLI.functions
    assert "quit" in CLI.functions

    # Test that it works
    cli.runcmd("help 'help'", localed_input=False)
    # Prints a list of functions

    # Testing that failures are handled and do not crash the program
    # Missing end quotation
    cli.runcmd("help 'help", localed_input=False)
    # Missing command - should work and show an message to user
    cli.runcmd("", localed_input=False)

    # Exit on quit – reraise SystemExit
    with pytest.raises(SystemExit):
        cli.runcmd("quit", localed_input=False)
    capsys.readouterr().out  # noqa (B018)

    # error in function
    cli.runcmd("quit now", localed_input=False)  # Quit doesn't take arguments
    assert capsys.readouterr().out.startswith("Error")

    cli.close()
    assert not CLI.running
    cli_is_off()


def test_run_script():
    assert not CLI.running
    cli_is_off()
    cli = CLI([test_module_en], "")

    assert CLI.running
    assert "help" in CLI.functions
    assert "quit" in CLI.functions

    run_script("help\nhelp quit", localed_input=False)
    assert cli.cmdlog.get(1) == ["help", "help quit"]
    assert cli.answers.get(1) == ['\n', 'quit\n']  # These functions do not print
    transcript = "¤ help\n\n¤ help quit\nquit\n"
    assert cli.transcript.get()[0].split('\n', maxsplit=1)[1] == transcript

    cli.close()
    assert not CLI.running
    cli_is_off()


def test_language_change():
    # Test that CLI is off
    cli_is_off()
    with pytest.raises(RuntimeError):
        change_cli_language("abc")

    # Module needs to be named "general" for translations to work.
    # test_module_en.__name__ = "general"

    # Language wqe are testing
    lang = "de_DE"

    # Create temporary localisation file
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdirname = tempfile.TemporaryDirectory().name
        # Must have all three to enable translation
        for domain in [CLI_DOMAIN, FUNCTION_DOMAIN, TYPE_DOMAIN]:
            create_mo(domain, lang, tmpdirname)

        cli = CLI([test_module_en], "", localedir=tmpdirname)

        assert "hilfe" not in CLI.functions
        assert "help" in CLI.functions

        # Test change to German
        change_cli_language(lang)

        translations = get_translations()
        filename = os.path.join(tmpdirname, lang, 'LC_MESSAGES', domain + '.mo')
        assert filename in translations.files

        assert CLI.language == lang
        assert "hilfe" in CLI.functions
        assert "help" not in CLI.functions

        # Test that it works
        cli.runcmd("hilfe 'hilfe'")

        # Test that nothing changes if language does not exist
        change_cli_language("abc")
        assert CLI.language == lang
        assert "hilfe" in CLI.functions
        assert "help" not in CLI.functions

        # Test change to fallback language
        change_cli_language("")
        assert CLI.language == ""
        assert "hilfe" not in CLI.functions
        assert "help" in CLI.functions
        cli.close()


def test_other_stdout(capsys):
    assert capsys.readouterr().out == ''
    cli_is_off()
    stdout = io.StringIO()
    cli = CLI([test_module_en], "", stdout=stdout)
    run_script("help\nhelp quit", localed_input=False)
    cli.close()
    assert capsys.readouterr().out == ''
    assert stdout.getvalue().endswith('quit\n')


def test_printout(capsys):
    cli_is_off()
    txt = 'Hello, world!'
    printout(txt)
    assert capsys.readouterr().out.strip() == txt
