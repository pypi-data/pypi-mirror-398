# TOON Parser (Python)

TOON (Token-Oriented Object Notation) is a human-readable data format optimized for Large Language Models (LLMs). This is the Python implementation of the TOON parser.

## Installation

```bash
pip install toon-format-parser
```

## Quick Start

```python
import toon_parser

# Encode Python data to TOON format
data = { 
  "sessionId": "abc-123",
  "users": [
    { "name": "Alice", "role": "admin" },
    { "name": "Bob", "role": "user" }
  ]
}

toon_string = toon_parser.encode(data)
print(toon_string)
# Output:
# sessionId: abc-123
# users: items[2]{name,role}:
#   Alice,admin
#   Bob,user

# Decode back to Python
decoded = toon_parser.decode(toon_string)
print(decoded)
```

## Features

- **Collection Markers**: Full support for `items[N]:` and `items[N]{headers}:`.
- **Tabular Arrays**: Efficient CSV-like representation for object arrays.
- **Ambiguity Resolution**: Robust parsing for nested structures.
- **LLM Optimized**: Minimizes tokens by removing redundant brackets and quotes.
