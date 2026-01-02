# Options Reference

Complete reference for all `RecoveryOptions` settings.

## Overview

```python
from sloppy_json import RecoveryOptions

# All options with defaults
opts = RecoveryOptions(
    # Strict mode
    strict=False,  # When True, all other options are ignored
    
    # Quoting
    allow_unquoted_keys=False,
    allow_single_quotes=False,
    allow_unquoted_identifiers=False,
    
    # Commas
    allow_trailing_commas=False,
    allow_missing_commas=False,
    
    # Incomplete JSON
    auto_close_objects=False,
    auto_close_arrays=False,
    auto_close_strings=False,
    
    # Extra content
    extract_json_from_text=False,
    extract_from_code_blocks=False,
    extract_from_triple_quotes=False,
    
    # Value normalization
    convert_python_literals=False,
    handle_undefined="null",
    handle_nan="string",
    handle_infinity="string",
    
    # Other
    allow_comments=False,
    escape_newlines_in_strings=False,
    partial_recovery=False,
)
```

## Usage Modes

### Default Permissive Mode

When you call `parse()` without options, all recovery is enabled:

```python
from sloppy_json import parse

# All recovery options enabled
result = parse("{'key': 'value',}")
```

### Strict Mode

Use `strict=True` to parse standard JSON only:

```python
from sloppy_json import parse, RecoveryOptions

result = parse('{"key": "value"}', RecoveryOptions(strict=True))
```

### Custom Options

Enable only specific options:

```python
opts = RecoveryOptions(
    allow_single_quotes=True,
    allow_trailing_commas=True,
)
result = parse("{'key': 'value',}", opts)
```

### Auto-detected Options

Detect required options from samples:

```python
samples = ["{'key': 'value',}", "{name: True}"]
opts = RecoveryOptions.detect_from(samples)
result = parse(new_json, opts)
```
```

---

## Quoting Options

### `allow_unquoted_keys`

**Default:** `False`

Allow object keys without quotes (JavaScript-style).

```python
opts = RecoveryOptions(allow_unquoted_keys=True)

parse('{name: "John", age: 30}', opts)
# Returns: '{"name": "John", "age": 30}'

parse('{$special_key: 1, _private: 2}', opts)
# Returns: '{"$special_key": 1, "_private": 2}'
```

Keys must follow JavaScript identifier rules: start with letter, `_`, or `$`, followed by letters, digits, `_`, or `$`.

---

### `allow_single_quotes`

**Default:** `False`

Allow single-quoted strings for both keys and values.

```python
opts = RecoveryOptions(allow_single_quotes=True)

parse("{'name': 'John'}", opts)
# Returns: '{"name": "John"}'

parse("{'msg': 'He said \"hello\"'}", opts)
# Returns: '{"msg": "He said \\"hello\\""}'
```

---

### `allow_unquoted_identifiers`

**Default:** `False`

Allow unquoted identifiers as values (not just keys).

```python
opts = RecoveryOptions(allow_unquoted_identifiers=True)

parse('{"status": success, "mode": enabled}', opts)
# Returns: '{"status": "success", "mode": "enabled"}'

parse('{"result": not_found}', opts)
# Returns: '{"result": "not_found"}'
```

Only valid JavaScript identifiers are matched. Numbers and special characters won't be treated as identifiers.

---

## Comma Options

### `allow_trailing_commas`

**Default:** `False`

Allow trailing commas in objects and arrays.

```python
opts = RecoveryOptions(allow_trailing_commas=True)

parse('{"a": 1, "b": 2,}', opts)
# Returns: '{"a": 1, "b": 2}'

parse('[1, 2, 3,]', opts)
# Returns: '[1, 2, 3]'

# Multiple trailing commas also work
parse('{"a": 1,,,}', opts)
# Returns: '{"a": 1}'
```

---

### `allow_missing_commas`

**Default:** `False`

Allow missing commas between elements.

```python
opts = RecoveryOptions(allow_missing_commas=True)

parse('{"a": 1 "b": 2 "c": 3}', opts)
# Returns: '{"a": 1, "b": 2, "c": 3}'

parse('[1 2 3]', opts)
# Returns: '[1, 2, 3]'
```

---

## Incomplete JSON Options

### `auto_close_objects`

**Default:** `False`

Automatically close unclosed objects.

```python
opts = RecoveryOptions(auto_close_objects=True)

parse('{"name": "John"', opts)
# Returns: '{"name": "John"}'

parse('{"outer": {"inner": 1}', opts)
# Returns: '{"outer": {"inner": 1}}'
```

---

### `auto_close_arrays`

**Default:** `False`

Automatically close unclosed arrays.

```python
opts = RecoveryOptions(auto_close_arrays=True)

parse('[1, 2, 3', opts)
# Returns: '[1, 2, 3]'

parse('[[1, 2], [3, 4]', opts)
# Returns: '[[1, 2], [3, 4]]'
```

---

### `auto_close_strings`

**Default:** `False`

Automatically close unclosed strings.

```python
opts = RecoveryOptions(auto_close_strings=True, auto_close_objects=True)

