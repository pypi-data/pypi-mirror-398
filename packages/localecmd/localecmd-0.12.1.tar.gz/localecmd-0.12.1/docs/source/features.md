# Features

```{contents} 
:depth: 3
:local:
```

(add-functions-to-cli)=
## Functions
When the CLI is started, the developer has to give a list of modules containing functions.
The CLI will look for {py:class}`localecmd.Function` objects in the modules and load them.

To convert a normal Python function to a {py:class}`localecmd.func.Function`, 
it can be decorated with the {py:func}`localecmd.func.programfunction` decorator including parentheses, for example
:::{code} python
>>> from localecmd import programfunction
>>> @programfunction()
... def hello_world():
...     print("Hello, World!")

:::
For parameter description, see {py:class}`localecmd.func.Function`. 
The {py:class}`localecmd.func.Function` instance can also be initialised directly.

Docstrings are helpful and are displayed by the help function. 
See [helptexts](helptexts) for more guidance.

### Parameters and calling
The parameters of the functions calls behave like normal Python functions.
They are however written as for command-line interpreters.
Name and arguments separated with space. Keyword arguments must be named and have its name after a dash.
For example the CLI calling 
:::{code} bash
some_function lorem ipsum -kwarg 'dolor sit amet'
:::
in Python becomes
:::{code} python
some_function('lorem', 'ipsum', kwarg2='dolor sit amet')
:::
The internal parser breaks the line down:
:::{code} python
>>> from localecmd.parsing import line_to_args
>>> line_to_args("some_function lorem ipsum -kwarg 'dolor sit amet'")[:-1]
('some_function', ['lorem', 'ipsum'], {'kwarg': 'dolor sit amet'})

:::
and then the corresponding Python function is called with those arguments as shown above.

### Argument injection
Localecmd suports to inject positional and keyword arguments when the CLI calls a function.
This can be useful if there are arguments that are present in some module and cannot be typed (easily) as a string.
Simple example would be methods of class instances as these need the `self` argument, 
but this can't be passed from CLI.

To inject the arguments, these must be given on the function after creation
or to the module as whole. If give to the module, these arguments will be given
to all functions in the module.
A class instance can be converted to a module like a python module.

:::{code} python
>>> from localecmd import programfunction, CLI, Module
>>> class HelloGroup():
...     def __init__(self):
...         super().__init__()
...         self.greeting = "Hello, World!" 
...     
...     @programfunction()
...     def hello_world(self):
...         print(self.greeting)
>>> group = HelloGroup()  # Class must be instanced like one would do elsewise
>>> cli = CLI([Module.from_module(group, 'hello', prependargs=[group])])
The language of the command line is fallback language
>>> cli.runcmd("hello world")
Hello, World!
>>> cli.close()

:::
::::{important}
The inserted arguments are not injected when calling the function directly.
When called from CLI, the arguments are inserted with
{py:meth}`~localecmd.func.Function.substitute_call` before calling the actual function.
For calling the function otherwise, all arguments must be given:

:::{code} python
>>> group.hello_world()
Traceback (most recent call last):
...
TypeError: HelloGroup.hello_world() missing 1 required positional argument: 'self'
>>> group.hello_world(group)
Hello, World!

This is how it is done internally:
>>> args, kwargs = group.hello_world.substitute_call()
>>> group.hello_world(*args, **kwargs)
Hello, World!

:::
::::
:::{note}
The type of injected positional and keyword arguments is not checked at runtime, 
but it is presumed that they are correct.
It is uncertain if type checkers like mypy would detect wrong types in in the calling these 
positions.
:::


(command-completion)=
### Command completion
Commands are completed automatically if there is only one way to complete it.
For example, "h" will be completed to "help". 
The package also completes functions consisting of several words separated with underscore `_`.
When calling, a space can be used instead of an underscore.
Thereby, instead of writing "change_language", one can also write "c l".
Currently, this multi-word completion is restricted to only two words.

:::{important}
Since Command completion is done as part of line parsing,
It can't be triggered otherwise, as for example by pressing `tab`.
:::

The multi-word completion is implemented by using distributors.
A distributor works like a function consisting of the first word of a function
with two words separated by an underscore "_":
If there is a function "change_language", "change" is a distributor. 

When completing, distributors are prioritised over functions. 
If there are functions "help" and "halt_program", "h" will be extended to "halt"
since "halt" is a distributor. To then call "help", at least "he" is required.
To call "halt_program", "h p" is enough.
:::{code} python
>>> from localecmd import CLI, Module, programfunction
>>> @programfunction()
... def help():
...     print("help")
>>> @programfunction()
... def halt_program():
...     print("halt_program")
>>> @programfunction()
... def halt_function():
...     print("halt_function")
>>> cli = CLI([Module('completiontest', [help, halt_program, halt_function])])
The language of the command line is fallback language
>>> cli.runcmd("he")
help
>>> cli.runcmd("h p")
halt_program
>>> cli.runcmd("h")
halt_ could be completed to ['halt_program', 'halt_function']
Command incomplete: halt
Line could not be parsed!

