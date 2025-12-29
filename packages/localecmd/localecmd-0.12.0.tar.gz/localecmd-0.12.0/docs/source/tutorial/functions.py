import turtle

from localecmd import programfunction
from localecmd.cli import CLI, run_script
from localecmd.localisation import get_translations

DOMAIN = 'messages'


def _(msgid: str) -> str:
    "Gettext for message domain."
    return get_translations().dgettext(DOMAIN, msgid)


@programfunction()
def forward(*args: int):
    'Move the turtle forward by the specified distance:  FORWARD 10'
    turtle.forward(*args)


@programfunction()
def right(*args: int):
    'Turn turtle right by given number of degrees:  RIGHT 20'
    turtle.right(*args)


@programfunction()
def left(*args: int):
    'Turn turtle left by given number of degrees:  LEFT 90'
    turtle.left(*args)


@programfunction()
def goto(*args: int):
    'Move turtle to an absolute position with changing orientation.  GOTO 100 200'
    turtle.goto(*args)


@programfunction()
def home():
    'Return turtle to the home position:  HOME'
    turtle.home()


@programfunction()
def circle(*args: int):
    'Draw circle with given radius an options extent and steps:  CIRCLE 50'
    turtle.circle(*args)


@programfunction()
def position():
    'Print the current turtle position: POSITION'
    pos = (int(p) for p in turtle.position())
    print(_('Current position is {0} {1}\n').format(*pos))


@programfunction()
def heading():
    'Print the current turtle heading in degrees:  HEADING'
    print(_('Current heading is {0}\n').format(int(turtle.heading())))


@programfunction()
def reset():
    'Clear the screen and return turtle to center:  RESET'
    turtle.reset()


@programfunction()
def bye():
    'Stop recording, close the turtle window, and exit:  BYE'
    print(_('Thank you for using Turtle'))
    turtle.bye()
    raise SystemExit


@programfunction()
def playback(from_line: int, to_line: int = -1):
    "Rerun all commands between two line numbers"
    cli = CLI.get_cli()

    run_script('\n'.join(cli.cmdlog.get(from_line + 1, to_line)))
