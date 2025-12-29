#!/usr/bin/env python3
from localecmd.localisation import d_
from localecmd.module import Module
from localecmd.topic import Topic


def dummy_d_(y):  # pragma: no cover # Doesnt need to be run
    return y


def dummy_f_(x, y):  # pragma: no cover # Doesnt need to be run
    return y


def test_topic():
    name = "haha"
    text = """Lorem ipsum dolor sit amet.
    Consectetur adipiscing elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua.
    Ut enim ad minim veniam, 
    quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat. 
    Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. 
    Excepteur sint obcaecat cupiditat non proident, 
    sunt in culpa qui officia deserunt mollit anim id est laborum.
    """
    t = Topic(name, text, translate_function=dummy_d_)
    # Show that properties are the expected ones
    assert t.doc.startswith("Lorem ipsum dolor sit amet.\nConsectetur")
    assert t.name == name
    assert t.name == "haha"
    assert t.module is None
    assert t.modulename == ""
    assert t.fullname == ".haha"
    assert t.translated_name == name
    assert t.d_ == dummy_d_

    # Todo: Check non-valid translation functions


def test_type_topic():
    # Test
    t = Topic.from_type(list)
    mod = Module('test_typic', [t])
    assert t.doc == list.__doc__
    assert t.name == 'list'
    assert t.module == mod
    assert t.modulename == 'test_typic'
    assert t.fullname == 'test_typic.list'
    assert t.d_ == d_


def test_translation():
    # Test first that dict works
    # But need to test in English since translations may not be known.
    # Don't want to mess with the proper translations functions here
    name = "haha"
    # parameters = "a b c d".split()  # for clarity

    t = Topic(name, 'bla', translate_function=lambda x: x.upper())
    assert t.translated_name == "HAHA"


def test_docs():
    t = Topic(
        "calling",
        """How to call functions
        
        To call a function, type the name of the function into the cli and press enter.
        Arguments follow the function name....
        """,
        dummy_f_,
    )

    assert t.oneliner == "How to call functions"

    doc = (
        ":::{topic} Calling"
        + """
        :label: calling
        
        How to call functions
        
        To call a function, type the name of the function into the cli and press enter.
        Arguments follow the function name....
        :::
    """
    )

    # Test the docstring seen within the program
    assert t.program_doc.startswith('Calling')
    assert t.program_doc.split()[1:] == doc.split()[4:-1]
    # Now set the docs to something else and see if those have changed
    teststring = "### Hello, world\nhelloworld"
    t.program_doc = teststring
    assert t.program_doc == teststring
    # And the oneliner should also have changed
    assert t.oneliner == "helloworld"
