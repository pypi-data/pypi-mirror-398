import numpy as np

from pytnl.containers import NDArray

# Create a 2D array of floats
a = NDArray[2, float]()
a.setSizes(3, 4)

# Initialize the array elements
shape = a.getSizes()
for i in range(shape[0]):
    for j in range(shape[1]):
        a[i, j] = i + j


# Define a function for evaluation
def f(i: int, j: int) -> None:
    print(f"{[i, j]}:  {a[i, j] = }")


# Evaluate a function for all indices of the array
a.forAll(f)

# Print the memory layout of the array
print(list(a.getStorageArray()))

# Get a NumPy array that shares memory
np_array = np.from_dlpack(a)
print(np_array)
print(type(np_array), np_array.shape, np_array.dtype)
