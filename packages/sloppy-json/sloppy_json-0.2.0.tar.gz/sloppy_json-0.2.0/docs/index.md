# sloppy-json

A forgiving JSON parser that recovers broken JSON from LLM outputs.

## Why sloppy-json?

LLMs often produce JSON that isn't quite valid:
- Single quotes instead of double quotes
- Trailing commas
- Unquoted keys
- Python literals (`True`, `False`, `None`)
- Truncated output
- Markdown code blocks around JSON
- JavaScript values (`undefined`, `NaN`, `Infinity`)

Standard `json.loads()` fails on all of these. sloppy-json recovers them.

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

## Basic Usage

### Default Permissive Parsing

```python
from sloppy_json import parse

# Default: maximum recovery (permissive mode)
parse("{key: 'value'")  # truncated, unquoted key, single quotes
# Returns: '{"key": "value"}'
```

### Strict Parsing

```python
from sloppy_json import parse, RecoveryOptions

# Strict: standard JSON only (like json.loads)
parse('{"key": "value"}', RecoveryOptions(strict=True))
```

### Custom Options

```python
from sloppy_json import parse, RecoveryOptions

opts = RecoveryOptions(
    allow_single_quotes=True,
    allow_trailing_commas=True,
)
result = parse("{'flag': true,}", opts)
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

## API Reference

### Functions

#### `parse(text: str, options: RecoveryOptions | None = None) -> str`

Parse JSON with specified recovery options.

- `options=None` (default): Permissive mode - all recovery enabled
- `options=RecoveryOptions(strict=True)`: Strict JSON parsing
- `options=RecoveryOptions(...)`: Custom options

Returns normalized JSON string.

### Classes

#### `RecoveryOptions`

Configuration dataclass for recovery behavior. See [Options Reference](options.md).

```python
from sloppy_json import RecoveryOptions

# Strict mode
RecoveryOptions(strict=True)

# Custom options
RecoveryOptions(allow_single_quotes=True, allow_trailing_commas=True)

# Auto-detect from samples
RecoveryOptions.detect_from(["{'key': 'value',}"])
```

#### `SloppyJSONDecodeError`

Exception raised when parsing fails. Includes position information.

```python
from sloppy_json import parse, RecoveryOptions, SloppyJSONDecodeError

try:
    parse('{invalid}', RecoveryOptions(strict=True))
except SloppyJSONDecodeError as e:
    print(e.message)   # "Expected string for key"
    print(e.line)      # 1
    print(e.column)    # 2
    print(e.position)  # 1
```

## Documentation

- [Options Reference](options.md) - All `RecoveryOptions` explained
- [Auto-Detection](detection.md) - Automatically detect required options
- [Error Handling](errors.md) - Exceptions and partial recovery
- [Examples](examples.md) - Common scenarios and recipes
