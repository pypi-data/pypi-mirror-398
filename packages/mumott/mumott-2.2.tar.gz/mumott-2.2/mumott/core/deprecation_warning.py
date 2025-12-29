import warnings
import functools
from inspect import isfunction, isclass
from typing import Union


def print_deprecation_warning(warning_message: str, stack_level: int = 3):
    warnings.simplefilter('always', DeprecationWarning)  # turn off filter
    warnings.warn(warning_message,
                  category=DeprecationWarning,
                  stacklevel=3)
    warnings.simplefilter('default', DeprecationWarning)  # reset filter


def deprecated(extra_message: str = ''):
    """This is a decorator which can be used to mark classes
    and functions as deprecated. It will result in a warning being emitted
    when the function is used.

    Parameters
    ----------
    dep_obj
        The object (a class or function) to be deprecated.
    extra_message
        A string that will be printed after the standard deprecation warning,
        used to, e.g., suggest usage of a different object. Default is an empty string.
    """
    def deprecated_inner(dep_obj: Union[type, callable]):
        return_class = False
        if isclass(dep_obj):
            obj_name = 'Class'
            return_class = True
        elif isfunction(dep_obj):
            obj_name = 'Function/Method'
        else:
            raise TypeError(f'Unknown object type {type(dep_obj)}!')

        if not return_class:
            @functools.wraps(dep_obj)
            def new_obj(*args, **kwargs):
                print_deprecation_warning(f'{obj_name} {dep_obj.__name__} is deprecated and will be '
                                          f'removed with the next major version' + extra_message)
                return dep_obj(*args, **kwargs)
            return new_obj
        else:
            orig_init = dep_obj.__init__

            def __init__(self, *args, **kwargs):
                print_deprecation_warning(f'{obj_name} {dep_obj.__name__} is deprecated and will be '
                                          f'removed with the next major version' + extra_message)
                orig_init(self, *args, **kwargs)
            dep_obj.__init__ = __init__
            return dep_obj
    return deprecated_inner
