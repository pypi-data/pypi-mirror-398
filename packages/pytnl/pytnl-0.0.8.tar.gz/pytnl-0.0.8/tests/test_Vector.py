import copy
import math
from collections.abc import Collection
from typing import TypeVar, cast

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

import pytnl._containers
import pytnl.containers

# ----------------------
# Configuration
# ----------------------

# Type variables constraining the vector types
V = TypeVar(
    "V",
    pytnl._containers.Vector_int,
    pytnl._containers.Vector_float,
    pytnl._containers.Vector_complex,
)
Vreal = TypeVar(
    "Vreal",
    pytnl._containers.Vector_int,
    pytnl._containers.Vector_float,
)
type Vint = pytnl._containers.Vector_int

# List of vector types to test
vector_types = V.__constraints__
real_vector_types = Vreal.__constraints__


# ----------------------
# Helper Functions
# ----------------------


@st.composite
def complex_numbers(draw: st.DrawFn) -> complex:
    # avoid too small/large exponents
    real: float | None = None
    while real is None or 0 < abs(real) < 1e-30:
        real = draw(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e30, max_value=1e30))
    imag: float | None = None
    while imag is None or 0 < abs(imag) < 1e-30:
        imag = draw(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e30, max_value=1e30))
    return complex(real, imag)


def element_strategy(vector_type: type[V]) -> st.SearchStrategy[int | float | complex]:
    """Return appropriate data strategy for the given vector type."""
    if vector_type.ValueType is int:
        # lower limits because C++ uses int64_t for IndexType and we test even multiplication
        return st.integers(min_value=-(2**31), max_value=2**31)
    elif vector_type.ValueType is float:
        return st.floats(allow_nan=False, allow_infinity=False)
    else:
        return complex_numbers()


def create_vector(data: Collection[int | float | complex], vector_type: type[V]) -> V:
    """Create a vector of the given type from a list of values."""
    v = vector_type(len(data))
    for i, val in enumerate(data):
        v[i] = val  # type: ignore[assignment]
    return v


# ----------------------
# Hypothesis Strategies
# ----------------------


@st.composite
def vector_strategy(draw: st.DrawFn, vector_type: type[V]) -> V:
    """Generate a vector of the given type."""
    data = draw(st.lists(element_strategy(vector_type), max_size=20))
    return create_vector(data, vector_type)


@st.composite
def vector_pair_strategy(draw: st.DrawFn, vector_type: type[V]) -> tuple[V, V]:
    """Generate two vectors of the same size and type."""
    data1 = draw(st.lists(element_strategy(vector_type), max_size=20))
    data2 = draw(st.lists(element_strategy(vector_type), min_size=len(data1), max_size=len(data1)))
    return create_vector(data1, vector_type), create_vector(data2, vector_type)


@st.composite
def vector_scalar_strategy(draw: st.DrawFn, vector_type: type[V]) -> tuple[V, int | float | complex]:
    """Generate a vector and a scalar of the same type."""
    v = draw(vector_strategy(vector_type))
    s = draw(element_strategy(vector_type))
    return v, s


# ----------------------
# Basic Properties
# ----------------------


def test_typedefs() -> None:
    for vector_type in vector_types:
        assert vector_type.IndexType is int

    assert pytnl.containers.Vector[complex].ValueType is complex
    assert pytnl.containers.Vector[float].ValueType is float
    assert pytnl.containers.Vector[int].ValueType is int

    assert pytnl.containers.Vector[complex].RealType is complex
    assert pytnl.containers.Vector[float].RealType is float
    assert pytnl.containers.Vector[int].RealType is int


@pytest.mark.parametrize("vector_type", vector_types)
@given(size=st.integers(min_value=0, max_value=2**10))
def test_init(vector_type: type[V], size: int) -> None:
    v = vector_type(size)
    assert v.getSize() == size


