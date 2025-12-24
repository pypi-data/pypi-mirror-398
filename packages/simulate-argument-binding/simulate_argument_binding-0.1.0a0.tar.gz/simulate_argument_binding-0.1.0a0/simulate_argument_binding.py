# Copyright (c) 2025 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
from collections import OrderedDict
from itertools import chain
from typing import Mapping, Optional, Sequence, TypeVar

V = TypeVar('V')


def simulate_argument_binding(
        posonlyargs,  # type: Sequence[str],
        args,  # type: Sequence[str]
        vararg,  # type: Optional[str]
        kwonlyargs,  # type: Sequence[str]
        varkwarg,  # type: Optional[str]
        defaults,  # type: Mapping[str, V]
        provided_args,  # type: Sequence[V]
        provided_kwargs,  # type: Mapping[str, V]
):
    """
    Simulate Python function argument binding.

    Parameters:
        posonlyargs: Sequence of positional-only argument names.
        args: Sequence of positional-or-keyword argument names.
        vararg: Name of the *args variable.
        kwonlyargs: Sequence of keyword-only argument names.
        varkwarg: Name of the **kwargs variable.
        defaults: Mapping of argument names to default values.
        provided_args: Sequence of values supplied as positional arguments.
        provided_kwargs: Mapping of values supplied as keyword arguments.

    Returns:
        OrderedDict mapping parameter names to their bound values.

    Raises:
        TypeError: On missing, duplicate, or extra arguments.
    """
    # Initialize with defaults and a sentinel representing a missing argument
    binding = OrderedDict()
    sentinel = object()

    for posonlyarg in posonlyargs:
        if posonlyarg in defaults:
            binding[posonlyarg] = defaults[posonlyarg]
        else:
            binding[posonlyarg] = sentinel

    for arg in args:
        if arg in defaults:
            binding[arg] = defaults[arg]
        else:
            binding[arg] = sentinel

    if vararg is not None:
        binding[vararg] = tuple()

    for kwonlyarg in kwonlyargs:
        if kwonlyarg in defaults:
            binding[kwonlyarg] = defaults[kwonlyarg]
        else:
            binding[kwonlyarg] = sentinel

    if varkwarg is not None:
        binding[varkwarg] = OrderedDict()

    user_filled_args_and_kwonlyargs = set()

    # Handle positional arguments
    # Ensure all posonlyargs are bound
    # Record set args
    # Collect extra positional arguments and bind vararg
    for positional_arg, value in zip(chain(posonlyargs, args), provided_args):
        binding[positional_arg] = value

    if len(provided_args) < len(posonlyargs):
        missing_posonlyargs_set = set()
        for posonlyarg in posonlyargs[len(provided_args):]:
            if binding[posonlyarg] is sentinel:
                missing_posonlyargs_set.add(posonlyarg)

        if missing_posonlyargs_set:
            raise TypeError('Missing positional-only arguments: %r' % (missing_posonlyargs_set,))
    elif len(provided_args) < len(posonlyargs) + len(args):
        user_filled_args_and_kwonlyargs.update(args[:len(provided_args) - len(posonlyargs)])
    else:
        user_filled_args_and_kwonlyargs.update(args)

        extra_positional_args = tuple(provided_args[len(posonlyargs) + len(args):])
        if vararg is not None:
            binding[vararg] = extra_positional_args
        else:
            if extra_positional_args:
                raise TypeError('Got extra positional arguments: %r' % (extra_positional_args,))

    # Handle keyword arguments
    # Record set args and kwonlyargs
    # Cannot set args and kwonlyargs more than once
    # Ensure all args and kwonlyargs are bound
    # Collect extra keyword arguments and bind varkwarg
    extra_keyword_arguments_to_values = OrderedDict()
    for key, value in provided_kwargs.items():
        if key in args or key in kwonlyargs:
            if key in user_filled_args_and_kwonlyargs:
                raise TypeError('Got multiple values for argument %r' % (key,))
            else:
                binding[key] = value
                user_filled_args_and_kwonlyargs.add(key)
        else:
            extra_keyword_arguments_to_values[key] = value

    missing_args_set = set()
    for arg in args:
        if binding[arg] is sentinel:
            missing_args_set.add(arg)
    if missing_args_set:
        raise TypeError('Missing arguments: %r' % (missing_args_set,))

    missing_kwonlyargs_set = set()
    for kwonlyarg in kwonlyargs:
        if binding[kwonlyarg] is sentinel:
            missing_kwonlyargs_set.add(kwonlyarg)
    if missing_kwonlyargs_set:
        raise TypeError('Missing keyword-only arguments: %r' % (missing_kwonlyargs_set,))

    if varkwarg is not None:
        binding[varkwarg] = extra_keyword_arguments_to_values
    else:
        if extra_keyword_arguments_to_values:
            raise TypeError('Got extra keyword arguments: %r' % (extra_keyword_arguments_to_values,))

    return binding