:::

If there are two or more ways to complete, no completion is done.
If there are functions "crop_image", "chop_image" and "change_language",
"c l", can't be completed uniquely since "c" could be "crop", "chop" or "change".

Command completion can be tested from command line with the function 
{py:func}`localecmd.builtins.complete`:
::: {code} python
>>> from localecmd.builtins import complete
>>> complete("he")
help
>>> complete("h p")
halt_program
>>> complete("h")
halt_ could be completed to ['halt_program', 'halt_function']
Command incomplete: halt

>>> cli.close()

:::

:::{rubric} Name conflicts
:::
In case the first word of the function name conflicts with another function, the
function name must be included with the underscore '_'.
If there are functions "help" and "help_program" and one wants to call "help" with 
argument "program", one can safely write "help program". 
To call the function "help_program", the underscore must be included since the 
calling else would go to "help".
:::{code} python
>>> from localecmd import CLI, Module, programfunction
>>> @programfunction()
... def help(*args: str):
...     print(f"help:{' '.join(args)}")
>>> @programfunction()
... def help_program():
...     print("help_program")
>>> cli = CLI([Module('completiontest2', [help, help_program])])
The language of the command line is fallback language
>>> cli.runcmd("h")
help:
>>> cli.runcmd("help program")
help:program
>>> cli.runcmd("h p")
help:p
>>> cli.runcmd("help_program")
help_program
>>> cli.runcmd("help_")
help_program
>>> cli.close()

:::

Command completion is done by {py:func}`~localecmd.parsing.complete_command`.


(helptexts)=
## Markdown helptexts
When loading functions, module helptexts are loaded from `locale/<language>/docs`. 
Thereby internationalization is supported.

