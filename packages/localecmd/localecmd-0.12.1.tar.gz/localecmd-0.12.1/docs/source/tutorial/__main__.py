import functions
from functions import DOMAIN, _

from localecmd import CLI, builtins


def main():
    modules = [functions, builtins]
    greeting = _("Welcome to the turtle shell. Type help to list commands.")
    cli = CLI(modules, greeting=greeting, gettext_domains=[DOMAIN], use_file_docstrings=True)
    cli.cmdloop()
    cli.close()


main()