@pytest.mark.parametrize("vector_type", vector_types)
@given(size=st.integers(min_value=-(2**10), max_value=-1))
def test_negative_size(vector_type: type[V], size: int) -> None:
    with pytest.raises(ValueError):
        vector_type(size)


@pytest.mark.parametrize("vector_type", vector_types)
@given(size=st.integers(min_value=0, max_value=2**10))
def test_square_brackets(vector_type: type[V], size: int) -> None:
    v = vector_type(size)
    for i in range(size):
        v[i] = i
    for i in range(size):
        assert v[i] == i


@pytest.mark.parametrize("vector_type", vector_types)
@given(size=st.integers(min_value=0, max_value=2**10))
def test_assign(vector_type: type[V], size: int) -> None:
    v1 = vector_type(size)
    for i in range(size):
        v1[i] = i
    v2 = vector_type()
    v2.assign(v1)
    assert v1 is not v2
    assert v1 == v2
    if size > 0:
        v2[0] = 99
        assert v1 != v2


# ----------------------
# Copy and Deepcopy
# ----------------------


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_copy(vector_type: type[V], data: st.DataObject) -> None:
    v = data.draw(vector_strategy(vector_type))
    v_copy = copy.copy(v)
    assert v == v_copy
    if v.getSize() > 0:
        v_copy[0] = -v_copy[0] or 1  # pyright: ignore[reportArgumentType, reportCallIssue]
        assert v_copy != v


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_deepcopy(vector_type: type[V], data: st.DataObject) -> None:
    v = data.draw(vector_strategy(vector_type))
    v_copy = copy.deepcopy(v)
    assert v == v_copy
    if v.getSize() > 0:
        v_copy[0] = -v_copy[0] or 1  # pyright: ignore[reportArgumentType, reportCallIssue]
        assert v_copy != v


# ----------------------
# Unary Operators
# ----------------------


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_unary_plus(vector_type: type[V], data: st.DataObject) -> None:
    v = data.draw(vector_strategy(vector_type))
    v2 = +v
    for i in range(v.getSize()):
        assert v2[i] == +v[i]


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_unary_minus(vector_type: type[V], data: st.DataObject) -> None:
    v = data.draw(vector_strategy(vector_type))
    v2 = -v
    for i in range(v.getSize()):
        assert v2[i] == -v[i]


# ----------------------
# Vector OP Vector
# ----------------------


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_vector_plus_vector(vector_type: type[V], data: st.DataObject) -> None:
    v1, v2 = data.draw(vector_pair_strategy(vector_type))
    v3 = v1 + v2
    for i in range(v1.getSize()):
        assert v3[i] == v1[i] + v2[i]


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_vector_minus_vector(vector_type: type[V], data: st.DataObject) -> None:
    v1, v2 = data.draw(vector_pair_strategy(vector_type))
    v3 = v1 - v2
    for i in range(v1.getSize()):
        assert v3[i] == v1[i] - v2[i]


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_vector_mult_vector(vector_type: type[V], data: st.DataObject) -> None:
    v1, v2 = data.draw(vector_pair_strategy(vector_type))
    v3 = v1 * v2
    for i in range(v1.getSize()):
        assert v3[i] == v1[i] * v2[i]


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_vector_div_vector(vector_type: type[V], data: st.DataObject) -> None:
    v1, v2 = data.draw(vector_pair_strategy(vector_type))
    for i in range(v2.getSize()):
        if v2[i] == 0:
            assume(False)
    v3 = v1 / v2
    for i in range(v1.getSize()):
        if vector_type.RealType is int:
            # GOTCHA: Python rounds to the next lower integer (floor), whereas C++ rounds towards zero (trunc)
            assert v3[i] == math.trunc(v1[i] / v2[i])  # type: ignore[arg-type]
        else:
            assert v3[i] == v1[i] / v2[i]


