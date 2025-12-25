# PyArgument

**PyArgument** is a lightweight Python command-line argument parser with support for aliases, optional values, required arguments, and argument collection.  
It is designed for simplicity and direct control over parsing behavior.

---

## Features

- Long and short flags (e.g., --help, -h)
- Add arguments with multiple aliases
- Supports optional argument with values (optarg=True)
- Required arguments (`required=True`)
- Handles default values
- Tracks which arguments were provided
- Attribute-based access (`parser.input`, `parser.dir`)
- Collects parsed arguments into a list, using (`parser.pyargs`)

---

## Installation

### Install locally

```bash
pip install .
```

### Install via PIP

```bash
pip install pyargument
```

---

## Usage

### Example 1: Basic usage

```python
from pyargument import PyArgument
import json
import os

pwd = os.getcwd()
parser = PyArgument()
parser.add_arg("--online")
parser.add_arg("--input", "-in", optarg=True, required=True)
parser.add_arg("--dir", "--folder", optarg=True, default=pwd)
parser.add_arg("--file", optarg=True)
parser.add_arg("--pwd", "-p", "--cwd", required=True)

parser.parse_args()

print("Collected args:", parser.pyargs)
print("Arguments metadata:", json.dumps(parser.list_all(), indent=4))
print("Arguments provided:", parser.list_args())
print("Arguments alias:", json.dumps(parser.list_alias(), indent=4))
print("online:", parser.online)
print("input:", parser.input)
print("dir:", parser.dir, "is exists:", parser.dir.exists, "metadata:", parser.dir.meta)
print("file:", parser.file.value)
parser.file.value = "new_value.txt"
print("file:", parser.file.value) # argument value changed!
```

**Run from command line:**

```bash
python -m pyargument --input data.txt --pwd /home/user --dir /tmp
```

---

### Example 2: Aliases

```python
parser.add_arg("--help", "-h", "-?")
parser.parse_args()
print(parser.help)  # True if any alias is used
```

- All aliases (`--help`, `-h`, `-?`) map to the same internal argument.  
- Access via the main argument name (`help`).

---

## Methods

### Defining Arguments
#### `add_arg(*names, optarg=False, default=None, required=True)`

Parameters:

- names: One or more argument names
- optarg: Accepts a value if True
- default: Default value if not provided
- required: Program exits if missing

Example:
```
parser.add_arg("--input", "-in", optarg=True, required=True)
parser.add_arg("--online")
```
---

### Supported Argument Formats

--flag  
--key value  
--key=value  
-key value  

Examples:
```
python app.py --input file.txt --pwd /home/user  
python app.py --input=file.txt -p /home/user  
```
---

### Accessing Parsed Values

Each argument is available as an attribute:
```
parser.input  
parser.dir  
parser.file  
parser.pwd  
parser.online  
```
Boolean flags return True when present.

## Provider Object

Each argument is a Provider (class) instance.
It behaves like its value:
```
str(parser.input)
int(parser.count)
bool(parser.online)
```
But also exposes metadata:
```
parser.input.value
parser.input.exists
parser.input.required
parser.input.optarg
parser.input.names
```
---

### Required Arguments

If a required argument is missing, execution stops:

Required argument ('--input', '-in') not provided.

Exit code: 1

---

### `parse_args(*args)`

- Parses command-line arguments (`sys.argv[1:]`).  
- Updates attributes of the parser object.  


## Inspecting Arguments

#### `list_meta()`

- Returns a dictionary of all defined arguments metadata.

#### `list_args()`

- Returns a list of arguments that were **provided** in the command line.

#### `list_alias()`

- Returns a dictionary mapping each internal argument to all its aliases.

---

## Raw Parsed Arguments (pyargs)
- parser.pyargs

pyargs stores a simplified list of parsed arguments.
Useful for forwarding arguments to another command.

Example output:
```
['input', 'file.txt', 'pwd', '/home/user']
```
---

## Design Philosophy

- Minimal
- Explicit
- Hackable
- No magic
- Object-oriented
- Easy to understand

---

## License

MIT License

---

## Repository

[https://github.com/ankushbhagats/pyargument](https://github.com/ankushbhagats/pyargument)