The requirements for file and content are
- The file must have same name as the module and have ending `.md` for Markdown.
- The Markdown format supported is what [rich](https://rich.readthedocs.io/en/stable/introduction.html) supports. 
See also [further down](#generate-helptexts) on how to generate helptexts automatically.
- The function helptext must start as a 3. order header "###" and the title must 
be the function name in the loaded language. 
Paragraphs with other headers will be appended to the function above it.

The function loading the files is {py:func}`~localecmd.module.Module.load_docs_from_file`, 
and {py:func}`~localecmd.module.Module.assign_docs` divides the document into function paragraphs. 
For parsing of the markdown format itself, 
see [rich documentation](https://rich.readthedocs.io/en/stable/introduction.html).
 
(generate-helptexts)=
###  Generate helptexts from docstrings
The Function helptexts can be extracted from the docstrings of the functions.
This is done similar to automatic API documenters in sphinx, 
but function, parameter and type names
in the docstrings are translated to the current CLI language. 

The 
[sphinx-localecmddoc](https://jbox.codeberg.page/sphinx-localecmddoc/) 
extension for sphinx which can extract the docstrings automatically.
[The sphinx markdown builder] (https://pypi.org/project/sphinx-markdown-builder/)
can be used to put the output into markdown.

:::{rubric} Example for single cli language
:::
The list of needed sphinx options is quite long, so using the (same) `conf.py`
as for the project may be useful.

Anyway, the following command is an example for running from the project folder.
Important here is to use the correct cvalue for `localecmd_modules` options.
See [sphinx-build documentation](https://www.sphinx-doc.org/de/master/man/sphinx-build.html)
on how to type the options.
:::{code} bash
sphinx-build -b markdown docs/source/functions locale/<language>/docs \
 -a -C -D extensions=myst_parser,sphinx_markdown_builder,localecmddoc \
 -D language=<language> -D source_suffix..md=markdown -D localecmd_outdir='' \
 -D localecmd_modules.functions='functions'
:::

For cli with multi-language support, the cli must be translated first.
See also the [tutorial](tutorial-helptexts).
    
## Translated cli
The functions, messages and types of localecmd programs can be translated with gettext:
:::{code} bash
£ help change_language
                           change_language language ⠀

Change language of program

 • Parameters:
   language (string) – Folder name inside of locale/ containing the
   translation strings. Defaults to ‘’ meaning the fallback language
   English. 
£ change_language de_DE
Die Sprache der Befehlszeile ist Deutsch (Deutschland)
€ hilfe sprache_wechseln
                           sprache_wechseln sprache ⠀

Programmsprache ändern

 • Parameter:
   sprache (Zeichenkette) – Ordnername under locale der die Wörterbücher 
   enthält. Standard ist ‚‘ für die Rückfallsprache Englisch
€ sprache_wechseln -sprache en_GB
The language of the command line is English (United Kingdom)
£ quit
:::

The package defines three domains for the translation and looks for translation files in folder 'locale'.
The domains are

- cli_functions: Names of functions, its parameters and keywords (True/False).
- cli_types: Names of types such as `int`, `str` and so on.
- cli_messages: Messages printed by localecmd library. 
Currently, log lessages are not marked for translation.

:::{warning}
By changing the translations in `cli_functions` domain, the public API is changed!
Therefore do those changes with care!
:::

To extract messages for the three domains, use the method 
{py:meth}`~localecmd.create_pot`. 
See there for documentation on string extraction.

User-defined messages may come into another domain which typically is 'messages'.
These can be extracted like for every other localised project.
For documentation, look to [babel](https://babel.pocoo.org) and 
[gettext](https://www.gnu.org/software/gettext/manual/index.html) docs.

Language initialisation and string updating is done like for all gettext projects.
Confer a localisation tutorial for guidance.


## Type conversion
Inputs to shells are always strings while the functions may need arguments of other types to be
possible to use as normal Python functions of a library.
Before calling the function, the argument strings are converted to the desired types.
This conversion following the type annotations of the function.

The type conversion is only implemented for a subset of type annotations since there are few 
possibilities to create objects from pure strings.

Allowed types are:

- Python builtins int, float, bool, str (and None)
- All user-defined classes that can be created with a single string as positional argument
- [Union types](#union-types)
- [Sequences such as lists with restrictions](#sequence-types)

Parameters without annotation are handled as the `typing.Any` type which simply passes the input 
string or list of strings.

The type annotations are read with {py:func}`inspect.get_annotations`
which also reads atring annotations by calling {py:func}`eval`.
This also allows for the use of `from __future__ import annotations`.

Type conversion is done with {py:func}`localecmd.parsing.convert_arg` and 
If the strings can't be converted, a `TypeError` is raised which is catched by the command runner. 

(union-types)=
### Union types
Union types are supported as long as they are not nested.
When converting to a union type, the library will try out converting to the types in the order they are given.
Therefore the most restrictive types should be first while the most general types should be last.
For example when integers and strings are accepted, the union should list int first, `Union[int, str]`,
since all strings can be accepted as strings, but only a small subset of strings can be converted to integers.

:::{code} python
>>> from localecmd import CLI, Module, programfunction
>>> from typing import Union
>>> @programfunction()
... def func1(arg1: Union[str, int], arg2: int):
...     print(repr(arg1), repr(arg2))
>>> @programfunction()
... def func2(arg1: Union[int, str], arg2: int):
...     print(repr(arg1), repr(arg2))
>>> cli = CLI([Module('typeconversion', [func1, func2])])
The language of the command line is fallback language
>>> cli.runcmd("func1 80 90")  # is str is first, arg1 will always be a string
'80' 90
>>> cli.runcmd("func2 80 90")  # If int is first, arg1 may become converted to integer
80 90
>>> cli.runcmd("func2 80 90.0")  # Python can't convert the string '90.0' to an integer.
Error while executing: Error while converting argument 'arg2' of function 'func2':
Could not convert value '90.0' to type 'int'.
Message:
'90.0' is not a valid number
>>> cli.close()

:::
(sequence-types)=
### Sequence types
Sequences except strings are only partially supported by localecmd as it is not obvious how to convert
the string input to sequences without using amount of parentheses.
There are several ways of creating sequences from the calling.

Two ways of creating sequences use Python functionality of function callings.
To create a sequence of variables in positional arguments, one has to use the 
[variadic argument](https://docs.python.org/3/tutorial/controlflow.html#arbitrary-argument-lists)
with a star in front.
Typically, the parameter is called `args` and the written `*args`, but any name Python allows is possible.
The same applies to dictionaries. 
The only way to create a dictionary from command line is to use variable keyword arguments to create a dictionary (mapping).

:::{note}
The translation of dictionary keys is not possible for variable keyword arguments. 
:::

Type annotations of variable arguments follow the way defined by Python. 
For example, if all `*args` should be floats, the annotation is `*args: float`


A third way only works in keyword arguments and creates lists.
All words after the argument name are concatenated to a list.

Other than these methods, sequences can not be created directly by localecmd, 
but custom types may be used to convert a string to some user-defined type which is handled as a sequence.

:::{code} python
>>> from localecmd import CLI, Module, programfunction
>>> @programfunction()
... def fl(*l: int, kw_list: list[int], **d: float):
...     print(l, kw_list, d)
>>> cli = CLI([Module('sequencetypes', [fl])])
The language of the command line is fallback language
>>> cli.runcmd("fl 80 90 -kw-list 10 20 30")
(80, 90) [10, 20, 30] {}
>>> cli.close()

:::