# ----------------------
# Vector OP Scalar
# ----------------------


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_vector_plus_scalar(vector_type: type[V], data: st.DataObject) -> None:
    v, s = data.draw(vector_scalar_strategy(vector_type))
    v2 = v + s  # type: ignore[operator]
    for i in range(v.getSize()):
        assert v2[i] == v[i] + s


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_vector_minus_scalar(vector_type: type[V], data: st.DataObject) -> None:
    v, s = data.draw(vector_scalar_strategy(vector_type))
    v2 = v - s  # type: ignore[operator]
    for i in range(v.getSize()):
        assert v2[i] == v[i] - s


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_vector_mult_scalar(vector_type: type[V], data: st.DataObject) -> None:
    v, s = data.draw(vector_scalar_strategy(vector_type))
    v2 = v * s  # type: ignore[operator]
    for i in range(v.getSize()):
        assert v2[i] == v[i] * s


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_vector_div_scalar(vector_type: type[V], data: st.DataObject) -> None:
    v, s = data.draw(vector_scalar_strategy(vector_type))
    if s == 0:
        assume(False)
    v2 = v / s  # type: ignore[operator]
    for i in range(v.getSize()):
        if vector_type.RealType is int:
            # GOTCHA: Python rounds to the next lower integer (floor), whereas C++ rounds towards zero (trunc)
            assert v2[i] == math.trunc(v[i] / s)  # type: ignore[arg-type]
        else:
            assert v2[i] == v[i] / s


# ----------------------
# Scalar OP Vector
# ----------------------


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_scalar_plus_vector(vector_type: type[V], data: st.DataObject) -> None:
    v, s = data.draw(vector_scalar_strategy(vector_type))
    v2 = s + v  # type: ignore[operator]
    for i in range(v.getSize()):
        assert v2[i] == s + v[i]


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_scalar_minus_vector(vector_type: type[V], data: st.DataObject) -> None:
    v, s = data.draw(vector_scalar_strategy(vector_type))
    v2 = s - v  # type: ignore[operator]
    for i in range(v.getSize()):
        assert v2[i] == s - v[i]


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_scalar_mult_vector(vector_type: type[V], data: st.DataObject) -> None:
    v, s = data.draw(vector_scalar_strategy(vector_type))
    v2 = s * v  # type: ignore[operator]
    for i in range(v.getSize()):
        assert v2[i] == s * v[i]


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_scalar_div_vector(vector_type: type[V], data: st.DataObject) -> None:
    v, s = data.draw(vector_scalar_strategy(vector_type))
    for i in range(v.getSize()):
        if v[i] == 0:
            assume(False)
    v2 = s / v  # type: ignore[operator]
    for i in range(v.getSize()):
        if vector_type.RealType is int:
            # GOTCHA: Python rounds to the next lower integer (floor), whereas C++ rounds towards zero (trunc)
            assert v2[i] == math.trunc(s / v[i])  # type: ignore[arg-type]
        else:
            assert v2[i] == s / v[i]


# ----------------------
# Modulo Tests (Only for Vector_int)
# ----------------------


@pytest.mark.parametrize("vector_type", [t for t in vector_types if t.ValueType is int])
@given(data=st.data())
def test_vector_modulo_vector(vector_type: type[Vint], data: st.DataObject) -> None:
    v1, v2 = data.draw(vector_pair_strategy(vector_type))
    for i in range(v2.getSize()):
        if v2[i] == 0:
            assume(False)
    v3 = v1 % v2
    for i in range(v1.getSize()):
        # GOTCHA: Python uses the sign of the divisor, whereas C++ uses the sign of the dividend
        # assert v3[i] == v1[i] % v2[i]
        assert v3[i] == int(math.fmod(v1[i], v2[i]))


