from typing import Any, cast

import pytest

import pytnl._containers
from pytnl._meta import is_dim_guard
from pytnl.containers import NDArrayIndexer

# Type alias for indexer types
type Indexer = pytnl._containers.NDArrayIndexer_1 | pytnl._containers.NDArrayIndexer_2 | pytnl._containers.NDArrayIndexer_3

# Type alias for the case parameters
type Case = dict[str, int | tuple[int, ...] | list[tuple[Any, ...]]]

# Test cases grouped by dimension
test_cases_1d: list[Case] = [
    {
        "sizes": (3,),
        "strides": (1,),
        "overlaps": (0,),
        "storage_size": 3,
        "index_cases": [
            ((0,), 0),
            ((1,), 1),
            ((2,), 2),
        ],
        "contiguous_cases": [
            ((0,), (1,), True),
            ((1,), (2,), True),
            ((0,), (3,), True),
        ],
    },
]

test_cases_2d: list[Case] = [
    {
        "sizes": (3, 4),
        "strides": (4, 1),
        "overlaps": (0, 0),
        "storage_size": 12,
        "index_cases": [
            ((0, 0), 0),
            ((1, 2), 6),
            ((2, 3), 11),
        ],
        "contiguous_cases": [
            ((0, 0), (3, 4), True),
            ((1, 1), (2, 3), True),
            ((1, 1), (3, 3), False),
        ],
    },
    {
        "sizes": (2, 2),
        "strides": (2, 1),
        "overlaps": (1, 0),
        "storage_size": 8,
        "index_cases": [
            ((0, 0), 2),
            ((1, 1), 5),
        ],
        "contiguous_cases": [
            ((-1, 0), (3, 2), True),
            ((0, 0), (2, 2), True),  # TODO: this may be wrong
            ((1, 0), (2, 2), True),
            ((0, 1), (2, 2), False),
        ],
    },
]

test_cases_3d: list[Case] = [
    {
        "sizes": (2, 3, 4),
        "strides": (12, 4, 1),
        "overlaps": (0, 0, 0),
        "storage_size": 24,
        "index_cases": [
            ((0, 0, 0), 0),
            ((1, 1, 1), 17),
        ],
        "contiguous_cases": [
            ((0, 0, 0), (2, 3, 4), True),
            ((1, 1, 1), (2, 3, 4), False),
        ],
    },
    {
        "sizes": (1, 2, 3),
        "strides": (6, 3, 1),
        "overlaps": (0, 1, 0),
        "storage_size": 12,
        "index_cases": [
            ((0, 0, 0), 3),
            ((0, 1, 2), 8),
        ],
        "contiguous_cases": [
            ((0, -1, 0), (1, 3, 3), True),
            ((0, 0, 0), (1, 2, 3), True),
            ((0, 1, 1), (1, 2, 3), True),
            ((0, 0, 1), (1, 2, 3), False),
        ],
    },
    {
        "sizes": (3, 3, 3),
        "strides": (9, 3, 1),  # static in C++
        "overlaps": (0, 0, 0),
        "storage_size": 27,
        "index_cases": [],
        "contiguous_cases": [
            ((1, 1, 1), (2, 2, 3), True),
            ((1, 1, 1), (2, 3, 2), False),
            ((1, 1, 1), (3, 2, 2), False),
            ((0, 0, 0), (1, 3, 3), True),
            ((0, 0, 0), (3, 3, 1), False),
        ],
    },
]

test_cases = {
    1: test_cases_1d,
    2: test_cases_2d,
    3: test_cases_3d,
}


@pytest.fixture(params=test_cases.keys())
def indexer_class(request: pytest.FixtureRequest) -> Indexer:
    """
    Provides the indexer class for each dimension specified in test_cases.
    """
    dim = request.param
    return cast(Indexer, NDArrayIndexer[dim])


# Test the default constructor
def test_default_constructor(indexer_class: type[Indexer]) -> None:
    indexer = indexer_class()
    sizes = indexer.getSizes()
    strides = indexer.getStrides()
    overlaps = indexer.getOverlaps()
    assert all(size == 0 for size in sizes)
    assert all(stride == 0 for stride in strides)
    assert all(overlap == 0 for overlap in overlaps)


