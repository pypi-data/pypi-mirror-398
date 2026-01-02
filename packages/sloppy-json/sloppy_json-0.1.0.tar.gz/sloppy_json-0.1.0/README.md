# sloppy-json

A forgiving JSON parser that recovers broken JSON from LLM outputs.

## Installation

```bash
uv add sloppy-json
```

or with pip:

```bash
pip install sloppy-json
```

## Usage

```python
from sloppy_json import parse, parse_lenient, parse_permissive, RecoveryOptions

# Strict parsing (standard JSON only)
result = parse('{"key": "value"}')

# Lenient parsing (common LLM issues)
result = parse_lenient("{'key': 'value',}")  # single quotes + trailing comma

# Permissive parsing (maximum recovery)
result = parse_permissive("Here is the JSON: {name: 'test'")  # everything

# Custom options
opts = RecoveryOptions(
    allow_single_quotes=True,
    allow_trailing_commas=True,
    convert_python_literals=True,
)
result = parse("{'flag': True,}", opts)
```

## Features

- **Quoting**: Unquoted keys, single-quoted strings
- **Commas**: Trailing commas, missing commas
- **Incomplete JSON**: Auto-close objects, arrays, strings
- **Extra content**: Extract JSON from surrounding text or code blocks
- **Python literals**: Convert `True`/`False`/`None` to JSON equivalents
- **Special values**: Handle `undefined`, `NaN`, `Infinity`
- **Comments**: JavaScript-style `//` and `/* */` comments
- **Escape handling**: Handle unescaped newlines in strings

## Auto-detection

Automatically detect what options are needed:

```python
from sloppy_json import detect_required_options

samples = ["{'key': 'value',}", "{name: True}"]
options = detect_required_options(samples)
# options.allow_single_quotes == True
# options.allow_trailing_commas == True
# options.allow_unquoted_keys == True
# options.convert_python_literals == True
```

## License

MIT
