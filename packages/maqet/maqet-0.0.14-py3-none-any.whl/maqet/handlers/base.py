import inspect
from abc import ABC
from typing import Callable

from maqet.logger import LOG


# TODO: Did you replaced ready solution of benedict with this? Why?
class DotDict(dict):
    """
    Dictionary with dot notation access
    Replaces python-benedict for simple attribute-style dict access
    """

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{key}'")


class HandlerError(Exception):
    """
    Handler error
    """


class Handler(ABC):
    """
    Interface for Maqet state processors
    """
    __METHODS = {}

    @classmethod
    def method(self, function: Callable = None, **kwargs):
        """
        Decorator to add method to handler methods

        Validates that handler methods have the expected signature:
        method(state: dict, *args, **kwargs)

        Can be used as:
            @Handler.method
            def my_handler(state: dict): ...

        Or with custom name:
            @Handler.method(name='custom_name')
            def my_handler(state: dict): ...
        """
        def decorator(func: Callable):
            name = kwargs.get('name', func.__name__)
            handler_name = self.__name__
            if handler_name not in self.__METHODS:
                self.__METHODS[handler_name] = {}

            # Validate handler method signature
            self._validate_handler_signature(func, name)

            self.__METHODS[handler_name][name] = func

            # TODO: This logic was totally copied from previous version of maqet.
            # Maybe there is more elegant solution? In perfect case - there should be no common dictionary
            # for all handlers. Every inherited class has it's registered methods
            # And at all - maybe there is an alternative to do same job as handlers, but easier?

            def stub(*args, **stub_kwargs):
                raise HandlerError("Handler method called outside of handler")

            return stub

        # Support both @Handler.method and @Handler.method(name='...')
        if function is not None:
            # Called as @Handler.method (without parentheses)
            return decorator(function)
        else:
            # Called as @Handler.method(...) (with parentheses)
            return decorator

    @classmethod
    def _validate_handler_signature(self, function: Callable, name: str) -> None:
        """
        Validate that a handler method has the expected signature.

        Expected signature: method(state: dict, *args, **kwargs)

        Args:
            function: The handler method to validate
            name: The name of the handler method

        Raises:
            HandlerError: If the signature is invalid
        """
        sig = inspect.signature(function)
        params = list(sig.parameters.values())

        if len(params) == 0:
            raise HandlerError(
                f"Handler method '{
                    name}' must have at least one parameter 'state'"
            )

        first_param = params[0]

        # Check first parameter is named 'state'
        if first_param.name != 'state':
            raise HandlerError(
                f"Handler method '{
                    name}' first parameter must be named 'state', "
                f"got '{first_param.name}'"
            )

        # Check if state has type annotation and if so, verify it's dict
        if first_param.annotation != inspect.Parameter.empty:
            # Handle both dict and typing.Dict annotations
            annotation_str = str(first_param.annotation)
            if 'dict' not in annotation_str.lower():
                raise HandlerError(
                    f"Handler method '{
                        name}' state parameter should be annotated as 'dict', "
                    f"got '{first_param.annotation}'"
                )

    def __init__(self, state: dict,
                 argument: list | dict | str,
                 *args, **kwargs):

        # Use state directly if it's already a DotDict, otherwise wrap it
        self.state = state if isinstance(state, DotDict) else DotDict(state)
        self.error_fatal = kwargs.get('error_fatal', False)

        self.__execute(argument)

    def __execute(self, argument: list | dict | str):
        if isinstance(argument, list):
            LOG.debug(f"Argument {argument} - splitting into subarguments")
            for subargument in argument:
                self.__execute(subargument)
        elif isinstance(argument, dict):
            LOG.debug(f"Argument {argument} - running by key-value")
            for method_name, subargument in argument.items():
                self.__call_method(method_name, subargument)
        elif isinstance(argument, str):
            LOG.debug(f"Argument {argument} - running without argument")
            self.__call_method(argument, None)
        else:
            self.__fail("Type check error"
                        f" {argument} is not list | dict | str")

    @classmethod
    def method_exists(self, method_name: str) -> bool:
        if method_name not in self.__METHODS[self.__name__]:
            LOG.debug(f"{self.__name__}::{method_name} not exists")
            return False
        LOG.debug(f"{self.__name__}::{method_name} exists")
        return True

    @classmethod
    def get_methods(self) -> list:
        return self.__METHODS[self.__name__].keys()

    def __call_method(self,
                      method_name: str,
                      argument: list | dict | str = None):

        if not self.method_exists(method_name):
            self.__fail(f"Method '{method_name}' not available"
                        f" in {self.__class__.__name__}")
        method = self.__METHODS[self.__class__.__name__].get(method_name)

        LOG.debug(f"Inspecting signature for {
                  method_name}: {inspect.signature(method)}")
        LOG.debug(f"{self.__class__.__name__}::"
                  f"{method.__name__}({str(argument)})")
        try:
            if isinstance(argument, list):
                method(self.state, *argument)
            elif isinstance(argument, dict):
                method(self.state, **argument)
            elif argument is None:
                method(self.state)
            else:
                method(self.state, argument)
        except Exception as exc:
            msg = f"{method_name}({argument}) execution error\n{exc}\n"
            self.__fail(msg)

    def __fail(self, msg: str):
        if self.error_fatal:
            raise HandlerError(msg)
        else:
            LOG.error(msg)
