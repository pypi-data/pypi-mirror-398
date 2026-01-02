# Error Handling

sloppy-json provides detailed error information and partial recovery capabilities.

## Exceptions

### SloppyJSONError

Base exception class for all sloppy-json errors.

```python
from sloppy_json import SloppyJSONError

try:
    result = parse(text, options)
except SloppyJSONError as e:
    print(f"Parsing failed: {e}")
```

### SloppyJSONDecodeError

Raised when JSON decoding fails. Includes position information.

```python
from sloppy_json import parse, RecoveryOptions, SloppyJSONDecodeError

try:
    parse('{invalid json}', RecoveryOptions(strict=True))
except SloppyJSONDecodeError as e:
    print(e.message)    # "Expected string for key"
    print(e.line)       # 1
    print(e.column)     # 2
    print(e.position)   # 1 (character offset from start)
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Error description |
| `line` | `int` | Line number (1-based) |
| `column` | `int` | Column number (1-based) |
| `position` | `int` | Character offset (0-based) |

---

## Partial Recovery Mode

By default, parsing stops at the first error. With `partial_recovery=True`, parsing continues and collects all errors.

### Basic Usage

```python
from sloppy_json import parse, RecoveryOptions

opts = RecoveryOptions(partial_recovery=True)

result, errors = parse('{"a": 1, "b": , "c": 3}', opts)

print(result)  # '{"a": 1, "b": null, "c": 3}'
print(len(errors))  # 1

for error in errors:
    print(f"Line {error.line}: {error.message}")
```

### Return Type

When `partial_recovery=True`:
- Returns: `tuple[str, list[ErrorInfo]]`

When `partial_recovery=False` (default):
- Returns: `str`
- Raises: `SloppyJSONDecodeError` on error

### Recovery Behavior

In partial recovery mode:
- Missing values become `null`
- Invalid tokens are skipped where possible
- Parsing continues to find more errors

```python
opts = RecoveryOptions(partial_recovery=True)

# Multiple errors
text = '{"a": , "b": undefined, "c": }'
result, errors = parse(text, opts)

print(result)  # '{"a": null, "b": null, "c": null}'
print(len(errors))  # 3 errors collected
```

---

## Common Error Messages

| Message | Cause |
|---------|-------|
| `Expected string for key` | Object key is not a quoted string |
| `Expected ':'` | Missing colon after object key |
| `Expected ',' or '}'` | Missing comma or closing brace |
| `Expected value` | Missing value after colon or in array |
| `Unexpected token` | Invalid character in context |
| `Unterminated string` | String not closed before end of input |
| `Invalid escape sequence` | Bad `\x` in string |
| `Trailing data after JSON` | Extra content after valid JSON |

---

## Best Practices

### 1. Use Appropriate Mode

```python
from sloppy_json import parse, RecoveryOptions, SloppyJSONDecodeError

# For validation: strict mode, catch errors
try:
    result = parse(text, RecoveryOptions(strict=True))
except SloppyJSONDecodeError as e:
    log_error(f"Invalid JSON at line {e.line}: {e.message}")

# For recovery: default permissive mode
result = parse(text)

# For debugging: partial recovery
result, errors = parse(text, RecoveryOptions(partial_recovery=True))
if errors:
    for e in errors:
        log_warning(f"Recovered from: {e}")
```

### 2. Validate After Recovery

```python
import json
from sloppy_json import parse

def safe_parse(text):
    result = parse(text)  # permissive by default
    
    # Verify it's valid JSON
    try:
        json.loads(result)
        return result
    except json.JSONDecodeError:
        raise ValueError("Recovery produced invalid JSON")
```

---

## Type Hints

For type checkers, the return type depends on `partial_recovery`:

```python
from sloppy_json import parse, RecoveryOptions

# Without partial_recovery (default) - returns str
def process(text: str) -> str:
    return parse(text)

# With partial_recovery - returns tuple
def process_safe(text: str) -> tuple[str, list]:
    opts = RecoveryOptions(partial_recovery=True)
    return parse(text, opts)
```
