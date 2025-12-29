#!/usr/bin/env python3
from __future__ import annotations

import logging
import shlex
import sys
import types
from typing import Any, Callable, Iterable, List, Union, cast, get_args, get_origin

from babel.numbers import parse_decimal, parse_number

from localecmd.func import Function
from localecmd.localisation import _, d_, f_, get_language

module_logger = logging.getLogger("parsing")

KEYWORD = 'keyword'
"Mesage context of keywords"
# Changes here must be reflected in the documentation of bool in builtins module
KEYWORDS = {True: 'yes', False: 'no'}
"Boolean values"

EMPTY_DICT: dict[str, str] = {}  # To make both mypy AND ruff happy

# https://discuss.python.org/t/how-to-check-if-a-type-annotation-represents-an-union/77692/2
if sys.version_info >= (3, 10):
    _UNION_TYPES = {Union, types.UnionType}
else:
    _UNION_TYPES = {Union}


def to_bool(string: str) -> bool:
    """
    Localised conversion of a string to a boolean value

    The string will be compared to a list of keywords for the current language.
    The comparison is case-insensitive.

    :param str string: String to convert
    :raises ValueError: If string not possible to convert
    """
    string = string.casefold()
    Y = [s.strip().casefold() for s in f_(KEYWORD, KEYWORDS[True]).split('|')]
    N = [s.strip().casefold() for s in f_(KEYWORD, KEYWORDS[False]).split('|')]

    if string in Y:
        return True
    elif string in N:
        return False
    else:
        msg = "Only strings {bools} can be interpreted as bool, but got {got}"
        raise ValueError(_(msg).format(bools=Y + N, got=string))


def _convert_onetyped_arg(val: str | list[str], typ: Callable[[str], Any]):
    """
    Convert string to certain type

    :param str val: String to convert
    :param type typ: Type to convert string to.
    The type must be callable with a string as an argument and return it converted.
    Therefore union types are not allowed. Use :{py:func}`convert_arg` for that.
    :raises TypeError: If string could not be converted

    """

    try:
        module_logger.debug(f"Inner: Try converting '{val}' to type {typ}")
        if get_origin(typ) in [list, List] or typ in [list, List]:
            msg = _("Conversion of a single string to list is explicitly disallowed.")
            raise TypeError(msg)
        elif typ is float and isinstance(val, str):
            return float(parse_decimal(val, get_language(), strict=True))
        elif typ is int and isinstance(val, str):
            return int(parse_number(val, get_language()))
        elif typ is bool and isinstance(val, str):
            return to_bool(val)
        elif typ is Any:
            return val

        # Not all types allow to be created from lists, but that error is handled below.
        return typ(val)  # type:ignore[arg-type]
    except (ValueError, TypeError) as e:
        msg = _("Could not convert value {val} to type '{typ}'.\nMessage:\n")
        if hasattr(typ, '__name__'):
            typename = d_(typ.__name__)
        else:
            typename = str(typ)

        tmsg = msg.format(typ=typename, val=repr(val))
        module_logger.debug(tmsg)
        raise TypeError(tmsg + ''.join(e.args)) from e


def convert_arg(val: str | list[str], typ: type):
    """
    Convert string to certain type

    The type must be callable with a string as an argument and return it converted.

    Union types are handled by iterating over the its types in specified order.
    When using Unions, the types in the union must fulfil the same requirements as the single types.
    :::{important}
    The function will try convert the string to the types in the specified order.
    This means that the order of the types decides what type it is converted to.
    The most special type (f.ex. int) should be first and the most flexible (f.ex. str) last
    as strings always can be converted to strings, but seldom to integers.
    :::

    :param str val: String to convert
    :param type typ: Type to convert string to.
    :raises TypeError: If string could not be converted
    """
    msg = f"Outer: Converting '{val}' to type {typ}, origin {get_origin(typ)}"
    module_logger.debug(msg)

    if get_origin(typ) in _UNION_TYPES:
        for arg in get_args(typ):
            try:
                return convert_arg(val, arg)
            except TypeError:
                continue
        # Come here if all conversion attempts failed.
        msg = _("Could not convert value '{val}' to any of the types {types}.")
        types = [d_(n.__name__) if hasattr(n, '__name__') else d_(str(n)) for n in get_args(typ)]
        tmsg = msg.format(val=val, types=types)
        raise TypeError(tmsg)
    elif get_origin(typ) in [list, List]:
        if isinstance(val, list):
            elem_type = cast(type, Union[get_args(typ)])
            return [convert_arg(v, elem_type) for v in val]
        else:
            msg = _("Cannot convert value '{val}' to a list.")

            raise TypeError(msg.format(val=val))
    else:
        return _convert_onetyped_arg(val, typ)


