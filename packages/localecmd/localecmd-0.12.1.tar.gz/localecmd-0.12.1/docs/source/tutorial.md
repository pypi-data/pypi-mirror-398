# Tutorial
This tutorial introduces the `localecmd` library and its features.
We will create a simple shell for drawing turtle graphics and translate it into other languages.
For drawing, we will use the python builtin 
[turtle module](https://docs.python.org/3/library/turtle.html). 


If you get the error `No module named '_tkinter'`, you have to install tkinter first.
See [tkinter documentation](https://docs.python.org/3/library/tkinter.html#module-tkinter) 
on how to do that.

To translate, you need to edit `.po` files and export them to `.mo` files. 
In the tutorial, we will use a normal text editor to edit the files and 
[babel](https://babel.pocoo.org/en/latest/) to convert them. 
Babel should be installed along with the `localecmd` library.

Part of the tutorial is based on the 
[example of builtin cmd library](https://docs.python.org/3/library/cmd.html#cmd-example)
and it can thereby be seen as a comparison between these two libraries.


## Create project
We will need a project folder for the tutorial which contains certain subfolders.
Create the project folder with you favourite file explorer. 
In bash shell, run `mkdir localecmd-tutorial` (or use whatever descriptive name).

Go into that folder and create a python file named `functions.py`. 
You may use any name, but the tutorial presumes `functions.py`.
Also create a python file `__main__.py` and subfolders `locale` and `helptexts`. 


## Build TurtleShell
First introduce the functions. Edit `functions.py` to look as 
:::{literalinclude} tutorial/functions.py
:::


Then set up the shell. Edit `__main__.py` to be 
:::{literalinclude} tutorial/__main__.py
:::

Now, you can start the turtle shell by typing `python .` into the shell.
Here is a sample session with the turtle shell showing the help functions, 
using blank lines to repeat commands, and the simple record and playback facility:
:::{literalinclude} tutorial/turtle1.txt
:::

## Translate
Localecmd uses [gettext](https://www.gnu.org/software/gettext/) to translate strings.
This includes also function and parameter names and their types.
The procedure of translating the program is the following: 

1. Extract strings from the source files. These are messages and names. 
The extracted strings can be found in `.pot` files. These are templates for the translations.
2. Initialise and update translation files from template. 
Every translation has its own folder containing the translation files 
3. Translate strings.
4. Compile translation files to machine-readable format.
5. Localecmd should now recognise the new translations.

:::{hint}
Several of the commands have to be run multiple times with different arguments.
In a real case, one should consider to use a script or makefile to cover the process.
:::
### Extract strings
Localecmd only provides Python API to extract strings from source files. 
Here, we will extract the strings with a script. 
Create a file `extract_pot.py` with the content
:::{literalinclude} tutorial/extract_pot.py
:::
The folder `locale` should now contain the translation template for every domain:
`cli_functions`, `cli_messages` and `cli_types`.

If we now open `locale/cli_functions.pot`, it should look like
:::{code} po
# Translations template for localecli_tutorial.
# Copyright (C) <YEAR> ORGANIZATION
# This file is distributed under the same license as the localecli_tutorial
# project.
# FIRST AUTHOR <EMAIL@ADDRESS>, <YEAR>.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: localecli_tutorial 0.1\n"
"Report-Msgid-Bugs-To: user@example.com\n"
"POT-Creation-Date: YEAR-MO-DA HO:MI+ZONE\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel <BABEL-VERSION>\n"

# Function
# Change language of program
msgctxt "builtins"
msgid "change_language"
msgstr ""

# Parameter
msgctxt "builtins.change_language"
msgid "language"
msgstr ""
:::
The first ~20 lines are header and metadata. 
The actual translation strings start below that, starting with the builtin functions.
:::{important}
Don't change this file. 
It is the template for the translations and will anyway be overwritten everytime `tutorial/extract_pot.py` is called.
:::
Further down, the turtle functions appear. 
Note that the comments above the function names show the first line of the docstring.
Also, the context of every function is the module name: The `bye` function is in module `functions`, so the context is `functions`.
The context of a parameter name is the function name: Parameter `args` of function `circle` in module `functions` has context `functions.circle`.
This means that the parameter name must be translated for every function separately, even if it has the same name.

:::{code} po

# Function
# Stop recording, close the turtle window, and exit:  BYE
msgctxt "functions"
msgid "bye"
msgstr ""

# Function
# Draw circle with given radius an options extent and steps:  CIRCLE 50
msgctxt "functions"
msgid "circle"
msgstr ""

# Parameter
msgctxt "functions.circle"
msgid "args"
msgstr ""

# Function
# Set the color:  COLOR BLUE
msgctxt "functions"
msgid "color"
msgstr ""
:::
The files `cli_messages.pot` and `cli_types.pot` are built up similarly, but contain no more info than typical for gettext.

Additionally we need to extract the messages shown in the tutorial functions.
To extract those, run `pybabel extract . -o locale/messages.pot`.

Now translation templates for all domains are extracted. 
This message extraction has to be done every time sources have changed.

### Initialise translations
Before the translation into a language can be started, it must be initialised.
Initialisation is only needed the first time a domain for a language is being translated.
We will use babel for this and every domain needs to be initialised separately.

As language, we first use English. Run
:::{code} shell
pybabel init -i locale/cli_functions.pot -d locale -D cli_functions -l en_GB
pybabel init -i locale/cli_messages.pot -d locale -D cli_messages -l en_GB
pybabel init -i locale/cli_types.pot -d locale -D cli_types -l en_GB
pybabel init -i locale/messages.pot -d locale -D messages -l en_GB
:::

This should generate a subfolder of `locale` named `en_GB` which contains another folder `LC_MESSAGES`.
Inside that, there are four files with the same names as the domains, but with ending `.po`.
The content of those is practically the same as the templates.

To show differences, we also will translate the program into an other language.
Select a language that you are comfortable to translate into. 
If you use an other language than German (Germany), make sure to replace `de_DE` with the language code you are translating into further in the tutorial.
Run:
:::{code} shell
pybabel init -i locale/cli_functions.pot -d locale -D cli_functions -l de_DE
pybabel init -i locale/cli_messages.pot -d locale -D cli_messages -l de_DE
pybabel init -i locale/cli_types.pot -d locale -D cli_types -l de_DE
pybabel init -i locale/messages.pot -d locale -D messages -l de_DE
:::

### Update translations
When the sources have changed and templates updates as in last section, the translation files must be updated.
This is done with
:::{code} shell
pybabel update -i locale/cli_functions.pot -d locale -D cli_functions
pybabel update -i locale/cli_messages.pot -d locale -D cli_messages
pybabel update -i locale/cli_types.pot -d locale -D cli_types
pybabel update -i locale/messages.pot -d locale -D messages
:::
Again, every domain must be updated separately, but at least the update is done for all lanugages at the same time.

### Translate strings
We will translate the string with a normal text editor as this is enough for simple use.
The source language is already English, so the English files may be left unchanged. 
Go through all `.po` files in directory `locale/de_DE/LC_MESSAGES` and translate the string in msgid to msgstr. 
All strings may have non-ASCII characters.
Confer a gettext software localisation tutorial for more details on translating.

### Compile strings
This has again to be done separately for every locale and file. 
The list of commands to run now is
:::{code} shell
pybabel compile -l en_GB -d locale -D cli_functions
pybabel compile -l en_GB -d locale -D cli_messages
pybabel compile -l en_GB -d locale -D cli_types
pybabel compile -l en_GB -d locale -D messages
pybabel compile -l de_DE -d locale -D cli_functions
pybabel compile -l de_DE -d locale -D cli_messages
pybabel compile -l de_DE -d locale -D cli_types
pybabel compile -l de_DE -d locale -D messages
:::

### Use translated program
As a default, the CLI is started in the fallback language, that is how it was coded.

The language can be changed in runtime with the command `change_language` as demonstrated below.
Note that helptexts are not translated as that is part of the next step.
:::{literalinclude} tutorial/turtle2.txt
:::
(tutorial-helptexts)=
## Helptexts
Localecmd primarily loads helptext from provided markdown files.
These are expected to be in the folder `locale/<language>/docs`.
The name has to be the name of the module.

We will now create those four files (two modules, two languages).
We will use a script that uses the docstrings to generate the helptexts.
First, we need a to extract the messages to translate and translate them. 
Create `extract_docs.py` with the following content:
:::{literalinclude} tutorial/extract_docs.py
:::

To run it, the packages `sphinx`, `myst-parser`, `sphinx-intl` and 
`sphinx-markdown-builder` must be installed.
:::{code} shell
pip install myst-parser sphinx sphinx-intl sphinx-markdown-builder
:::
Then run the script:
:::{code} shell
python extract_docs.py
:::
It should generate `builtins.po` and `functions.po` in `locale/en_GB` and `locale/de_DE` folders.

Translate the messages. For example as
:::{literalinclude} tutorial/locale/de_DE/LC_MESSAGES/functions.po
:lines: 1-30
:::
The files for English language do not have to be translated since docstrings
already are in English.
Compilation will be done by sphinx-intl, so that is not nessesary now.

Then we will actually create the translated docs with a new script.
Create `generate_helptexts.py` containing
:::{literalinclude} tutorial/generate_helptexts.py
:::
and run it with 
:::{code} shell
python generate_helptexts.py
:::

The translated helptexts should now be in folder `locale/<language>/docs`.
If we open `locale/de_DE/docs/functions.md` the first 20 lines should look like
:::{literalinclude} tutorial/locale/de_DE/docs/functions.md
:lines: 1-20
:::

Last we check that the translations are loaded correctly by our turtle-program.
Run `python .` in the shell to start it again and check that translations are correct.
:::{literalinclude} tutorial/turtle3.txt
:::
