# Module builtins

General functions in a command-line program.

### change_language language ⠀

Change language of program

* **Parameters:**
  **language** (*string*) – Folder name inside of `locale/` containing the
  translation strings. Defaults to ‘’ meaning the fallback language
  English.

### help topic... ⠀

Get help

* **Parameters:**
  **topic** (*string*) – Function/Topic to get help on. If empty, a list of all
  functions and topics is shown.

### Examples

```default
Show list of all functions and topics
¤ help 
(...)
Show helptext on function `help`
¤ help 'help'
(...)
```

### list_languages ⠀

Print list of available program languages

### quit ⠀

Terminate program

* **Raises:**
  **SystemExit** – Always
