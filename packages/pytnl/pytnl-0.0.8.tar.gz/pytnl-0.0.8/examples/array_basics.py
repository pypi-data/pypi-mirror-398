import os

from pytnl.containers import Array


def f(i: int) -> None:
    # Access the array element by its index
    print(f"[{i}]:  {a[i] = }")


# --- 1. Create a 1D Array of floats ---
# Array[float]() specifies a 1-dimensional array of float type
a = Array[float]()

# Set the size
a.setSize(10)

# --- 2. Initialize the array elements ---
size = a.getSize()  # Get the total number of elements
for i in range(size):
    # Set the element value: a[i] = i * 10
    a[i] = float(i * 10)

print(f"Array initialized with size: {size}")

# --- 3. We can iterate the array ---
for elem in a:
    print(elem)

# --- 4. It is possible to see if the array is empty ---
bol = a.empty()
print(f"Is the array empty?{bol}")

# ---5. we can apply a function f to all the elements ---
# STILL NOT AVAILABLE FOR PYTHON CODE
# a.forAllElements(f)

# ---6. we can apply a function f to all the elements from index begin to index end ---
# STILL NOT AVAILABLE FOR PYTHON CODE
# BEGIN = 0
# END = a.getSize()
# a.forElements(BEGIN, END, f)

# ---7. We can get the value of the element in position i, this method does the same as the [] operator---
for i in range(a.getSize()):
    print(f"The element in position {i} is {a.getElement(i)}")
    print(f"The element in position {i} is {a[i]}")

# ---8. We can also set the value of element in position i---
for i in range(a.getSize()):
    a.setElement(i, 2 * i)
    print(f"The element in position {i} is {a.getElement(i)}")

# ---9. It is possible to set elements from index begin to index end to a value value ---
BEGIN = 0
END = 3
VALUE = 1
a.setValue(VALUE, BEGIN, END)
print(f"All values from 0 to 3 should be 1: {a}")

# ---10. We can read and save data in custom binary files---
a.save("ArrayData")
b = Array[float]()
b.load("ArrayData")
print(f"We have written and read info from a document in array {b}")
os.remove("ArrayData")

# ---11. It is possible to reset the array---
bol = a.empty()
print(f"Is the array empty? {bol}")
a.reset()
print(f"The array once it has been reset: {a}")
bol = a.empty()
print(f"Is the array empty? {bol}")
