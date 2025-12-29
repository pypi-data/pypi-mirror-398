from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, overload

import pytnl._containers
import pytnl._meta
import pytnl.devices
from pytnl._meta import DIMS, DT, VT

if TYPE_CHECKING:
    # This is an optional module - at runtime it is lazy-imported in
    # `CPPClassTemplate`, for type checking there must be the import statement.
    import pytnl._containers_cuda as _containers_cuda  # type: ignore[import-not-found, unused-ignore]

__all__ = [
    "Array",
    "NDArray",
    "NDArrayIndexer",
    "StaticVector",
    "Vector",
]


class _ArrayMeta(pytnl._meta.CPPClassTemplate):
    _cpp_module = pytnl._containers
    _class_prefix = "Array"
    _template_parameters = (
        ("value_type", type),
        ("device_type", type),
    )
    _device_parameter = "device_type"

    # NOTE: Python's typing `float` type accepts even `int` so the overloads
    # "overlap" and `float` must be carefully ordered last so that pyright
    # selects the first overload in a tie.
    # https://stackoverflow.com/a/62734976

    @overload
    def __getitem__(  # type: ignore[overload-overlap]
        self,
        key: type[bool] | tuple[type[bool], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.Array_bool]: ...

    @overload
    def __getitem__(  # pyright: ignore[reportOverlappingOverload]
        self,
        key: type[int] | tuple[type[int], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.Array_int]: ...

    @overload
    def __getitem__(
        self,
        key: type[float] | tuple[type[float], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.Array_float]: ...

    @overload
    def __getitem__(
        self,
        key: type[complex] | tuple[type[complex], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.Array_complex]: ...

    @overload
    def __getitem__(  # type: ignore[overload-overlap, no-any-unimported, unused-ignore]
        self,
        key: tuple[type[bool], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.Array_bool]: ...  # pyright: ignore[reportUnknownMemberType]

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[type[int], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.Array_int]: ...  # pyright: ignore[reportUnknownMemberType]

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[type[float], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.Array_float]: ...  # pyright: ignore[reportUnknownMemberType]

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[type[complex], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.Array_complex]: ...  # pyright: ignore[reportUnknownMemberType]

    def __getitem__(
        self,
        key: type[bool | VT] | tuple[type[bool | VT], type[DT]],
        /,
    ) -> type[Any]:
        if isinstance(key, tuple):
            items = key
        else:
            # make a tuple of arguments, use host as the default device
            items = (key, pytnl.devices.Host)
        return self._get_cpp_class(items)


class Array(metaclass=_ArrayMeta):
    """
    Allows `Array[value_type, device_type]` syntax to resolve to
    the appropriate C++ `Array` class.

    This class provides a Python interface to C++ arrays of a specific value
    type and device type.

    The `device_type` argument is optional and defaults to `pytnl.devices.Host`.

    Examples:
    - `Array[int]` → `_containers.Array_int`
    - `Array[float, devices.Cuda]` → `_containers_cuda.Array_float`
    - `Array[complex, devices.Host]` → `_containers.Array_complex`
    """


class _VectorMeta(pytnl._meta.CPPClassTemplate):
    _cpp_module = pytnl._containers
    _class_prefix = "Vector"
    _template_parameters = (
        ("value_type", type),
        ("device_type", type),
    )
    _device_parameter = "device_type"

    # NOTE: Python's typing `float` type accepts even `int` so the overloads
    # "overlap" and `float` must be carefully ordered last so that pyright
    # selects the first overload in a tie.
    # https://stackoverflow.com/a/62734976

    @overload
    def __getitem__(  # pyright: ignore[reportOverlappingOverload]
        self,
        key: type[int] | tuple[type[int], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.Vector_int]: ...

    @overload
    def __getitem__(
        self,
        key: type[float] | tuple[type[float], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.Vector_float]: ...

    @overload
    def __getitem__(
        self,
        key: type[complex] | tuple[type[complex], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.Vector_complex]: ...

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[type[int], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.Vector_int]: ...  # pyright: ignore[reportUnknownMemberType]

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[type[float], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.Vector_float]: ...  # pyright: ignore[reportUnknownMemberType]

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[type[complex], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.Vector_complex]: ...  # pyright: ignore[reportUnknownMemberType]

    def __getitem__(
        self,
        key: type[VT] | tuple[type[VT], type[DT]],
        /,
    ) -> type[Any]:
        if isinstance(key, tuple):
            items = key
        else:
            # make a tuple of arguments, use host as the default device
            items = (key, pytnl.devices.Host)
        return self._get_cpp_class(items)


class Vector(metaclass=_VectorMeta):
    """
    Allows `Vector[value_type, device_type]` syntax to resolve to
    the appropriate C++ `Vector` class.

    This class provides a Python interface to C++ vectors of a specific value
    type and device type.

    The `device_type` argument is optional and defaults to `pytnl.devices.Host`.

    Examples:
    - `Vector[int]` → `_containers.Vector_int`
    - `Vector[float, devices.Cuda]` → `_containers_cuda.Vector_float`
    - `Vector[complex, devices.Host]` → `_containers.Vector_complex`
    """


class _StaticVectorMeta(pytnl._meta.CPPClassTemplate):
    _cpp_module = pytnl._containers
    _class_prefix = "StaticVector"
    _template_parameters = (
        ("dimension", int),
        ("value_type", type),
    )

    # NOTE: Python's typing `float` type accepts even `int` so the overloads
    # "overlap" and `float` must be carefully ordered last so that pyright
    # selects the first overload in a tie.
    # https://stackoverflow.com/a/62734976

    @overload
    def __getitem__(  # pyright: ignore[reportOverlappingOverload]
        self,
        key: tuple[Literal[1], type[int]],
        /,
    ) -> type[pytnl._containers.StaticVector_1_int]: ...

    @overload
    def __getitem__(  # pyright: ignore[reportOverlappingOverload]
        self,
        key: tuple[Literal[2], type[int]],
        /,
    ) -> type[pytnl._containers.StaticVector_2_int]: ...

    @overload
    def __getitem__(  # pyright: ignore[reportOverlappingOverload]
        self,
        key: tuple[Literal[3], type[int]],
        /,
    ) -> type[pytnl._containers.StaticVector_3_int]: ...

    @overload
    def __getitem__(
        self,
        key: tuple[Literal[1], type[float]],
        /,
    ) -> type[pytnl._containers.StaticVector_1_float]: ...

    @overload
    def __getitem__(
        self,
        key: tuple[Literal[2], type[float]],
        /,
    ) -> type[pytnl._containers.StaticVector_2_float]: ...

    @overload
    def __getitem__(
        self,
        key: tuple[Literal[3], type[float]],
        /,
    ) -> type[pytnl._containers.StaticVector_3_float]: ...

    @overload
    def __getitem__(
        self,
        key: tuple[Literal[1], type[complex]],
        /,
    ) -> type[pytnl._containers.StaticVector_1_complex]: ...

    @overload
    def __getitem__(
        self,
        key: tuple[Literal[2], type[complex]],
        /,
    ) -> type[pytnl._containers.StaticVector_2_complex]: ...

    @overload
    def __getitem__(
        self,
        key: tuple[Literal[3], type[complex]],
        /,
    ) -> type[pytnl._containers.StaticVector_3_complex]: ...

    def __getitem__(
        self,
        key: tuple[DIMS, type[VT]],
        /,
    ) -> type[Any]:
        return self._get_cpp_class(key)


class StaticVector(metaclass=_StaticVectorMeta):
    """
    Allows `StaticVector[dimension, value_type]` syntax to resolve to
    the appropriate C++ `StaticVector` class.

    This class provides a Python interface to C++ static vectors with a fixed
    dimension and value type.

    Examples:
    - `StaticVector[3, float]` → `StaticVector_3_float`
    - `StaticVector[2, int]` → `StaticVector_2_int`
    """


class _NDArrayMeta(pytnl._meta.CPPClassTemplate):
    _cpp_module = pytnl._containers
    _class_prefix = "NDArray"
    _template_parameters = (
        ("dimension", int),
        ("value_type", type),
        ("device_type", type),
    )
    _device_parameter = "device_type"

    # NOTE: Python's typing `float` type accepts even `int` so the overloads
    # "overlap" and `float` must be carefully ordered last so that pyright
    # selects the first overload in a tie.
    # https://stackoverflow.com/a/62734976

    @overload
    def __getitem__(  # pyright: ignore[reportOverlappingOverload]
        self,
        key: tuple[Literal[1], type[int]] | tuple[Literal[1], type[int], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.NDArray_1_int]: ...

    @overload
    def __getitem__(  # pyright: ignore[reportOverlappingOverload]
        self,
        key: tuple[Literal[2], type[int]] | tuple[Literal[2], type[int], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.NDArray_2_int]: ...

    @overload
    def __getitem__(  # pyright: ignore[reportOverlappingOverload]
        self,
        key: tuple[Literal[3], type[int]] | tuple[Literal[3], type[int], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.NDArray_3_int]: ...

    @overload
    def __getitem__(
        self,
        key: tuple[Literal[1], type[float]] | tuple[Literal[1], type[float], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.NDArray_1_float]: ...

    @overload
    def __getitem__(
        self,
        key: tuple[Literal[2], type[float]] | tuple[Literal[2], type[float], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.NDArray_2_float]: ...

    @overload
    def __getitem__(
        self,
        key: tuple[Literal[3], type[float]] | tuple[Literal[3], type[float], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.NDArray_3_float]: ...

    @overload
    def __getitem__(
        self,
        key: tuple[Literal[1], type[complex]] | tuple[Literal[1], type[complex], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.NDArray_1_complex]: ...

    @overload
    def __getitem__(
        self,
        key: tuple[Literal[2], type[complex]] | tuple[Literal[2], type[complex], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.NDArray_2_complex]: ...

    @overload
    def __getitem__(
        self,
        key: tuple[Literal[3], type[complex]] | tuple[Literal[3], type[complex], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._containers.NDArray_3_complex]: ...

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[Literal[1], type[int], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.NDArray_1_int]: ...  # pyright: ignore[reportUnknownMemberType]

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[Literal[2], type[int], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.NDArray_2_int]: ...  # pyright: ignore[reportUnknownMemberType]

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[Literal[3], type[int], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.NDArray_3_int]: ...  # pyright: ignore[reportUnknownMemberType]

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[Literal[1], type[float], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.NDArray_1_float]: ...  # pyright: ignore[reportUnknownMemberType]

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[Literal[2], type[float], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.NDArray_2_float]: ...  # pyright: ignore[reportUnknownMemberType]

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[Literal[3], type[float], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.NDArray_3_float]: ...  # pyright: ignore[reportUnknownMemberType]

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[Literal[1], type[complex], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.NDArray_1_complex]: ...  # pyright: ignore[reportUnknownMemberType]

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[Literal[2], type[complex], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.NDArray_2_complex]: ...  # pyright: ignore[reportUnknownMemberType]

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[Literal[3], type[complex], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_containers_cuda.NDArray_3_complex]: ...  # pyright: ignore[reportUnknownMemberType]

    def __getitem__(
        self,
        key: tuple[DIMS, type[VT]] | tuple[DIMS, type[VT], type[DT]],
        /,
    ) -> type[Any]:
        if len(key) == 2:
            # use host as the default device
            key = (*key, pytnl.devices.Host)
        return self._get_cpp_class(key)


class NDArray(metaclass=_NDArrayMeta):
    """
    Allows `NDArray[dimension, value_type, device_type]` syntax to resolve to
    the appropriate C++ `NDArray` class.

    This class provides a Python interface to C++ N-dimensional arrays of a
    specific dimension, value type, and device type.

    The `device_type` argument is optional and defaults to `pytnl.devices.Host`.

    Examples:
    - `NDArray[3, float]` → `_containers.NDArray_3_float`
    - `NDArray[2, int, devices.Cuda]` → `_containers_cuda.NDArray_2_int`
    - `NDArray[2, float, devices.Host]` → `_containers.NDArray_2_float`
    """


class _NDArrayIndexerMeta(pytnl._meta.CPPClassTemplate):
    _cpp_module = pytnl._containers
    _class_prefix = "NDArrayIndexer"
    _template_parameters = (("dimension", int),)

    @overload
    def __getitem__(
        self,
        key: Literal[1],
        /,
    ) -> type[pytnl._containers.NDArrayIndexer_1]: ...

    @overload
    def __getitem__(
        self,
        key: Literal[2],
        /,
    ) -> type[pytnl._containers.NDArrayIndexer_2]: ...

    @overload
    def __getitem__(
        self,
        key: Literal[3],
        /,
    ) -> type[pytnl._containers.NDArrayIndexer_3]: ...

    def __getitem__(
        self,
        key: DIMS,
        /,
    ) -> type[Any]:
        items = (key,)
        return self._get_cpp_class(items)


class NDArrayIndexer(metaclass=_NDArrayIndexerMeta):
    """
    Allows `NDArrayIndexer[dimension]` syntax to resolve to
    the appropriate C++ `NDArrayIndexer` class.

    This class provides a Python interface to C++ indexers for N-dimensional
    arrays with a fixed dimension.

    Examples:
    - `NDArrayIndexer[1]` → `NDArrayIndexer_1`
    - `NDArrayIndexer[2]` → `NDArrayIndexer_2`
    """
