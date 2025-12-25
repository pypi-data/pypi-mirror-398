import inspect
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable


# initialize the context variables holding argument data
func_defaulted_args: ContextVar[dict[str, Any]] = ContextVar("defaulted_args")
func_specified_args: ContextVar[dict[str, Any]] = ContextVar("specified_args")

# initialize the context variables holding parameter data
func_defaulted_params: ContextVar[list[str]] = ContextVar("defaulted_params")
func_specified_params: ContextVar[list[str]] = ContextVar("specified_params")


def func_capture_args(func: Callable) -> Callable:
    """
    Create a decorator to identify arguments in a function which were defaulted, and which were explicitly passed.

    Introspect the call to *func* and make available two dictionaries in context variables:
        - *defaulted_args*: arguments not passed, but defaulted as per their respective declarations
        - *specified_qrgs*: arguments explicitly passed (named, positionally in *args*, or keyworded in *kwargs*)

    The need for a decorator, rather than inspecting the function at its start, results from the fact that,
    once a function is executing, no metadata about which arguments were explicitly passed vs. filled in
    by default is retained. The *inspect* module can show the current values and defaults, but not the intent
    of the caller. This is why constructs like *frame.f_locals*, *args_info*, and even *Signature.bind_partial()*
    all fall short.

    :param func: the function being decorated
    :return: the return from the call to *func*
    """
    @wraps(func)
    # ruff: noqa: ANN003 - Missing type annotation for *{name}
    def wrapper(*args, **kwargs) -> Any:

        sig = inspect.signature(func)

        # bind only explicitly passed arguments
        bound_explicit = sig.bind(*args, **kwargs)
        bound_explicit.apply_defaults()

        # bind all arguments (with defaults applied)
        bound_all = sig.bind(*args, **kwargs)
        bound_all.apply_defaults()

        # All parameters with defaults
        with_defaults = {
            name for name, param in sig.parameters.items()
            if param.default is not inspect.Parameter.empty
        }

        # explicitly passed arguments
        explicitly_passed: dict[str, Any] = dict(bound_explicit.arguments)

        # arguments that used default values
        used_defaults: dict[str, Any] = {
            name: bound_all.arguments[name]
            for name in with_defaults
            if name not in explicitly_passed
        }

        # Store in context variables
        func_specified_args.set(explicitly_passed)
        func_defaulted_args.set(used_defaults)

        # proceed executing the decorated function
        return func(*args, **kwargs)

    # prevent a rogue error ("View function mapping is overwriting an existing endpoint function")
    wrapper.__name__ = func.__name__

    return wrapper


def func_capture_params(func: Callable) -> Callable:
    """
    Create a decorator to identify parameters in a function which were defaulted, and which were explicitly passed.

    Introspect the call to *func* and make available two lists in context variables:
        - *defaulted_params*: parameters not passed, but defaulted as per their respective declarations
        - *specified_params*: parameters explicitly passed (named, positionally in *args*, or keyworded in *kwargs*)

    The need for a decorator, rather than inspecting the function at its start, results from the fact that,
    once a function is executing, no metadata about which arguments were explicitly passed vs. filled in
    by default is retained. The *inspect* module can show the current values and defaults, but not the intent
    of the caller. This is why constructs like *frame.f_locals*, *args_info*, and even *Signature.bind_partial()*
    all fall short.

    :param func: the function being decorated
    :return: the return from the call to *func*
    """
    @wraps(func)
    # ruff: noqa: ANN003 - Missing type annotation for *{name}
    def wrapper(*args, **kwargs) -> Any:

        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        # all parameters with defaults
        with_defaults: set[str] = {
            name for name, param in sig.parameters.items()
            if param.default is not inspect.Parameter.empty
        }

        # explicitly passed parameters (from bind, before defaults applied)
        explicitly_passed: set[str] = set(sig.bind(*args, **kwargs).arguments.keys())

        # parameters that used default values
        used_defaults: set[str] = with_defaults - explicitly_passed

        # store in context variables
        func_specified_params.set(list(explicitly_passed))
        func_defaulted_params.set(list(used_defaults))

        # proceed executing the decorated function
        return func(*args, **kwargs)

    # prevent a rogue error ("View function mapping is overwriting an existing endpoint function")
    wrapper.__name__ = func.__name__

    return wrapper
