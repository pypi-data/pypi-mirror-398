#!/usr/bin/env python3
from __future__ import annotations

import inspect
from typing import Union

import pytest

from localecmd.func import (
    BRAILLE_PATTERN_BLANK,
    Function,
    programfunction,
)
from localecmd.localisation import f_
from localecmd.module import Module


def dummy_f_(x, y):
    return y


def func(a: int = 9, *b: float, c: int | str = 8, **d: str):  # pragma: no cover
    """
    This is a docstring

    This has many lines

    """
    # A function to use for testing, but should not be tested itself
    return "func"


def func2(a: int = 9, b: float = 80, c: int = 8, d: float = 10):  # pragma: no cover
    # A function to use for testing, but should not be tested itself
    return f"{a} {b} {c} {d}"


class Bla:
    def __init__(self, e: int = 9):
        self.e = e

    def func3(self, a: int = 9):
        return f"{self.e} {a}"


def test_create_callstring():
    # Note that python allows atart to be a positional argument in bultin sum.
    f = Function(func, translate_function=dummy_f_)
    assert f.calling.strip() == "func a b... -c -d..."

    f = Function(func2, translate_function=dummy_f_)
    assert f.calling.strip() == "func2 a b c d"

    c = Bla()
    f = Function(c.func3, translate_function=dummy_f_)
    assert f.calling.strip() == "func3 a"


def test_method():
    c = Bla()
    f = Function(c.func3, translate_function=dummy_f_)
    assert f(6) == "9 6"

    c.e = 90

    assert f(6) == "90 6"


def test_func():
    name = "haha"
    parameters = ["a", "b", "c", "d"]
    param_types = [int, float, Union[int, str], str]
    f = Function(func, name, translate_function=dummy_f_)
    f2 = Function(func, translate_function=dummy_f_)
    # Test when no translation function is given
    f3 = Function(func)

    # Module assignment must be done explicitly
    Module("test_func", [f, f2, f3])
    # Show that properties are the same as of the wrapped function
    assert f.func == func
    assert f.__wrapped__ == func
    assert inspect.signature(f) == inspect.signature(func)
    assert f() == func()

    assert f.modulename == "test_func"
    assert f.fullname == "test_func.haha"
    assert f.name == name
    assert f.__name__ == "func"
    assert f.translated_name == name
    assert f.parameters == parameters
    assert f.annotations == dict(zip(parameters, param_types))
    assert f.f_ == dummy_f_

    assert f2.modulename == "test_func"
    assert f2.name == "func"
    assert f2.parameters == parameters

    assert f3.modulename == "test_func"
    assert f3.name == "func"
    assert f3.parameters == parameters
    assert f3.f_ == f_

    # Todo: Check non-valid translation functions


def test_error_if_not_callable():
    # If not function or method, Function should fail
    with pytest.raises(ValueError):
        Function(None)


def test_translation():
    # Test first that dict works
    # But need to test in English since translations may not be known.
    # Don't want to mess with the proper translations functions here
    name = "haha"
    # parameters = "a b c d".split()  # for clarity

    f = Function(func2, name, translate_function=lambda y, x: x.upper())

    paramdict = f.parameter_dictionary
    assert list(paramdict.keys()) == ["A", "B", "C", "D"]

    # Then overwrite that to see that translated call works
    args, kwargs = f.translate_call(A=10, B=20, C=30, D=40)
    assert kwargs == dict(zip('abcd', range(10, 50, 10)))

    with pytest.raises(KeyError):
        f.translate_call(A=10, E=90)


def test_wrapper():
    name = "haha"
    # parameters = "a b c d".split()  # for clarity

    f = Function(func, name, translate_function=dummy_f_)
    deco = programfunction(name, translate_function=dummy_f_)
    g = deco(func)
    Module(__name__, [f, g])

    assert f.func == g.func
    assert f.__wrapped__ == g.__wrapped__
    assert inspect.signature(f) == inspect.signature(g)
    assert f() == g()
    assert f.module == g.module

    assert f.modulename == g.modulename
    assert f.translated_name == g.translated_name
    assert f.name == g.name
    assert f.parameters == g.parameters


def test_docs():
    f1 = Function(func, "func", dummy_f_)
    f2 = Function(func2, "func2", dummy_f_)
    assert f1.oneliner == "This is a docstring"
    assert f2.oneliner == ""

    func2_doc = (
        ":::{py:function}"
        + f""" func a b... -c -d... {BRAILLE_PATTERN_BLANK}
        
        This is a docstring
    
        This has many lines
    
        :::
    """
    )

    # Test the docstring seen within the program
    assert f1.program_doc.split() == func2_doc.split()[1:-1]
    # Now set the docs to something else and see if those have changed
    teststring = "### Hello, world\nhelloworld"
    f1.program_doc = teststring
    assert f1.program_doc == teststring
    # And the oneliner should also ne changed
    assert f1.oneliner == "helloworld"
    # The oneliner should not have changed?
    # assert f.oneliner == teststring
