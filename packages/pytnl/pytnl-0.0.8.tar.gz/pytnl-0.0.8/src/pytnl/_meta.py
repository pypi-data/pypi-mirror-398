from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any, Literal, TypeGuard, cast, get_args

import pytnl.devices

# value types
type VT = int | float | complex

# device types
type DT = pytnl.devices.Host | pytnl.devices.Cuda

# static dimensions
type DIMS = Literal[1, 2, 3]

# general type for the `items` argument in `__getitem__`
type ItemType = type[Any] | DIMS


def is_dim_guard(dim: int) -> TypeGuard[DIMS]:
    """Verify if given `dim` satisfies the `DIMS` literal type at runtime."""
    DimsType = DIMS.__value__
    return dim in get_args(DimsType)


# Unfortunately __class_getitem__ is reserved for typing generics.
# But using __getitem__ in a metaclass allows us to implement the same API
# with non-reserved elements.
# See https://stackoverflow.com/a/77754379
class CPPClassTemplate(type):
    """
    Base metaclass for C++ class template wrappers.

    This class provides shared functionality for dynamically resolving C++ classes
    based on type parameters using Python's `__getitem__` syntax.
    Prevents direct instantiation and allows the target module and class lookup
    to be configured.

    Class attributes:

        _cpp_module (ModuleType):
            The Python module where C++ classes are looked up.

        _class_prefix (str):
            The prefix of the C++ classes to look up.

        _template_parameters (tuple[str, type]):
            The arguments of the `__getitem__` method to validate and use for
            looking up the C++ class template.

        _device_parameter (str):
            Optional special template parameter that activates dispatching
            the C++ class lookup into different device-specific modules.
            Example: `_device_parameter = "device_type"` -> the `device_type`
            template parameter decides the module (`Host` means use `_cpp_module`,
            `Cuda` means use `_cpp_module + "_cuda"`, etc.)

        _dispatch_same_module_parameter (str):
            Optional special template parameter that activates dispatching
            the C++ class lookup into the same module that contains the class
            given as the specified template parameter.
            Example: `_dispatch_same_module_parameter = "array_type"` -> the
            module that contains the `array_type` given as argument to
            `__getitem__` is used for lookup.
    """

    # Configurable module for C++ class resolution
    _cpp_module: ModuleType

    # Configurable prefix of the C++ class
    _class_prefix: str

    # Configurable tuple of arguments for the __getitem__ method
    _template_parameters: tuple[tuple[str, type], ...]

    # Optional special template parameter that activates dispatching the C++
    # class lookup into different device-specific modules.
    _device_parameter: str = ""

    # Optional special template parameter that activates dispatching
    # the C++ class lookup into the same module that contains the class
    # given as the specified template parameter.
    _dispatch_same_module_parameter: str = ""

    def _get_cpp_class(self, items: tuple[ItemType, ...]) -> type[Any]:
        """
        Resolves the appropriate C++-exported class based on the provided type parameters.

        Validates the input and constructs the class name using `_validate_params`.
        Raises an error if the class is not found in the configured module.
        """
        module, class_name = self._validate_params(items)

        if not hasattr(module, class_name):
            raise ValueError(f"Class '{class_name}' not found in module '{module.__name__}'. Ensure it is properly exported from C++.")
        return cast(type[Any], getattr(module, class_name))

    def _validate_params(self, items: tuple[ItemType, ...]) -> tuple[ModuleType, str]:
        """
        Validates the parameters passed to `__getitem__` and returns the corresponding
        module and class name.
        """
        item_names = [name for name, _ in self._template_parameters]
        if len(items) != len(item_names):
            raise TypeError(f"{self.__name__} must be subscripted with {len(item_names)} arguments: {item_names}")

        module = self._cpp_module
        class_name = self._class_prefix

        for item, pair in zip(items, self._template_parameters):
            if pair[1] is type:
                if not isinstance(item, type):
                    raise TypeError(f"{pair[0]} must be a type, got {item}")
                # device type handling and module dispatching
                if pair[0] == self._device_parameter:
                    # host is special - no suffix, use the configured module
                    if item is pytnl.devices.Host:
                        pass
                    else:
                        # add the suffix to the module and lazy-import it
                        module_name = f"{module.__name__}_{item.__name__.lower()}"
                        module = importlib.import_module(module_name)
                elif pair[0] == self._dispatch_same_module_parameter:
                    # dispatch lookup into the module that contains the given type
                    module = importlib.import_module(item.__module__)
                    # add the suffix to the class name as usual
                    class_name += f"_{item.__name__}"
                else:
                    # normal handling - add the suffix to the class name
                    class_name += f"_{item.__name__}"
            else:
                if not isinstance(item, pair[1]):
                    raise TypeError(f"{pair[0]} must be an instance of {pair[1].__name__}, got {item}")
                class_name += f"_{item}"

        return module, class_name
