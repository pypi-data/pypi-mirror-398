## 0.12.2 (2025-12-27)

### Fixes

- Removed injected arguments from calling

## 0.12.1 (2025-12-27)

### Fixes

- Hide injected arguments for translation

## 0.12.0 (2025-12-27)

### Breaking change

- The loading of docstrings from file is now disabled by default. use `cli(..., use_file_docstrings=True)` to reenable it.

### New features

- Added command save_commands that saves run commands
- Use file docstrings only if desired.

## 0.11.5 (2025-12-18)

### Fixes

- Allow string annotations for pot export too

## 0.11.4 (2025-12-15)

### Fixes

- Enables print even if cli is not running
- **Docs**: Put doctests of builtin functions into code blocks and changed to backticks fence

## 0.11.3 (2025-12-14)

### Fixes

- Removed attribute module.exported_md which functionality was removed in 0.11.0
- Changed logging level of closing cli to info.

## 0.11.2 (2025-12-14)

### Fixes

- Removed untested function that was already replaced with sphinx-localecmddoc
- Redirect output for debugging
- Fixed some builtin functions that printed to wrong file

## 0.11.1 (2025-12-08)

### Fixes

- Fixed error when calling create_pot several times

## 0.11.0 (2025-12-08)

### Breaking change

- In function localecmd.create_pot project metadata are now keyword-only arguments
- The extract_docs module and <function or topic>.exported_md attributes are removed. to extract docstrings as markdown, use sphinx-localecmddoc
- Renamed attribute cli.log to cli.cmdlog. also:
entries now have new index due to first entry being empty.
to be able to use the logging features, the printoutput function must be used.

### New features

- Added logging of answers to commands and log the transcript of all in and output

### Fixes

- Added newline in transcript after command
- Added prompt and written command to transcript also if input vis script (not only via console)

### Changes

- Changed signature of create_pot to include destination folder
- Markdown docuentation extraction is now done by sphinx_localcmddoc

## 0.10.0 (2025-11-06)

### New features

- Allow string annotations

### Fixes

- The type of injected arguments is not tested

## 0.9.0 (2025-11-05)

Got published while WIP

## 0.8.0 (2025-11-03)

### Breaking change

- Instead of using programmethod and inheriting from functiongroup, use programfunction decorator in normal class instance instead. to inject `self`, use the `prependargs` parameter of module initialisastion. see also section 'class_instance as module' in documentation.

### New features

- Added ability to inject positional and keyword arguments to cli callings

### Changes

- Removed functiongroups

## 0.7.0 (2025-10-30)

### New features

- Added functionality to build classes with functions that should be available from cli

## 0.6.3 (2025-10-28)

### Fixes

- Function now accepts methods

## 0.6.2 (2025-04-09)

### Fixes

- Fixed error that doctests were not detected in wrapped functions

## 0.6.1 (2025-04-05)

### Fixes

- Ignore empty type annotations
- Problems down to python 3.8
- Removed functionality that did not exist for python<3.11
- Support union type arguments with '|'

### Changes

- More linting and fix problems
- More linting with bug fixes

## 0.6.0 (2025-03-28)

### New features

- Add function that predicts command autocompletion

### Fixes

- Better error message when calling functions with wrong arguments

### Changes

- Factor out command completion to an own function
- Use dashes within kewyword arguments instead of underscores

## 0.5.0 (2025-03-26)

### Breaking change

- Translator function in module is no longer supported.

### New features

- Support boolean values
- Show list of distributor functions

## 0.4.0 (2025-03-22)

### New features

- Keyword arguments can now contain more than one argument per keyword

### Changes

- Type of arguments is now converted with function annotations (#2)

## 0.3.0 (2025-03-09)

### New features

- Allow handling of more domains than the internal ones

### Changes

- Switch to babel for gettext domain handling and language switching

## 0.2.0 (2025-03-06)

### New features

- Function to create all pot files at once
- Export module directly to library users
- Function t o run scripts
- Addability to optionally run commands in system/fallback language (typically english)
- **Function**: Give default translator function by library
- **Cli**: Allow to run commands directly with cli.runcmd
- **Cli**: Allow loading module objects in addition to modules
- **Pot**: Generate pot file for localecmd messages
- **Type-translation**: Create type list automatically
- **Pot**: Add function to generate pot files o ffunction names and parameters
- **Cli**: Add function to restart cli to start it even if it is running
- **Cli**: Include builtin functions and enable them by default
- Make important parts of library easier accessible

### Fixes

- **Parsing**: Negative numbers are not longer interpreted as keyword arguments
- **Parsing**: Solve name conflicts between function and distributor
- Load correct docstrings
- Markdown needs double newline to generate a newline and added missing type annotation
- **Docstrings**: Only show myst syntax in myst export
- Fix typing and removed missing imports
- **Cli**: Ensure that translators are enabled every time the cli starts
- Fix errors detected by mypy
- Stop overriding cli attributes when one tries to create second cli

### Changes

- Change default docstring folder
- Log executed commands
- Don't add space after command run
- Start_cli now retuns cli object
- **Pot**: Centralise pot file saving
- **Cli**: Closing cli now needs access to cli object
- **Cli**: Move cmdloop to method of cli but keep a wrapper of it
- **Cli**: Move static functions out of class
- Simplify calling
- **Function-translation**: Reorder if statements for better understanding
- **Language-switching**: Simplify fallback handling