def convert_args(func: Function, *args, **kwargs) -> tuple[Iterable, dict]:
    """
    Convert positional and keyword args in a function calling to correct type.

    It is presumed that all arguments are strings.

    :raises TypeError: If at least one type could not be converted.
    :return: Positional and keyword arguments in the type of the function annotation
    :rtype: tuple[Iterable, dict]

    """
    ba = func.signature.bind(*args, **kwargs)
    for i, (arg, val) in enumerate(ba.arguments.items()):
        try:
            param = func.signature.parameters[arg]

            annotation = func.annotations.get(param.name, Any)

            if param.kind == param.VAR_POSITIONAL:
                ba.arguments[arg] = tuple([convert_arg(v, annotation) for v in val])
            elif param.kind == param.VAR_KEYWORD:
                ba.arguments[arg] = {k: convert_arg(v, annotation) for k, v in val.items()}
            elif i < len(func.prependargs) or param.name in func.addkwargs:
                # Prepended arguments do not need to be converted as they already are
                # Same for injected keyword arguments
                continue
            else:
                ba.arguments[arg] = convert_arg(val, annotation)
        except TypeError as e:
            msg = _("Error while converting argument '{arg}' of function '{fname}':\n")
            tmsg = msg.format(arg=arg, fname=func.translated_name)
            raise TypeError(tmsg + ''.join(e.args)) from e
    module_logger.debug(f"Converted calling to {ba.arguments}")
    return ba.args, ba.kwargs


def object_to_token(o: int | float | str) -> str:
    """
    Converts the object into a string that can again be parsed by convert_tokens.

    This calls the Python str method for everything but strings. Here `repr(o)`
    is called to insert quotation marks.

    :param int | float | str o: The object to convert.
    :return str: The object as a string.

    """
    if isinstance(o, str) and ' ' in o:
        # Keep quotes around strings:
        return repr(o)
    return str(o)


def word_is_kwarg(word: str) -> bool:
    """
    Checks if the given word starts a keyword argument.

    A keyword argument starts with a dash '-' and the following characters are a valid Python
    variable name.
    However, the function checks only for the dash and that the first character afterwards is
    alphabetical.

    :param word: Word to check
    :type word: str
    :return: If the word starts a keyword argument
    :rtype: bool

    """
    return len(word) > 1 and word.startswith('-') and word[1].isalpha()


def line_to_args(
    line: str,
) -> tuple[str, list[str], dict[str, str | list[str]], str]:
    """Parse the line into a command name and a string containing
    the arguments. Returns a tuple containing (`command`, `args`, `kwargs`, `line`).
    'command' and 'args' may be empty if the line couldn't be parsed.

    """
    line = line.strip()

    # Split up at space, but keep quoted strings as such and also keep the quotes.
    tokens = shlex.split(line, posix=True)

    if len(tokens) == 0:
        # Nothing in the line
        cmd = ""
        words: list = []
    elif len(tokens) == 1:
        # Only command
        cmd, words = tokens[0], []
    else:
        # Should tokens be empty list anyway, this line will fail with
        # "IndexError: list index out of range".
        cmd, words = tokens[0], tokens[1:]

    # Sort out keyword arguments
    # Indices of keyword argument names
    kwi = [i for i, e in enumerate(words) if word_is_kwarg(e)]
    if kwi:
        args = list(words[0 : kwi[0]])
        kwi.append(len(words))
        kwargs: dict[str, str | list[str]] = {}
        for i in range(len(kwi) - 1):
            # Number of arguments to this keyword
            nargs = kwi[i + 1] - kwi[i] - 1
            if nargs == 0:
                # No actual keyword argument – It is an option/flag
                # This is not supported at the moment
                raise ValueError(_("Keywords must have arguments!"))
            elif nargs == 1:
                # One keyword argument – process that as for positional args
                kwargs[words[kwi[i]][1:]] = words[kwi[i] + 1]
            elif nargs > 1:
                # Multiple arguments for one keyword. That is a list.
                c_words = [words[iw] for iw in range(kwi[i] + 1, kwi[i + 1])]
                kwargs[words[kwi[i]][1:]] = c_words
            else:  # pragma: no cover
                # Means that index of keyword argument decreased. This should never happen
                msg = "Something really bad happened while parsing keyword arguments."
                raise RuntimeError(msg)
    else:
        args = words
        kwargs = {}

    return cmd, args, kwargs, line


def args_to_line(cmd: str, *args, **kwargs) -> str:
    """
    Convert the calling of a command to a string that produces this command.

    The arguments are converted directly. Keyword arguments get a minus "-" in
    front of the key and the argument comes afterward.

    Arguments fr keyword arguments including whitespace will be quoted.

    :param str cmd: Command name.
    :param list:args: Arguments to the command.
    :param dict kwargs: Keyword arguments to the command.
    :return str: The line to insert into command line prompt.

    :::{rubric} Example
    :::
    >>> args_to_line("bla", 80, "bla", hello="world", hello2="hello, World")
    "bla 80 bla -hello world -hello2 'hello, World"

    """
    tokens = [str(cmd)]
    for arg in args:
        tokens.append(object_to_token(arg))

    for key, value in kwargs.items():
        tokens.append("-" + str(key))
        tokens.append(object_to_token(value))

    return " ".join(tokens)


