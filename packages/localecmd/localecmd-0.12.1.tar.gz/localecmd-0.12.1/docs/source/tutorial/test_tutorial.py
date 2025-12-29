import contextlib
import importlib
import logging
import os
import subprocess
import sys
import turtle

from localecmd import builtins
from localecmd.cli import CLI, restart_cli

# Load functions from tutorial directory
this_dir = os.path.split(__file__)[0]
sys.path.append(this_dir)
print(sys.path)
functions = importlib.import_module('functions')
DOMAIN = functions.DOMAIN
sys.path.remove(this_dir)
# -> tuple[list[str], list[str]]:

logger = logging.getLogger(__name__)

localedir = os.path.join(this_dir, 'locale')

# Convert to -mo files
babel = sys.executable + ' -m babel.messages.frontend compile'
domains = ['cli_functions', 'cli_types', 'cli_messages', 'messages']
langs = ['en_GB', 'de_DE']
for d in domains:
    for lan in langs:
        args = f'-l {lan} -d {localedir} -D {d}'
        subprocess.run([*babel.split(), *args.split()])  # noqa: S603 # No user input


def _test_script(cli: CLI, script: str, capsys):
    # Split into command+answer
    ca = script.split(cli.prompt)
    # capsys.readouterr().out

    assert capsys.readouterr().out == ca[0]

    for _i, s in enumerate(ca[1:]):
        cmd, ans = s.split('\n', maxsplit=1)
        logger.debug(cmd)
        with contextlib.suppress(SystemExit):  # Quit command should not stop testing here
            cli.runcmd(cmd)
        assert capsys.readouterr().out.split() == ans.split()


def _test_scripts(cli: CLI, capsys):
    capsys.readouterr().out  # noqa: B018 # Remove printed stuff
    files = ['turtle1.txt', 'turtle2.txt', 'turtle3.txt']
    sys.path.append(this_dir)  # To find locale files
    for filename in files:
        # Force-start turtle
        with contextlib.suppress(turtle.Terminator):
            turtle.Turtle()

        turtle.delay(0)  # Speed up tests
        # Load script
        with open(os.path.join(this_dir, filename)) as file:
            script = ''.join(file.readlines())
        # Restart cli to get rid of double or missing startup messages
        cli = restart_cli(
            cli.modules.copy(),
            greeting=cli.greeting,
            localedir=localedir,
            gettext_domains=[DOMAIN],
            use_file_docstrings=True,
        )
        # Run script
        print(cli.greeting)  # Simulate cmdloop
        _test_script(cli, script, capsys)

    sys.path.remove(this_dir)  # To not clutter system path


def test_main(capsys):
    modules = [functions, builtins]
    greeting = "Welcome to the turtle shell. Type help to list commands."
    cli = CLI(modules, greeting=greeting, gettext_domains=[DOMAIN], use_file_docstrings=True)
    _test_scripts(cli, capsys)
    cli.close()
    assert not CLI.running
