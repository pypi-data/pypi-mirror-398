import copy
import os
import tempfile
from collections.abc import Collection
from typing import TypeVar

import numpy as np
import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

import pytnl._containers
import pytnl.containers

# ----------------------
# Configuration
# ----------------------

# Type variable constraining the array types
A = TypeVar(
    "A",
    pytnl._containers.Array_int,
    pytnl._containers.Array_float,
    pytnl._containers.Array_complex,
    pytnl._containers.Vector_int,
    pytnl._containers.Vector_float,
    pytnl._containers.Vector_complex,
)

# List of array types to test
array_types = A.__constraints__


# ----------------------
# Helper Functions
# ----------------------


def element_strategy(array_type: type[A]) -> st.SearchStrategy[int | float | complex]:
    """Return appropriate data strategy for the given array type."""
    if array_type.ValueType is int:
        # lower limits because C++ uses int64_t for IndexType
        return st.integers(min_value=-(2**63), max_value=2**63 - 1)
    elif array_type.ValueType is float:
        return st.floats(allow_nan=False, allow_infinity=False)
    else:
        return st.complex_numbers(allow_nan=False, allow_infinity=False)


def create_array(data: Collection[int | float | complex], array_type: type[A]) -> A:
    """Create an array of the given type from a list of values."""
    v = array_type(len(data))
    for i, val in enumerate(data):
        v[i] = val  # type: ignore[assignment]
    return v


# ----------------------
# Hypothesis Strategies
# ----------------------


@st.composite
def array_strategy(draw: st.DrawFn, array_type: type[A]) -> A:
    """Generate an array of the given type."""
    data = draw(st.lists(element_strategy(array_type), max_size=20))
    return create_array(data, array_type)


# ----------------------
# Constructors and basic properties
# ----------------------


def test_pythonization() -> None:
    assert pytnl.containers.Array[bool] is pytnl._containers.Array_bool
    assert pytnl.containers.Array[int] is pytnl._containers.Array_int
    assert pytnl.containers.Array[float] is pytnl._containers.Array_float
    assert pytnl.containers.Array[complex] is pytnl._containers.Array_complex
    assert pytnl.containers.Vector[int] is pytnl._containers.Vector_int
    assert pytnl.containers.Vector[float] is pytnl._containers.Vector_float
    assert pytnl.containers.Vector[complex] is pytnl._containers.Vector_complex


def test_typedefs() -> None:
    for array_type in array_types:
        assert array_type.IndexType is int

    assert pytnl.containers.Array[bool].ValueType is bool
    assert pytnl.containers.Array[int].ValueType is int
    assert pytnl.containers.Array[float].ValueType is float
    assert pytnl.containers.Array[complex].ValueType is complex

    assert pytnl.containers.Vector[int].ValueType is int
    assert pytnl.containers.Vector[float].ValueType is float
    assert pytnl.containers.Vector[complex].ValueType is complex


@pytest.mark.parametrize("array_type", array_types)
def test_constructors(array_type: type[A]) -> None:
    v1 = array_type()
    assert v1.getSize() == 0

    v2 = array_type(10)
    assert v2.getSize() == 10

    value = 3.14 if array_type.ValueType is float else 3
    v3 = array_type(5, value)  # type: ignore[arg-type]
    assert v3.getSize() == 5
    for i in range(5):
        assert v3[i] == value

    with pytest.raises(ValueError):
        array_type(-1)


# ----------------------
# Size management
# ----------------------


@pytest.mark.parametrize("array_type", array_types)
@given(size=st.integers(min_value=0, max_value=20))
def test_setSize(array_type: type[A], size: int) -> None:
    v = array_type()
    v.setSize(size)
    assert v.getSize() == size


@pytest.mark.parametrize("array_type", array_types)
@given(size=st.integers(min_value=-20, max_value=-1))
def test_setSize_negative(array_type: type[A], size: int) -> None:
    v = array_type()
    with pytest.raises(ValueError):
        v.setSize(size)


@pytest.mark.parametrize("array_type", array_types)
@given(size=st.integers(min_value=0, max_value=20))
def test_resize(array_type: type[A], size: int) -> None:
    v = array_type()
    v.resize(size)
    assert v.getSize() == size


@pytest.mark.parametrize("array_type", array_types)
@given(size=st.integers(min_value=-20, max_value=-1))
def test_resize_negative(array_type: type[A], size: int) -> None:
    v = array_type()
    with pytest.raises(ValueError):
        v.resize(size)