parse('{"message": "Hello, world', opts)
# Returns: '{"message": "Hello, world"}'
```

Usually combined with `auto_close_objects` and `auto_close_arrays` for truncated JSON recovery.

---

## Extra Content Options

### `extract_json_from_text`

**Default:** `False`

Extract JSON from surrounding text.

```python
opts = RecoveryOptions(extract_json_from_text=True)

parse('Here is the result: {"status": "ok"} Hope this helps!', opts)
# Returns: '{"status": "ok"}'

parse('The array is [1, 2, 3] as requested.', opts)
# Returns: '[1, 2, 3]'
```

Finds the first complete JSON object or array in the text.

---

### `extract_from_code_blocks`

**Default:** `False`

Extract JSON from markdown code blocks.

```python
opts = RecoveryOptions(extract_from_code_blocks=True)

text = '''Here's the JSON:
```json
{"key": "value"}
```
'''
parse(text, opts)
# Returns: '{"key": "value"}'

# Works with or without language specifier
text = '''```
[1, 2, 3]
```'''
parse(text, opts)
# Returns: '[1, 2, 3]'
```

---

### `extract_from_triple_quotes`

**Default:** `False`

Extract JSON from Python triple-quoted strings.

```python
opts = RecoveryOptions(extract_from_triple_quotes=True)

parse('"""{"key": "value"}"""', opts)
# Returns: '{"key": "value"}'

parse("'''[1, 2, 3]'''", opts)
# Returns: '[1, 2, 3]'
```

---

## Value Normalization Options

### `convert_python_literals`

**Default:** `False`

Convert Python literals to JSON equivalents.

```python
opts = RecoveryOptions(convert_python_literals=True)

parse('{"active": True, "data": None, "deleted": False}', opts)
# Returns: '{"active": true, "data": null, "deleted": false}'
```

| Python | JSON |
|--------|------|
| `True` | `true` |
| `False` | `false` |
| `None` | `null` |

---

### `handle_undefined`

**Default:** `"null"`

How to handle JavaScript `undefined` values.

| Value | Behavior |
|-------|----------|
| `"null"` | Convert to `null` |
| `"remove"` | Remove the key from objects (in arrays, becomes `null`) |
| `"error"` | Raise `SloppyJSONDecodeError` |

```python
# Default: convert to null
parse('{"a": undefined}')
# Returns: '{"a": null}'

# Remove from objects
opts = RecoveryOptions(handle_undefined="remove")
parse('{"a": 1, "b": undefined, "c": 3}', opts)
# Returns: '{"a": 1, "c": 3}'

# Error
opts = RecoveryOptions(handle_undefined="error")
parse('{"a": undefined}', opts)
# Raises: SloppyJSONDecodeError
```

---

### `handle_nan`

**Default:** `"string"`

How to handle `NaN` values.

| Value | Behavior |
|-------|----------|
| `"string"` | Convert to `"NaN"` |
| `"null"` | Convert to `null` |
| `"error"` | Raise `SloppyJSONDecodeError` |

```python
# Default: convert to string
parse('{"value": NaN}')
# Returns: '{"value": "NaN"}'

# Convert to null
opts = RecoveryOptions(handle_nan="null")
parse('{"value": NaN}', opts)
# Returns: '{"value": null}'
```

---

### `handle_infinity`

**Default:** `"string"`

How to handle `Infinity` and `-Infinity` values.

| Value | Behavior |
|-------|----------|
| `"string"` | Convert to `"Infinity"` / `"-Infinity"` |
| `"null"` | Convert to `null` |
| `"error"` | Raise `SloppyJSONDecodeError` |

```python
# Default: convert to string
parse('{"max": Infinity, "min": -Infinity}')
# Returns: '{"max": "Infinity", "min": "-Infinity"}'

# Convert to null
opts = RecoveryOptions(handle_infinity="null")
parse('{"max": Infinity}', opts)
# Returns: '{"max": null}'
```

---

## Other Options

### `allow_comments`

**Default:** `False`

Allow JavaScript-style comments.

```python
opts = RecoveryOptions(allow_comments=True)

parse('{"a": 1} // inline comment', opts)
# Returns: '{"a": 1}'

parse('''
{
  /* block comment */
  "key": "value"
}
''', opts)
# Returns: '{"key": "value"}'

# Nested block comments are handled
parse('{"a": 1 /* outer /* inner */ still outer */}', opts)
# Returns: '{"a": 1}'
```

---

### `escape_newlines_in_strings`

**Default:** `False`

Handle unescaped newlines and tabs in strings.

```python
opts = RecoveryOptions(escape_newlines_in_strings=True)

# Unescaped newline in string
parse('{"text": "line1\nline2"}', opts)
# Returns: '{"text": "line1\\nline2"}'

# Unescaped tab
parse('{"text": "col1\tcol2"}', opts)
# Returns: '{"text": "col1\\tcol2"}'
```

---

### `partial_recovery`

**Default:** `False`

When enabled, `parse()` returns a tuple of `(result, errors)` instead of raising on first error.

```python
opts = RecoveryOptions(partial_recovery=True)

result, errors = parse('{"a": 1, "b": , "c": 3}', opts)
# result: '{"a": 1, "b": null, "c": 3}'
# errors: [ErrorInfo(message="Expected value", ...)]

for error in errors:
    print(f"Line {error.line}, Col {error.column}: {error.message}")
```

See [Error Handling](errors.md) for more details.
