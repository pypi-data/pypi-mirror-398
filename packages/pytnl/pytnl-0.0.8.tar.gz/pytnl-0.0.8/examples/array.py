import numpy as np

from pytnl.containers import Array

# 1. Initialization and Element-wise Modification
# Array[int] specifies an Array of integers (int).
mi_array_int = Array[int](10, 0)

# Fill the first 5 elements.
for i in range(5):
    mi_array_int[i] = i * 2

print("Array after initialization and filling indices 0-4:")
print(str(mi_array_int))
# Expected: [0, 2, 4, 6, 8, 0, 0, 0, 0, 0]

# 2. Slice Assignment Workaround
data_list = [10, 20, 30, 40, 50]

# Convert the Python list into a temporary pytnl Array object.
array_temp = Array[int](len(data_list))
for i, val in enumerate(data_list):
    array_temp[i] = val

# Assign the temporary pytnl Array to the slice [5:10].
mi_array_int[5:10] = array_temp

print("\nArray after slice assignment [5:10]:")
print(str(mi_array_int))
# Expected: [0, 2, 4, 6, 8, 10, 20, 30, 40, 50]

# 3. Advanced Array Methods
# Resize the Array to 12 elements (new slots filled with 99).
mi_array_int.resize(12, 99)

# Fill a range (setValue) for indices [1, 4).
mi_array_int.setValue(-1, 1, 4)

print("\nArray after resize(12, 99) and setValue(-1, 1, 4):")
print(str(mi_array_int))
# Expected: [0, -1, -1, -1, 8, 10, 20, 30, 40, 50, 99, 99]

# 4. NumPy Interoperability
# Get a NumPy array that shares memory.
np_array = np.from_dlpack(mi_array_int)

# Modify the first element through the NumPy view.
np_array[0] = 5000

print("\nValue in mi_array_int[0] after changing NumPy view:")
print(mi_array_int[0])
# Expected: 5000 (Confirms memory sharing)
