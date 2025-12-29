
# localecmd documentation
Localecmd is a command-line interpreter like 
[cmd](https://docs.python.org/3/library/cmd.html) 
and [cmd2](https://cmd2.readthedocs.io/en/stable/), 
but where command and parameter names can switch into your language. 

It uses [babel](https://babel.pocoo.org/) and 
[gettext](https://www.gnu.org/software/gettext/) to translate all relevant strings. 


:::{toctree}
:maxdepth: 2
:caption: Contents:

Main page <self>
tutorial
features
contribution
API documentation <apidocs/localecmd/localecmd>
changelog
:::

## Quickstart
Create virtual development environment and install package. 
:::{code} bash
python3 -m venv testing-localecmd
pip install localecmd
:::
Then in python interpreter
:::{code} python
>>> from localecmd import programfunction, start_cli
>>> from localecmd.module import Module

>>> @programfunction()
... def hello_world():
...     print("Hello, world!")
...

>>> functions = Module('functions', [hello_world])

>>> cli = start_cli([functions])
The language of the command line is fallback language
>>> cli.runcmd("help")
... # doctest: +SKIP
This will show a list of all available function, including `hello_world`.

>>> cli.runcmd("hello_world")
Hello, world!

>>> cli.close()
    
:::