@pytest.mark.parametrize("vector_type", [t for t in vector_types if t.ValueType is int])
@given(data=st.data())
def test_vector_modulo_scalar(vector_type: type[Vint], data: st.DataObject) -> None:
    v, s = data.draw(vector_scalar_strategy(vector_type))
    if s == 0:
        assume(False)
    assert isinstance(s, int)
    v2 = v % s
    for i in range(v.getSize()):
        # GOTCHA: Python uses the sign of the divisor, whereas C++ uses the sign of the dividend
        # assert v2[i] == v[i] % s
        assert v2[i] == int(math.fmod(v[i], s))


@pytest.mark.parametrize("vector_type", [t for t in vector_types if t.ValueType is int])
@given(data=st.data())
def test_scalar_modulo_vector(vector_type: type[Vint], data: st.DataObject) -> None:
    v, s = data.draw(vector_scalar_strategy(vector_type))
    for i in range(v.getSize()):
        if v[i] == 0:
            assume(False)
    assert isinstance(s, int)
    v2 = s % v
    for i in range(v.getSize()):
        # GOTCHA: Python uses the sign of the divisor, whereas C++ uses the sign of the dividend
        # assert v2[i] == s % v[i]
        assert v2[i] == int(math.fmod(s, v[i]))


# ----------------------
# In-place Vector OP= Vector
# ----------------------


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_iadd_vector(vector_type: type[V], data: st.DataObject) -> None:
    v1, v2 = data.draw(vector_pair_strategy(vector_type))
    original_v1 = copy.deepcopy(v1)
    v1 += v2
    for i in range(v1.getSize()):
        assert v1[i] == original_v1[i] + v2[i]


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_isub_vector(vector_type: type[V], data: st.DataObject) -> None:
    v1, v2 = data.draw(vector_pair_strategy(vector_type))
    original_v1 = copy.deepcopy(v1)
    v1 -= v2
    for i in range(v1.getSize()):
        assert v1[i] == original_v1[i] - v2[i]


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_imul_vector(vector_type: type[V], data: st.DataObject) -> None:
    v1, v2 = data.draw(vector_pair_strategy(vector_type))
    original_v1 = copy.deepcopy(v1)
    v1 *= v2
    for i in range(v1.getSize()):
        assert v1[i] == original_v1[i] * v2[i]


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_idiv_vector(vector_type: type[V], data: st.DataObject) -> None:
    v1, v2 = data.draw(vector_pair_strategy(vector_type))
    for i in range(v2.getSize()):
        if v2[i] == 0:
            assume(False)
    original_v1 = copy.deepcopy(v1)
    v1 /= v2
    for i in range(v1.getSize()):
        if vector_type.RealType is int:
            # GOTCHA: Python rounds to the next lower integer (floor), whereas C++ rounds towards zero (trunc)
            assert v1[i] == math.trunc(original_v1[i] / v2[i])  # type: ignore[arg-type]
        else:
            assert v1[i] == original_v1[i] / v2[i]


@pytest.mark.parametrize("vector_type", [t for t in vector_types if t.ValueType is int])
@given(data=st.data())
def test_imod_vector(vector_type: type[Vint], data: st.DataObject) -> None:
    v1, v2 = data.draw(vector_pair_strategy(vector_type))
    for i in range(v2.getSize()):
        if v2[i] == 0:
            assume(False)
    original_v1 = copy.deepcopy(v1)
    v1 %= v2
    for i in range(v1.getSize()):
        # GOTCHA: Python uses the sign of the divisor, whereas C++ uses the sign of the dividend
        # assert v3[i] == v1[i] % v2[i]
        assert v1[i] == int(math.fmod(original_v1[i], v2[i]))


