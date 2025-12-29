#!/usr/bin/env python3
""" """

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable

from typing_extensions import Self

from localecmd.localisation import d_

module_logger = logging.getLogger("Topic")


class Topic:
    """
    A topic to get help on from the command line but is not callable.

    In the CLI, the docstring is printed when with the command `help <topicname>`
    where `<topicname>` is the name of the topic.
    """

    def __init__(self, name: str, doc: str | None, translate_function: Callable = d_):
        """
        Create topic.

        :param str name: Name of the topic.
        :param str doc: The text that should be printed. For more information, see below.
        :param Callable  translate_function: Function to translate topic name.
        For more information, see below.
        Defaults to {py:func}`localecmd.localisation.d_`

        The text is mostly printed as it is, but consider that:
        - The intentation of a multiline string will be fixed with inspect.cleandoc.
        - Markdown format is useful if helptexts are generated and translated.
        - The text will be translated.

        The translation function must take one arguments: the string to translate.

        """
        self.name = name

        if doc is None:
            doc = ""
        self.doc = inspect.cleandoc(doc)
        self.sphinx_directive = 'topic'

        # To be loaded by module
        self.__translated_doc__ = ""

        self._module = None
        self._modulename = ""

        # Translate function
        self.d_ = translate_function
        # Todo: Check that this function is valid and takes one parameter

    def set_module(self, module) -> None:
        """
        Set module and modulename properties explicitly.

        :param Module module: {py:class}`~localecmd.module.Module` this function belongs to.

        """
        # Sadly, can't test isinstance(module, Module) because we can't load localecmd.module here
        # As that would be a circular import.
        assert module.__class__.__name__ == "Module"
        self._module = module
        self._modulename = module.name

    @property
    def module(self):
        "Python module the function was in"
        return self._module

    # Is useful for sorting
    @property
    def modulename(self) -> str:
        "Name of the module the function was in without path"
        return self._modulename

    @property
    def translated_name(self) -> str:
        """Translated name"""
        return self.d_(self.name)

    @property
    def fullname(self) -> str:
        """Untranslated name with module as prefix"""
        return self.modulename + "." + self.name

    @property
    def program_doc(self) -> str:
        """Function docstring to show in program"""
        if self.__translated_doc__:
            return self.__translated_doc__
        else:
            msg = "No translated doc loaded. Use the raw one."
            module_logger.info(msg)
            return self.title + '\n\n' + self.doc

    @program_doc.setter
    def program_doc(self, doc: str) -> None:
        """Replace translated docstring with `doc`"""
        self.__translated_doc__ = str(doc)

    @property
    def title(self) -> str:
        """Header for the section in the docs"""
        return self.name.capitalize()

    @property
    def oneliner(self) -> str:
        """First line of docstring that shortly describes what the function does"""
        # Finds first line in markdown document that contatins something and is not a heading
        if self.__translated_doc__:
            # Loop below will never complete because of return statement at first opportunity
            for line in self.__translated_doc__.split("\n"):  # pragma: no branch
                if line and not line.startswith("#"):
                    return line
        # Or if it is just a python docstring, it is the first line
        lines = self.doc.split("\n")
        return lines[0]

    @classmethod
    def from_type(cls, typ: Callable, doc: str = "", translate_function: Callable = d_) -> Self:
        """
        Create a helptext (topic) about a type.

        This should be done for all types.

        :param Callable typ: Type or type converter to inform about
        :param str doc: Helptext. For formatting, see {py:class}`Topic`.
        If empty, the docstring of `typ` is used
        :param Callable | None translate_function: Function to translate topic name.
        For more information, , see {py:class}`Topic`. Defaults to None.

        """
        name = typ.__name__
        if not doc and typ.__doc__:
            doc = typ.__doc__
        return cls(name, doc, translate_function)
