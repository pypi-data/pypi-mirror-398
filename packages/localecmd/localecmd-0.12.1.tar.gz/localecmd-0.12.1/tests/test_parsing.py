#!/usr/bin/env python3

from typing import Iterable, List, Union

import pytest
from typing_extensions import Self

from localecmd import localisation, parsing, programfunction
from localecmd.parsing import (
    complete_command,
    convert_arg,
    convert_args,
    extend_word,
    parse_line,
)


class Vector:  # pragma: no cover
    def __init__(self, values):
        if not isinstance(values, list):
            values = [values]
        self.values = [float(v) for v in values]

    def __eq__(self, other: Self):  # type:ignore
        same_length = len(self.values) == len(other.values)
        same_values = all(i == j for i, j in zip(self.values, other.values))
        return same_length and same_values

    def __repr__(self):
        return 'Vector' + str(tuple(self.values))


def test_tokenising():
    assert parsing.object_to_token(8) == "8"
    assert parsing.object_to_token(8.9) == "8.9"
    assert parsing.object_to_token(-8.9) == "-8.9"
    assert parsing.object_to_token(-1) == "-1"
    assert parsing.object_to_token("b") == "b"
    assert parsing.object_to_token("a b c") == "'a b c'"


def test_word_kwarg():
    assert parsing.word_is_kwarg('-kwarg')
    assert parsing.word_is_kwarg('-k4')
    assert parsing.word_is_kwarg('-引数')  # Parameter? in Japanese
    assert parsing.word_is_kwarg('-پارامتر')  # Parameter? in Persian
    assert not parsing.word_is_kwarg('-5')
    assert not parsing.word_is_kwarg('-3.1415926')
    assert not parsing.word_is_kwarg('-3,1415926')
    assert not parsing.word_is_kwarg('-4g')


def test_parsing_args():
    assert parsing.line_to_args("") == ("", [], {}, "")
    assert parsing.line_to_args("bla") == ("bla", [], {}, "bla")
    line = "hello, world"
    assert parsing.line_to_args(line) == ("hello,", ["world"], {}, line)

    line = "edit stop 62850 Meyenburg -arr 08:15"
    args = ["stop", '62850', "Meyenburg"]
    kwargs = {"arr": "08:15"}
    assert parsing.line_to_args(line) == ("edit", args, kwargs, line)

    line = "edit stop 62850 'Frankfurt am Main Hbf' -arr 08:15 -dep 08:16"
    args = ["stop", '62850', "Frankfurt am Main Hbf"]
    kwargs = {"arr": "08:15", "dep": "08:16"}
    assert parsing.line_to_args(line) == ("edit", args, kwargs, line)

    # Test negative numbers
    line = "bla -8 -a -9"
    assert parsing.line_to_args(line) == ("bla", ['-8'], {'a': '-9'}, line)

    # Test lists in keyword arguments
    line = "bla -8 -a -9 -10 -11"
    assert parsing.line_to_args(line) == (
        "bla",
        ['-8'],
        {'a': ['-9', '-10', '-11']},
        line,
    )


def test_line_generation():
    assert parsing.args_to_line("cmd", *["arg"], **{"key": "value"}) == "cmd arg -key value"


def test_back_and_forth():
    line = "edit_stop 62850 Meyenburg 08:14 08:15 |"
    cmd, args, kwargs, line = parsing.line_to_args(line)
    assert parsing.args_to_line(cmd, *args, **kwargs) == line

    line = "edit_stop 62850 'Brügge (Prignitz)' -arr 08:14 -dep 08:15 -stop |"
    cmd, args, kwargs, line = parsing.line_to_args(line)
    assert parsing.args_to_line(cmd, *args, **kwargs) == line


def test_complete_command(capsys):
    flist = ["help", "quit", "list_all", "list_args", "list_cmds", "love_your_next"]
    dist = {"list", "love"}
    # First test word extension
    assert extend_word("help", flist, dist) == "help"
    assert extend_word("q", flist, dist) == "quit"
    assert extend_word("list_ar", flist, dist) == "list_args"
    assert extend_word("lo", flist, dist) == "love"
    assert extend_word("lo", flist, {"list"}) == "love_your_next"

    assert extend_word("list", flist, dist) == "list"
    assert extend_word("list_a", flist, dist) == ""
    assert "could be" in capsys.readouterr().out.strip()

    assert extend_word("k", flist, dist) == ""
    assert "does not exist" in capsys.readouterr().out.strip()

    # Then test actual command completion
    assert complete_command(["help"], flist, dist)[0] == "help"
    assert complete_command("q", flist, dist)[0] == "quit"
    assert complete_command(["list", "ar"], flist, dist)[0] == "list_args"
    assert complete_command(["li", "ar"], flist, dist)[0] == "list_args"

    # As long as there are no other commands starting with love
    assert complete_command(["lo"], flist, dist)[0] == "love_your_next"
    assert complete_command(["lo"], flist, {"list"})[0] == "love_your_next"

    assert complete_command(["list"], flist, dist)[0] == ""
    assert "could be" in capsys.readouterr().out.strip()

    assert complete_command(["list", "a"], flist, dist)[0] == ""
    assert "could be" in capsys.readouterr().out.strip()

    assert complete_command("k", flist, dist)[0] == ""
    assert "does not exist" in capsys.readouterr().out.strip()