@pytest.mark.parametrize("array_type", array_types)
@given(size=st.integers(min_value=0, max_value=20), value=st.integers(min_value=-(2**63), max_value=2**63 - 1))
def test_resize_with_value(array_type: type[A], size: int, value: int | float | complex) -> None:
    if array_type.ValueType is float:
        assert not isinstance(value, complex)
        value = float(value)
    elif array_type.ValueType is complex:
        value = complex(value)
    v = array_type()
    v.resize(size, value)  # type: ignore[arg-type]
    assert v.getSize() == size
    for i in range(size):
        assert v[i] == value


@pytest.mark.parametrize("array_type", array_types)
def test_swap(array_type: type[A]) -> None:
    v1 = array_type(5)
    v2 = array_type(10)
    v1.swap(v2)
    assert v1.getSize() == 10
    assert v2.getSize() == 5


@pytest.mark.parametrize("array_type", array_types)
def test_reset(array_type: type[A]) -> None:
    v = array_type(10)
    v.reset()
    assert v.getSize() == 0


@pytest.mark.parametrize("array_type", array_types)
def test_empty(array_type: type[A]) -> None:
    v = array_type()
    assert v.empty()
    v.setSize(1)
    assert not v.empty()


# ----------------------
# Data access
# ----------------------


@pytest.mark.parametrize("array_type", array_types)
@given(data=st.data())
def test_set_get_element(array_type: type[A], data: st.DataObject) -> None:
    elements = data.draw(st.lists(element_strategy(array_type), min_size=0, max_size=20))
    v = create_array(elements, array_type)
    for i in range(len(elements)):
        assert v[i] == elements[i]
        assert v.getElement(i) == elements[i]
        v.setElement(i, 42)
        assert v[i] == 42
        assert v.getElement(i) == 42
        v[i] = 1
        assert v[i] == 1
        assert v.getElement(i) == 1


@pytest.mark.parametrize("array_type", array_types)
def test_out_of_bounds_access(array_type: type[A]) -> None:
    v = array_type(1)
    with pytest.raises(IndexError):
        v[-1]
    with pytest.raises(IndexError):
        v.getElement(-1)
    with pytest.raises(IndexError):
        v.setElement(-1, 0)
    with pytest.raises(IndexError):
        v[1]
    with pytest.raises(IndexError):
        v.getElement(1)
    with pytest.raises(IndexError):
        v.setElement(1, 0)


@pytest.mark.parametrize("array_type", array_types)
@given(
    data=st.data(),
    size=st.integers(min_value=0, max_value=20),
    start=st.integers(min_value=0, max_value=10),
    stop=st.integers(min_value=0, max_value=20),
    step=st.integers(min_value=1, max_value=5),
)
def test_slicing(array_type: type[A], data: st.DataObject, size: int, start: int, stop: int, step: int) -> None:
    assume(start < stop)
    elements = data.draw(st.lists(element_strategy(array_type), min_size=size, max_size=size))
    v = create_array(elements, array_type)
    slice_ = slice(start, stop, step)
    result = v[slice_]
    expected = elements[slice_]
    assert result.getSize() == len(expected)
    for i in range(result.getSize()):
        assert result[i] == expected[i]


# ----------------------
# Assignment
# ----------------------


@pytest.mark.parametrize("array_type", array_types)
@given(data=st.data())
def test_assign(array_type: type[A], data: st.DataObject) -> None:
    v1 = data.draw(array_strategy(array_type))
    v2 = array_type()
    v2.assign(v1)
    assert v2.getSize() == v1.getSize()
    for i in range(v1.getSize()):
        assert v2[i] == v1[i]


# ----------------------
# Comparison operators
# ----------------------


@pytest.mark.parametrize("array_type", array_types)
@given(data=st.data())
def test_comparison_operators(array_type: type[A], data: st.DataObject) -> None:
    size = data.draw(st.integers(min_value=0, max_value=20))
    elements1 = data.draw(st.lists(element_strategy(array_type), min_size=size, max_size=size))
    elements2 = data.draw(st.lists(element_strategy(array_type), min_size=size, max_size=size))
    v1 = create_array(elements1, array_type)
    v2 = create_array(elements2, array_type)

    assert (v1 == v2) == (elements1 == elements2)
    assert (v1 != v2) == (elements1 != elements2)


# ----------------------
# Fill (setValue)
# ----------------------


@pytest.mark.parametrize("array_type", array_types)
@given(
    data=st.data(),
    size=st.integers(min_value=0, max_value=20),
    begin=st.integers(min_value=0, max_value=20),
    end=st.integers(min_value=0, max_value=20),
)
def test_setValue(array_type: type[A], data: st.DataObject, size: int, begin: int, end: int) -> None:
    assume(begin <= end <= size)
    elements = data.draw(st.lists(element_strategy(array_type), min_size=size, max_size=size))
    value = data.draw(element_strategy(array_type))

    v = create_array(elements, array_type)
    v.setValue(value, begin, end)  # type: ignore[arg-type]
    # adjust according to C++ behavior
    if end == 0:
        end = size
    for i in range(size):
        if begin <= i < end:
            assert v[i] == value
        else:
            assert v[i] == elements[i]


