# !/usr/bin/env python3
from __future__ import annotations

import inspect
import logging
from typing import Any, Callable

from localecmd.localisation import _, f_
from localecmd.topic import Topic

BRAILLE_PATTERN_BLANK = "⠀"

module_logger = logging.getLogger("Function")


class Function(Topic):
    """
    Function callable from the CLI.

    This is a wrapper around the python builtin function with the advantage that
    function name, parameters and types can be translated. It adds some properties
    that are useful for translation.

    Attributes `__name__` and `__doc__` are left unchanged. To access the shown
    name, use {py:attr}`Function.name` (untranslated) or
    {py:attr}`Function.translated_name`.

    To call the function from python, use the function as every other function.
    Then, args and kwargs are passed directly.

    :param Callable func: The original function
    :param str name: Untranslated name as it will be shown in the program
    :param list[str] parameters: Untranslated function parameters
    """

    def __init__(self, func: Callable, name: str = "", translate_function: Callable = f_) -> None:
        """
        Initialize function.

        :param Callable func: Actual function that will be called
        :param str name: Name of the function as shown in program.
        If empty, the name will be as shown in python.
        :param Callable | None translate_function: Function to translate function
        name and parameter names. For more information, see below.
        Defaults to {py:func}`localecmd.localisation.f_`.

        The translation function must take two arguments: First the context,
        then the string to translate.
        For functions, the context is the module name, for parameter names, this
        is `<module name>.<funcion name>`.
        """
        if inspect.isfunction(func) or inspect.ismethod(func):
            self.func: Callable = func
        else:
            msg = _("Argument `func`  must be a function or a method! Found a {t}")
            raise ValueError(msg.format(t=type(func)))

        # Tell Python where to find signature, annotations etc.
        self.__wrapped__ = func

        # Keep name, module and doc
        self.__name__ = func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__

        # For translation
        self.__translated_doc__ = ""

        # Function name in the program
        if not name:
            name = func.__name__

        super().__init__(name, func.__doc__)
        self.f_ = translate_function
        self.sphinx_directive = 'py:function'

        self.signature = inspect.signature(func)
        self.annotations = inspect.get_annotations(func, eval_str=True)
        # Function parameters
        self.parameters = list(self.signature.parameters.keys())

        # These are changed when the function is assigned to a module
        self.prependargs = ()
        self.addkwargs: dict[str, Any] = {}

    def __call__(self, *args, **kwargs):
        """
        Call wrapped function directly.

        raises TypeMismatch: If type of arguments does not comply with function type annotations.
        """
        # Todo: Add logging
        return self.func.__call__(*args, **kwargs)

    def substitute_call(self, *args, **kwargs):
        """
        Add positional and keyword arguments that are specified in attributes
        prependargs and addkwargs.

        These attributes are written to when the function is assigned to a module.

        If there is a name conflict in the keyword arguments list, those given
        in the calling override them given from the module.
        """
        module_logger.debug(f"Substituting call to function {self.name}")
        module_logger.debug(f"Prepending arguments {self.prependargs}")
        module_logger.debug(f"Adding keyword arguments {self.addkwargs}")
        newargs = self.prependargs + args
        newkwargs = self.addkwargs | kwargs
        module_logger.debug(f"New calling: {self.name}({newargs}, {newkwargs})")
        return newargs, newkwargs

    def translate_call(self, *args, **kwargs):
        # Translate kwargs
        try:
            kwargs = {self.parameter_dictionary[k]: v for k, v in kwargs.items()}
        except KeyError as e:
            msg1 = _("Function '{fname}' has no parameter '{param}'!")
            msg2 = _("Possible parameters are: {params}")
            fmsg = '\n'.join([msg1, msg2]).format(
                fname=self.translated_name,
                param=e.args[0],
                params=list(self.parameter_dictionary.keys()),
            )
            raise KeyError(fmsg) from e

        return args, kwargs

    def set_argument_substitutions(self, *prependargs, **addkwargs) -> None:
        """
        Set arguments to prepend and add when substituing a calling.

        This sets the attributes
        {py:attr}`~localecmd.func.Function.prependargs`,
        {py:attr}`~localecmd.func.Function.addkwargs`.

        :::{note}
        All prepended positional arguments will be prepended while
        only those keyword arguments will be added which actually correspond to
        parameter names in the signature of the function.
        """
        module_logger.debug(f"Set argument substitutions for function {self.name}:")
        module_logger.debug(f"{prependargs} {addkwargs}")
        self.prependargs = prependargs
        self.addkwargs = {k: v for k, v in addkwargs.items() if k in self.parameters}

    @property
    def calling(self) -> str:
        """Generate signature of function

        Signature is on the form\n
        func positional args... -kwarg1 -kwargs...
        """
        s = self.translated_name + " "
        sig = self.signature

        for p in sig.parameters.values():
            if p.kind in [
                inspect.Parameter.KEYWORD_ONLY,
                inspect.Parameter.VAR_KEYWORD,
            ]:
                s += "-"
            s += self.f_(self.fullname, p.name)
            if p.kind == inspect.Parameter.VAR_POSITIONAL:
                s += "..."
            if p.kind == inspect.Parameter.VAR_KEYWORD:
                s += "..."
            s += " "
        return s

    @property
    def parameter_dictionary(self) -> dict[str, str]:
        """Dictionary with translated -> untranslated parameter names

        :rtype: dict[str, str]

        """
        return {self.f_(self.fullname, p).replace('_', '-'): p for p in self.parameters}

    @property
    def translated_name(self) -> str:
        """Translated name"""
        return self.f_(self.modulename, self.name)

    @property
    def title(self) -> str:
        """Header for the section in the docs"""
        return self.calling + BRAILLE_PATTERN_BLANK


def programfunction(name: str = "", translate_function: Callable = f_) -> Callable:
    """
    Wrap function such that it becomes a {py:class}`Function`.

    The decorator must be used with parentheses also when no arguments are passed:
    :::{code} python
    @programfunction()
    def some_function():
        (...)
    :::
    See {py:class}`there <Function>` under Initialization for argument description.

    """

    def decorator(func: Callable) -> Function:
        f = Function(func, name, translate_function)
        return f

    return decorator