# Parametrize the test function to run for each test case
@pytest.mark.parametrize("case", [case for cases in test_cases.values() for case in cases])
def test_ndarray_indexer_methods(case: Case) -> None:
    sizes = cast(tuple[int, ...], case["sizes"])
    strides = cast(tuple[int, ...], case["strides"])
    overlaps = cast(tuple[int, ...], case["overlaps"])
    storage_size = cast(int, case["storage_size"])
    index_cases = cast(list[tuple[tuple[int, ...], int]], case["index_cases"])
    contiguous_cases = cast(list[tuple[tuple[int, ...], tuple[int, ...], bool]], case["contiguous_cases"])

    dim = len(sizes)
    assert is_dim_guard(dim)
    indexer_class = NDArrayIndexer[dim]  # type: ignore[type-arg,valid-type]

    indexer = indexer_class(sizes, strides, overlaps)  # pyright: ignore[reportArgumentType]

    # Test getDimension
    assert indexer_class.getDimension() == dim

    # Test getSizes
    assert indexer.getSizes() == sizes

    # Test getStrides
    assert indexer.getStrides() == strides

    # Test getOverlaps
    assert indexer.getOverlaps() == overlaps

    # Test getStorageSize
    assert indexer.getStorageSize() == storage_size

    # Test getStorageIndex
    for indices, expected in index_cases:
        assert indexer.getStorageIndex(*indices) == expected

    # Test isContiguousBlock
    for begins, ends, expected in contiguous_cases:
        assert indexer.isContiguousBlock(begins, ends) == expected  # pyright: ignore[reportArgumentType]


# Test invalid number of indices
def test_invalid_indices(indexer_class: type[Indexer]) -> None:
    dimension = indexer_class.getDimension()

    # Create a basic indexer with default values
    sizes = (1,) * dimension
    strides = (1,) * dimension
    overlaps = (0,) * dimension
    indexer = indexer_class(sizes, strides, overlaps)  # type: ignore[arg-type]

    # Generate invalid indices
    with pytest.raises(ValueError):
        indexer.getStorageIndex(*(0,) * (dimension - 1))  # Too few
    with pytest.raises(ValueError):
        indexer.getStorageIndex(*(0,) * (dimension + 1))  # Too many


# Test invalid begins or ends in isContiguousBlock
def test_invalid_begins_ends(indexer_class: type[Indexer]) -> None:
    dimension = indexer_class.getDimension()

    # Create a basic indexer with default values
    sizes = (1,) * dimension
    strides = (1,) * dimension
    overlaps = (0,) * dimension
    indexer = indexer_class(sizes, strides, overlaps)  # type: ignore[arg-type]

    # Test with incorrect dimensions
    with pytest.raises(TypeError):
        indexer.isContiguousBlock((0,) * (dimension - 1), (1,) * (dimension - 1))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        indexer.isContiguousBlock((0,) * (dimension + 1), (1,) * (dimension + 1))  # type: ignore[arg-type]


# Test zero-sized dimensions
def test_zero_sized(indexer_class: type[Indexer]) -> None:
    dimension = indexer_class.getDimension()

    sizes = (0,) * dimension
    strides = (0,) * dimension
    overlaps = (0,) * dimension

    indexer = indexer_class(sizes, strides, overlaps)  # type: ignore[arg-type]
    assert indexer.getStorageSize() == 0

    with pytest.raises(IndexError):
        indexer.getStorageIndex(*(0,) * dimension)


# Test dynamic overlaps
def test_overlaps(indexer_class: type[Indexer]) -> None:
    dimension = indexer_class.getDimension()

    sizes = (2,) * dimension
    strides = (1,) * dimension
    overlaps = (1,) * dimension

    indexer = indexer_class(sizes, strides, overlaps)  # type: ignore[arg-type]
    assert indexer.getOverlaps() == overlaps