def test_parse_line(capsys):
    help_str = "help"
    quit_str = "Print that program is exited"

    functions = {
        "help": lambda *x: print(help_str, *x),
        "help_program": lambda: print('help_program'),
        "quit": lambda: print(quit_str),
        "list_cmds": print,
        "list_args": print,
        "list_all": print,
    }

    ret = parse_line("help", functions, set())
    assert ret[0] == functions["help"]
    assert not ret[1]
    assert not ret[2]

    ret = parse_line("quit", functions, set())
    assert ret[0] == functions["quit"]
    assert not ret[1]
    assert not ret[2]

    # Test completion
    ret = parse_line("q", functions, set())
    assert ret[0] == functions["quit"]
    assert not ret[1]
    assert not ret[2]

    ret = parse_line("help_", functions, set())
    assert ret[0] == functions["help_program"]
    assert not ret[1]
    assert not ret[2]

    # Test that name conflict between function and distributor goes in favour of function
    ret = parse_line("h", functions, {"help"})
    assert ret[0] == functions["help"]
    assert not ret[1]
    assert not ret[2]

    ret = parse_line("h p", functions, {"help"})
    assert ret[0] == functions["help"]
    assert ret[1] == ["p"]
    assert not ret[2]

    # Test incomplete command
    # Shouldnt this raise an exception?
    parse_line("list", functions, {"list"})
    assert "incomplete" in capsys.readouterr().out.strip()

    # Test ambiguous commands
    # Shouldnt these raise an exception too?
    parse_line("list", functions, set())
    assert "could be" in capsys.readouterr().out.strip()

    parse_line("list a", functions, {"list"})
    assert "could be" in capsys.readouterr().out.strip()

    ret = parse_line("list all functions", functions, {"list"})
    assert ret[0] == functions["list_all"]
    assert ret[1] == ["functions"]
    assert not ret[2]

    # Test alias
    ret = parse_line("list all functions", functions, {"list"}, {"list_all": "help"})
    assert ret[0] == functions["help"]
    assert ret[1] == ["functions"]
    assert not ret[2]

    # Test empty line
    ret = parse_line("", functions, set())
    assert ret is None


def test_type_conversion():
    # First the obvious ones
    val = '80'
    assert convert_arg(val, str) == '80'
    assert convert_arg(val, int) == 80
    assert convert_arg(val, float) == 80.0
    with pytest.raises(TypeError):
        convert_arg(val, None)
    with pytest.raises(TypeError):
        convert_arg(val, list)
    with pytest.raises(TypeError):
        convert_arg(val, bool)

    val = '80.0'
    # Must assert that we use English as locale
    # Other languages may use comma as decimal comma (!)
    assert convert_arg(val, str) == '80.0'
    with pytest.raises(TypeError):
        convert_arg(val, int)
    assert convert_arg(val, float) == 80.0
    with pytest.raises(TypeError):
        convert_arg(val, None)
    with pytest.raises(TypeError):
        convert_arg(val, list)
    val = 'lorem ipsum'
    assert convert_arg(val, str) == 'lorem ipsum'
    with pytest.raises(TypeError):
        convert_arg(val, int)
    with pytest.raises(TypeError):
        convert_arg(val, float)
    with pytest.raises(TypeError):
        convert_arg(val, None)
    with pytest.raises(TypeError):
        convert_arg(val, bool)

    # Change locale and test again
    # Must monkey-patch program language
    orig_locale = localisation._language
    localisation._language = 'de_DE'
    val = '80,0'
    assert convert_arg(val, str) == '80,0'
    with pytest.raises(TypeError):
        convert_arg(val, int)
    assert convert_arg(val, float) == 80.0
    with pytest.raises(TypeError):
        convert_arg('80.0', float)
    with pytest.raises(TypeError):
        convert_arg(val, None)
    with pytest.raises(TypeError):
        convert_arg(val, list)

    assert convert_arg('1234,56', float) == 1234.56
    assert convert_arg('12.345,67', float) == 12345.67
    assert convert_arg('12345,67', float) == 12345.67

    localisation._language = orig_locale

    # Now union types
    val = '80'
    assert convert_arg(val, Union[str, int]) == '80'
    assert convert_arg(val, Union[int, str]) == 80
    assert convert_arg(val, Union[float, int]) == 80.0
    assert convert_arg(val, Union[int, float]) == 80
    assert convert_arg(val, Union[float, None]) == 80.0
    # Not recommended to have None first
    assert convert_arg(val, Union[None, int]) == 80
    with pytest.raises(TypeError):
        assert convert_arg('80.0', Union[int, None]) == 80.0

    # Python apparently unpacks Unions
    assert convert_arg(val, Union[Union[float, str], int]) == 80.0

    # Disallowed types:
    with pytest.raises(TypeError):
        assert convert_arg(val, dict[float, int])
    with pytest.raises(TypeError):
        assert convert_arg(val, Iterable[int])

    assert convert_arg(['1', '1'], Vector) == Vector([1, 1])
    assert convert_arg(['1'], Vector) == Vector([1])
    assert convert_arg(['1', '2', '3', '4.8'], Vector) == Vector([1, 2, 3, 4.8])