# ----------------------
# In-place Vector OP= Scalar
# ----------------------


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_iadd_scalar(vector_type: type[V], data: st.DataObject) -> None:
    v, s = data.draw(vector_scalar_strategy(vector_type))
    original_v = copy.deepcopy(v)
    v += s  # type: ignore[arg-type]
    # workaround for pyright: the assignment makes the type of v partially unknown
    v = cast(V, v)  # type: ignore[redundant-cast]
    for i in range(v.getSize()):
        assert v[i] == original_v[i] + s


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_isub_scalar(vector_type: type[V], data: st.DataObject) -> None:
    v, s = data.draw(vector_scalar_strategy(vector_type))
    original_v = copy.deepcopy(v)
    v -= s  # type: ignore[arg-type]
    # workaround for pyright: the assignment makes the type of v partially unknown
    v = cast(V, v)  # type: ignore[redundant-cast]
    for i in range(v.getSize()):
        assert v[i] == original_v[i] - s


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_imul_scalar(vector_type: type[V], data: st.DataObject) -> None:
    v, s = data.draw(vector_scalar_strategy(vector_type))
    original_v = copy.deepcopy(v)
    v *= s  # type: ignore[arg-type]
    # workaround for pyright: the assignment makes the type of v partially unknown
    v = cast(V, v)  # type: ignore[redundant-cast]
    for i in range(v.getSize()):
        assert v[i] == original_v[i] * s


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_idiv_scalar(vector_type: type[V], data: st.DataObject) -> None:
    v, s = data.draw(vector_scalar_strategy(vector_type))
    if s == 0:
        assume(False)
    original_v = copy.deepcopy(v)
    v /= s  # type: ignore[operator]
    # workaround for pyright: the assignment makes the type of v partially unknown
    v = cast(V, v)  # type: ignore[redundant-cast]
    for i in range(v.getSize()):
        if vector_type.RealType is int:
            # GOTCHA: Python rounds to the next lower integer (floor), whereas C++ rounds towards zero (trunc)
            assert v[i] == math.trunc(original_v[i] / s)  # type: ignore[arg-type]
        else:
            assert v[i] == original_v[i] / s


@pytest.mark.parametrize("vector_type", [t for t in vector_types if t.ValueType is int])
@given(data=st.data())
def test_imod_scalar(vector_type: type[Vint], data: st.DataObject) -> None:
    v, s = data.draw(vector_scalar_strategy(vector_type))
    if s == 0:
        assume(False)
    original_v = copy.deepcopy(v)
    assert isinstance(s, int)
    v %= s
    for i in range(v.getSize()):
        # GOTCHA: Python uses the sign of the divisor, whereas C++ uses the sign of the dividend
        # assert v3[i] == v1[i] % v2[i]
        assert v[i] == int(math.fmod(original_v[i], s))


# ----------------------
# Comparison operators
# ----------------------


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_vector_eq(vector_type: type[V], data: st.DataObject) -> None:
    size = data.draw(st.integers(min_value=0, max_value=20))
    elements1 = data.draw(st.lists(element_strategy(vector_type), min_size=size, max_size=size))
    elements2 = data.draw(st.lists(element_strategy(vector_type), min_size=size, max_size=size))
    v1 = create_vector(elements1, vector_type)
    v2 = create_vector(elements2, vector_type)
    assert (v1 == v2) == (elements1 == elements2)


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_vector_ne(vector_type: type[V], data: st.DataObject) -> None:
    size = data.draw(st.integers(min_value=0, max_value=20))
    elements1 = data.draw(st.lists(element_strategy(vector_type), min_size=size, max_size=size))
    elements2 = data.draw(st.lists(element_strategy(vector_type), min_size=size, max_size=size))
    v1 = create_vector(elements1, vector_type)
    v2 = create_vector(elements2, vector_type)
    assert (v1 != v2) == (elements1 != elements2)


@pytest.mark.parametrize("vector_type", real_vector_types)
@given(data=st.data())
def test_vector_lt(vector_type: type[Vreal], data: st.DataObject) -> None:
    size = data.draw(st.integers(min_value=0, max_value=20))
    elements1 = data.draw(st.lists(element_strategy(vector_type), min_size=size, max_size=size))
    elements2 = data.draw(st.lists(element_strategy(vector_type), min_size=size, max_size=size))
    v1 = create_vector(elements1, vector_type)
    v2 = create_vector(elements2, vector_type)
    assert (v1 < v2) == (elements1 < elements2)