def extend_word(cmd: str, cmdlist: Iterable[str], distributors: set[str]) -> str:
    """
    Extent word

    The function will try to extend the word `cmd` to a command in `cmdlist`
    or a word in the `distributors` set.

    The following will be the output:
    1. Given string is a valid command -> return it
    2. It can be completed to one word in the `distributors` set -> extend to that.
    3. It can be completed to one valid command -> extend to that.
    4. It can't be extended to any command, return empty string.
    Command doesn't exist.
    5. It can be extended to more than one command,
    but zero or at least two distributors -> return empty string.
    Command is ambigous.

    :param str cmd: Command to complete
    :param Iterable[str] cmdlist: List of known commands
    :param set[str] distributors: List of names to extend to.
    :return: Completed command, or empty string if not able to complete
    :rtype: str

    """
    # Remember to updating docstring of CLI when doing changes here
    if cmd not in cmdlist:
        func_completes = [n for n in cmdlist if n.startswith(cmd)]
        dist_completes = [n for n in distributors if n.startswith(cmd)]

        if len(dist_completes) == 1:
            cmd = dist_completes[0]
        elif len(func_completes) == 1:
            cmd = func_completes[0]
        elif not func_completes:
            print(_("Command {0} does not exist!").format(cmd))
            return ""
        else:
            msg = _("{0} could be completed to {1}")
            print(msg.format(cmd, str(func_completes)))
            return ""
    return cmd


def complete_command(
    words: list[str], cmdlist: Iterable[str], distributors: set[str]
) -> tuple[str, list[str]]:
    """
    Find and complete the command name from given words

    This function does not handle keywors arguments.

    :param list[str] words: Words containing function name and positional arguments
    :param Iterable[str] cmdlist: List of possible commands to extend to
    :param set[str] distributors: Set of possible distributors to extend to
    :return: Completed function name and remaining list of positional arguments.
    If the completion failed, the function name is empty.
    :rtype: tuple[str, list[str]]

    """
    # Remember to updating docstring of CLI when doing changes here

    cmd = extend_word(words[0], cmdlist, distributors)
    args = words[1:]
    module_logger.debug("Extended first word to command " + cmd)
    while cmd in distributors and cmd not in cmdlist:
        if len(args) > 0:
            newcmd = extend_word(cmd + '_' + args[0], cmdlist, distributors)
            if not newcmd:
                cmd = ''
                break
            args.pop(0)
            cmd = newcmd
            module_logger.debug("Extended word to command " + cmd)
        elif extend_word(cmd + '_', cmdlist, distributors):
            # There must be a better way of doing this than calling the command twice.
            cmd = extend_word(cmd + '_', cmdlist, distributors)
            break
        else:
            # Called f.e. edit and did not say what to edit.
            # or specified what to edit as an integer
            # This should be handled somehow
            print(_("Command incomplete: {0}").format(cmd))
            return "", []
            # Now just edit is called, which is no function
    return cmd, args


def parse_line(
    line: str,
    function_dict: dict[str, Function],
    distributors: set[str],
    aliases: dict[str, str] = EMPTY_DICT,
) -> tuple[Function, Iterable[str], dict[str, str | list[str]]] | None:
    """
    Interpret line as if it came from prompt.

    What function does is
    1. Parse line to get command name, positional args and keyword args.
    See {py:func}`parsing.line_to_args`
    2. Complete command
    3. If command is now in distributor set, use first argument to extend it.
    4. Apply aliases


    :param line: Line as typed in
    :type line: str
    :param function_dict: Dictionary of name – executable pairs.
    :type function_dict: dict[str, Function]
    :param distributors: Set of short names of functions to use for command completion
    and for being able to concatenate commands such that user can use space instead of underscore.
    :type distributors: set[str]
    :param aliases: Command aliases to apply *after* command completion,
    defaults to {}
    :type aliases: dict[str, str], optional
    :return: Function, positional args and dict of keyword args. None if command could not be parsed
    :rtype: tuple[Function, Iterable, dict]

    """

    if aliases is None:
        aliases = {}
    module_logger.debug("Got line " + line)
    kwargs: dict[str, str | list[str]]
    cmd, args, kwargs, line = line_to_args(line)

    if not cmd:
        print()
        return None

    funcs = list(function_dict.keys()) + list(aliases.keys())

    cmd, args = complete_command([cmd] + args, funcs, distributors)
    # Autocomplete_command
    if not cmd:  # If problems with the command, cmd is now empty
        return None

    # Handle aliases
    if cmd in aliases:
        cmd = aliases[cmd]

    func = function_dict[cmd]
    return func, args, kwargs