# ----------------------
# File I/O
# ----------------------


@pytest.mark.parametrize("array_type", array_types)
def test_serialization_type(array_type: type[A]) -> None:
    assert array_type.getSerializationType().startswith("TNL::Containers::Array<")


@pytest.mark.parametrize("array_type", array_types)
@given(data=st.data())
def test_save_load(array_type: type[A], data: st.DataObject) -> None:
    # Unfortunately functions-scoped fixtures like tmp_path do not work with Hypothesis
    # https://hypothesis.readthedocs.io/en/latest/reference/api.html#hypothesis.HealthCheck.function_scoped_fixture
    # Create a temporary file that will not be deleted automatically
    with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as tmpfile:
        filename = tmpfile.name

    try:
        v1 = data.draw(array_strategy(array_type))
        v1.save(str(filename))
        v2 = array_type()
        v2.load(str(filename))
        assert v2.getSize() == v1.getSize()
        for i in range(v1.getSize()):
            assert v2[i] == v1[i]

    finally:
        # Ensure the file is deleted after the test
        os.unlink(filename)


# ----------------------
# String representation
# ----------------------


@pytest.mark.parametrize("array_type", array_types)
def test_str(array_type: type[A]) -> None:
    v = array_type(5)
    for i in range(5):
        v[i] = i
    s = str(v)
    assert isinstance(s, str)
    assert len(s) > 0


# ----------------------
# Deepcopy support
# ----------------------


@pytest.mark.parametrize("array_type", array_types)
@given(data=st.data())
def test_copy(array_type: type[A], data: st.DataObject) -> None:
    v = data.draw(array_strategy(array_type))
    v_copy = copy.copy(v)
    assert v == v_copy
    if v.getSize() > 0:
        if array_type.ValueType is int:
            v_copy[0] = -v_copy[0] - 1  # pyright: ignore[reportArgumentType, reportCallIssue]
        else:
            v_copy[0] = -v_copy[0] or 1  # pyright: ignore[reportArgumentType, reportCallIssue]
        assert v_copy != v


@pytest.mark.parametrize("array_type", array_types)
@given(data=st.data())
def test_deepcopy(array_type: type[A], data: st.DataObject) -> None:
    v = data.draw(array_strategy(array_type))
    v_copy = copy.deepcopy(v)
    assert v == v_copy
    if v.getSize() > 0:
        if array_type.ValueType is int:
            v_copy[0] = -v_copy[0] - 1  # pyright: ignore[reportArgumentType, reportCallIssue]
        else:
            v_copy[0] = -v_copy[0] or 1  # pyright: ignore[reportArgumentType, reportCallIssue]
        assert v_copy != v


# ----------------------
# DLPack protocol (NumPy interoperability)
# ----------------------


@pytest.mark.parametrize("array_type", array_types)
@given(data=st.data())
def test_dlpack(array_type: type[A], data: st.DataObject) -> None:
    """
    Tests interoperability with NumPy using the DLPack API.

    Verifies:
    - The returned NumPy array has the correct shape and dtype.
    - The array contains the same data as the Array.
    - The underlying memory is shared.
    - Changes in NumPy are reflected in the Array and vice versa.
    """

    # Create and initialize the Array
    array = data.draw(array_strategy(array_type))
    assume(array.getSize() > 1)
    dims = (array.getSize(),)

    # Convert to NumPy array
    array_np = np.from_dlpack(array)

    # Check that the array is writable
    assert array_np.flags.writeable

    # Check shape
    assert array_np.shape == dims, f"Expected shape {dims}, got {array_np.shape}"

    # Check data type
    if array_type.ValueType is int:
        assert array_np.dtype == np.int_, f"Expected dtype {np.int_}, got {array_np.dtype}"
    elif array_type.ValueType is float:
        assert array_np.dtype == np.float64, f"Expected dtype {np.float64}, got {array_np.dtype}"
    else:
        assert array_np.dtype == np.complex128, f"Expected dtype {np.complex128}, got {array_np.dtype}"

    # Check element-wise equality
    assert np.all(array_np == list(array)), "Data mismatch in NumPy array"

    # Modify NumPy array and verify Array reflects the change
    array_np.flat[0] = 99
    assert array[0] == 99, "NumPy array modification not reflected in Array"

    # Modify Array and verify NumPy array reflects the change
    array[1] = 77
    assert array_np.flat[1] == 77, "Array modification not reflected in NumPy array"