def test_bool_type_convertion():
    val = 'yes'
    assert convert_arg(val, str) == 'yes'
    with pytest.raises(TypeError):
        convert_arg(val, int)
    with pytest.raises(TypeError):
        convert_arg(val, float)
    with pytest.raises(TypeError):
        convert_arg(val, None)
    with pytest.raises(TypeError):
        convert_arg(val, list)
    assert convert_arg(val, bool)

    val = 'no'
    assert convert_arg(val, str) == 'no'
    with pytest.raises(TypeError):
        convert_arg(val, int)
    with pytest.raises(TypeError):
        convert_arg(val, float)
    with pytest.raises(TypeError):
        convert_arg(val, None)
    with pytest.raises(TypeError):
        convert_arg(val, list)
    assert not convert_arg(val, bool)


def test_calling_conversion():
    @programfunction()  # pragma: no cover # Note that b must be called as keyword argument from cli
    def func1(a: Union[List[int], int], b: List[float], **kwargs: int):  # noqa: FA100, E501
        pass

    assert convert_args(func1, a='80', b=['90', '100']) == ((80, [90.0, 100.0]), {})
    assert convert_args(func1, a=['80', '90'], b=['90', '100']) == (
        ([80, 90], [90.0, 100.0]),
        {},
    )
    with pytest.raises(TypeError):
        # Can't convert string to list
        convert_args(func1, a=['80', '90'], b='90')

    assert convert_args(func1, a=['80', '90'], b=['90', '100'], c='80') == (
        ([80, 90], [90.0, 100.0]),
        {'c': 80},
    )
    with pytest.raises(TypeError):
        # Can't convert list to int
        convert_args(func1, '1', b=['3', '1'], c=['1', '2'])

    assert convert_args(func1, '1', b=['3', '1'], c='3', d='9') == (
        (1, [3, 1]),
        {'c': 3, 'd': 9},
    )

    @programfunction()
    def dot(a: Union[Vector, float], b: Union[Vector, float]):  # pragma: no cover  # noqa: FA100
        if not isinstance(a, Vector):
            return dot(Vector(a), b)
        if not isinstance(b, Vector):
            return dot(a, Vector(b))

        return sum([i * j for i, j in zip(a.values, b.values)])

    v10 = Vector([1.0, 0])
    v11 = Vector([1.0, 1.0])
    v12 = Vector([1.0, 2.0])
    v2 = Vector([2.0])
    v1 = Vector([1.0])
    assert convert_args(dot, a=['1', '1'], b=['1', '2']) == ((v11, v12), {})
    assert convert_args(dot, a=['1', '1'], b=['2']) == ((v11, v2), {})
    assert convert_args(dot, a=['1'], b=['1', '1']) == ((v1, v11), {})
    assert convert_args(dot, a=['1'], b=['2']) == ((v1, v2), {})

    # Test injected arguments
    dotx = dot
    dotx.set_argument_substitutions(v10)
    assert dotx.prependargs == (v10,)  # For debugging test

    assert convert_args(dotx, *dotx.prependargs, b=['1', '2']) == ((v10, v12), {})


def test_partial_typing():
    @programfunction()  # pragma: no cover # Note that b must be called as keyword argument from cli
    def func1(a: Union[List[int], int], b, **kwargs: int):  # noqa: FA100
        pass

    assert convert_args(func1, a='80', b=['90', '100']) == ((80, ['90', '100']), {})
