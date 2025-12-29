#!/usr/bin/env python3
import os
import tempfile

import pytest
from babel.messages.catalog import Catalog
from babel.messages.mofile import write_mo

from localecmd import builtins
from localecmd.cli import CLI
from localecmd.localisation import DOMAIN_LIST


def test_help(capsys):
    # Start CLI first, if not done already
    assert not CLI.running
    cli = CLI([builtins])

    # Startup messages
    capsys.readouterr().out  # noqa: B018

    builtins.help()
    help_words = capsys.readouterr().out.strip()
    helptext = """
    Available topics:
    bool
    float
    int
    str
    types
    
    Available commands:
    change_language complete help list_distributors list_languages quit save_commands
    """
    assert help_words.split() == helptext.split()
    assert "help" in help_words
    assert "quit" in help_words

    builtins.help("help")
    assert "help topic" in capsys.readouterr().out.strip()

    builtins.help("aojeg")
    assert capsys.readouterr().out.strip() == "Command aojeg does not exist!"

    builtins.help('float')
    assert capsys.readouterr().out.strip().startswith('Float')

    cli.close()


def test_quit():
    with pytest.raises(SystemExit):
        builtins.quit()


def create_mo(domain, lang, folder):
    catalog = Catalog()
    # Bad style. Should remove lang from calling, but want to be flexible
    assert lang == "de_DE"
    catalog.add("help", "hilfe", context="builtins", locations=[("test.py", 42)])
    catalog.add("quit", "schließen", context="builtins", locations=[("test.py", 815)])

    path = os.path.join(folder, lang, "LC_MESSAGES")
    os.makedirs(path, exist_ok=True)

    filename = os.path.join(path, domain + ".mo")
    print(filename)

    with open(filename, "wb") as mo:
        write_mo(mo, catalog)


def test_change_language():
    # Create temporary localisation file
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdirname = tempfile.TemporaryDirectory().name
        print(tmpdirname)
        lang = "de_DE"
        # Must have all three to enable translation
        for domain in DOMAIN_LIST:
            create_mo(domain, lang, tmpdirname)

        # Start CLI first, if not done already
        cli = CLI([builtins], localedir=tmpdirname)

        assert "help" in cli.functions
        assert "hilfe" not in cli.functions

        assert cli.language == ''

        builtins.change_language("de_DE")

        assert "help" not in cli.functions
        assert "hilfe" in cli.functions

        assert cli.language == 'de_DE'

        # Should not change anything
        builtins.change_language("abc")

        assert "help" not in cli.functions
        assert "hilfe" in cli.functions

        assert cli.language == 'de_DE'

        # Must change back for other tests to work.
        builtins.change_language("")

    cli.close()


def test_list_languages(capsys):
    # Start CLI first, if not done already
    # if CLI.running:
    #     cli = CLI.get_cli()
    #     cli.close()
    cli = CLI([builtins])
    builtins.list_languages()
    printed = capsys.readouterr().out
    assert 'fallback' in printed  # Cant really expect more...
    cli.close()


def test_list_distributors(capsys):
    cli = CLI([builtins])
    builtins.list_distributors()
    printed = capsys.readouterr().out
    assert 'change' in printed
    assert 'change_language' in printed
    assert 'list' in printed
    assert 'list_distributors' in printed
    assert 'list_languages' in printed
    assert 'help' not in printed
    cli.close()


def test_complete(capsys):
    cli = CLI([builtins])
    capsys.readouterr().out  # noqa: B018

    builtins.complete('complet')
    assert capsys.readouterr().out == 'complete\n'

    builtins.complete('l l')
    assert capsys.readouterr().out == 'list_languages\n'

    builtins.complete('l')
    strs = [
        "list_ could be completed to ['list_distributors', 'list_languages']",
        "Command incomplete: list\n",
    ]
    assert capsys.readouterr().out == '\n'.join(strs)

    cli.close()


def test_save_commands(tmp_path):
    cli = CLI([builtins])

    tmpfile = tmp_path / 'text.txt'
    tmpfile2 = tmp_path / 'text2.txt'

    cli.runcmd('help')
    cli.runcmd('help me')
    cli.runcmd(f'save_commands {tmpfile}')
    cli.runcmd(f'save_commands {tmpfile2}')

    assert tmpfile.read_text('utf8') == '\nhelp\nhelp me'
    txt = tmpfile2.read_text('utf8')
    assert txt.startswith('\nhelp\nhelp me\nsave_commands ')
    assert txt.endswith('/text.txt')

    with pytest.raises(OSError):
        builtins.save_commands(str(tmpfile))
    with pytest.raises(OSError):
        # Do NOT create this folder on HDD for real or the test will break
        builtins.save_commands(str(tmp_path / 'this folder should not exist' / 'txt.txt'))

    cli.close()