@pytest.mark.parametrize("vector_type", real_vector_types)
@given(data=st.data())
def test_vector_le(vector_type: type[Vreal], data: st.DataObject) -> None:
    size = data.draw(st.integers(min_value=0, max_value=20))
    elements1 = data.draw(st.lists(element_strategy(vector_type), min_size=size, max_size=size))
    elements2 = data.draw(st.lists(element_strategy(vector_type), min_size=size, max_size=size))
    v1 = create_vector(elements1, vector_type)
    v2 = create_vector(elements2, vector_type)
    assert (v1 <= v2) == (elements1 <= elements2)


@pytest.mark.parametrize("vector_type", real_vector_types)
@given(data=st.data())
def test_vector_gt(vector_type: type[Vreal], data: st.DataObject) -> None:
    size = data.draw(st.integers(min_value=0, max_value=20))
    elements1 = data.draw(st.lists(element_strategy(vector_type), min_size=size, max_size=size))
    elements2 = data.draw(st.lists(element_strategy(vector_type), min_size=size, max_size=size))
    v1 = create_vector(elements1, vector_type)
    v2 = create_vector(elements2, vector_type)
    assert (v1 > v2) == (elements1 > elements2)


@pytest.mark.parametrize("vector_type", real_vector_types)
@given(data=st.data())
def test_vector_ge(vector_type: type[Vreal], data: st.DataObject) -> None:
    size = data.draw(st.integers(min_value=0, max_value=20))
    elements1 = data.draw(st.lists(element_strategy(vector_type), min_size=size, max_size=size))
    elements2 = data.draw(st.lists(element_strategy(vector_type), min_size=size, max_size=size))
    v1 = create_vector(elements1, vector_type)
    v2 = create_vector(elements2, vector_type)
    assert (v1 >= v2) == (elements1 >= elements2)


# ----------------------
# Slicing with operators
# ----------------------


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_slicing(vector_type: type[V], data: st.DataObject) -> None:
    size = data.draw(st.integers(min_value=0, max_value=20))
    elements1 = data.draw(st.lists(element_strategy(vector_type), min_size=size, max_size=size))
    elements2 = data.draw(st.lists(element_strategy(vector_type), min_size=size, max_size=size))
    v1 = create_vector(elements1, vector_type)
    v2 = create_vector(elements2, vector_type)
    v1[0 : size // 2] += 0 * v2[0 : size // 2] - v1[0 : size // 2]  # pyright: ignore[reportArgumentType,reportCallIssue]
    for i in range(size):
        if i < size // 2:
            assert v1[i] == 0
        else:
            assert v1[i] == elements1[i]


# ----------------------
# Functions
# ----------------------


@pytest.mark.parametrize("vector_type", vector_types)
@given(data=st.data())
def test_abs(vector_type: type[V], data: st.DataObject) -> None:
    v = data.draw(vector_strategy(vector_type))
    v2 = abs(v)
    assert isinstance(v2, vector_type)
    for i in range(v.getSize()):
        assert v2[i] == abs(v[i])


@pytest.mark.parametrize("vector_type", real_vector_types)
@given(data=st.data())
def test_floor(vector_type: type[Vreal], data: st.DataObject) -> None:
    v = data.draw(vector_strategy(vector_type))
    v2 = math.floor(v)
    assert isinstance(v2, vector_type)
    for i in range(v.getSize()):
        assert v2[i] == math.floor(v[i])


@pytest.mark.parametrize("vector_type", real_vector_types)
@given(data=st.data())
def test_ceil(vector_type: type[Vreal], data: st.DataObject) -> None:
    v = data.draw(vector_strategy(vector_type))
    v2 = math.ceil(v)
    assert isinstance(v2, vector_type)
    for i in range(v.getSize()):
        assert v2[i] == math.ceil(v[i])
