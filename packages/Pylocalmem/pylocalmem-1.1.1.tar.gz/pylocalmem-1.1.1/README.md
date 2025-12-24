# 🧠 Pylocalmem

A Python package for local process data manipulation (64 bit).

---

## 📖 Description

Pylocalmem was made to be able to read and write values of local process addresses.

It can be used for **game modding**, **runtime patching**, or **process manipulation** — without needing to call `OpenProcess`, since you’re already *inside* the process you want to modify.

---

## 🧩 Requirements

Python 3.11 or higher (tested on 3.14 but should work from 3.11 to 3.14)

keystone-engine (pip install keystone-engine)

---

## ⚙️ Installation

```bash
pip install pylocalmem
```
## 🚀 Example Usage

```python
from pylocalmem import Process

# Create a memory object for the current process
mem = Process()

# Read an integer at a given address
value = mem.read_int(0x7FFDEAD)

print("Current value:", value)

# Write a new value
mem.write_int(0x7FFDEAD, 1337)
print("New value written!")

# Define a structure to read
class MyStruct(ctypes.Structure):
    _fields_ = [
        ("field1", ctypes.c_bool),
        ("field2", ctypes.c_longlong)
    ]


# Read the struct at a given address
data = mem.read_ctype(0x7FFDEAD, MyStruct)

print("Field 1:", data.field1)


# Modify our data
data.field1 = False

# Write the struct back at a given address
data = mem.read_ctype(0x7FFDEAD, data)


# Hide python
mem.hide_python()


# Get all modules exports
exports = mem.get_all_exports()

print(exports)
```