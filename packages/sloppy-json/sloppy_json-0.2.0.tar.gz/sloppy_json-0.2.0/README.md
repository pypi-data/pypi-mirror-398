<p align="center">
  <img src="assets/logo.png" alt="sloppy-json" width="400">
</p>

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

## Quick Start

```python
from sloppy_json import parse

# Handles almost any broken JSON (permissive by default)
result = parse("{'name': 'test', 'active': True,}")
# Returns: '{"name": "test", "active": true}'
```

## Usage

```python
from sloppy_json import parse, RecoveryOptions

# Default: permissive parsing (maximum recovery)
result = parse("Here is the JSON: {name: 'test'")  # handles everything

# Strict parsing (standard JSON only)
result = parse('{"key": "value"}', RecoveryOptions(strict=True))

# Custom options
opts = RecoveryOptions(
    allow_single_quotes=True,
    allow_trailing_commas=True,
)
result = parse("{'key': 'value',}", opts)
```

## Features

| Feature | Example Input | Output |
|---------|---------------|--------|
| Single quotes | `{'key': 'value'}` | `{"key": "value"}` |
| Unquoted keys | `{key: "value"}` | `{"key": "value"}` |
| Trailing commas | `{"a": 1,}` | `{"a": 1}` |
| Missing commas | `{"a": 1 "b": 2}` | `{"a": 1, "b": 2}` |
| Python literals | `{"flag": True}` | `{"flag": true}` |
| Truncated JSON | `{"key": "val` | `{"key": "val"}` |
| Code blocks | `` ```json {"a":1}``` `` | `{"a": 1}` |
| Comments | `{"a": 1} // comment` | `{"a": 1}` |
| JS undefined | `{"a": undefined}` | `{"a": null}` |
| NaN/Infinity | `{"a": NaN}` | `{"a": "NaN"}` |

## Auto-detection

Automatically detect what options are needed from sample data:

```python
from sloppy_json import parse, RecoveryOptions

samples = ["{'key': 'value',}", "{name: True}"]
options = RecoveryOptions.detect_from(samples)
# options.allow_single_quotes == True
# options.allow_trailing_commas == True
# options.allow_unquoted_keys == True
# options.convert_python_literals == True

result = parse(new_json, options)
```

## Documentation

- [Getting Started](docs/index.md) - Overview and quick start
- [Options Reference](docs/options.md) - All `RecoveryOptions` explained
- [Auto-Detection](docs/detection.md) - Automatically detect required options
- [Error Handling](docs/errors.md) - Exceptions and partial recovery
- [Examples](docs/examples.md) - Common scenarios and recipes

## Similar Projects

- **[sloppy-xml-py](https://github.com/mitsuhiko/sloppy-xml-py)** - A sloppy XML parser by Armin Ronacher for handling malformed XML. The naming of this project was inspired by sloppy-xml-py.
- **[json5](https://github.com/dpranke/pyjson5)** - A JSON extension that allows comments, trailing commas, and unquoted keys.

## License

MIT
