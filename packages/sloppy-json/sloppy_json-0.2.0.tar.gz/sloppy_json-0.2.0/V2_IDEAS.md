# V2 Ideas

Future improvements to consider for sloppy-json.

## Custom Special Value Mapping

Allow users to define custom mappings for JavaScript special values:

```python
from sloppy_json import parse, RecoveryOptions

opts = RecoveryOptions(
    special_value_map={
        "undefined": None,       # -> null
        "NaN": "NaN",            # -> "NaN" (string)
        "Infinity": 1e308,       # -> large number
        "-Infinity": -1e308,     # -> large negative number
    }
)

result = parse('{"a": undefined, "b": NaN, "c": Infinity}', opts)
# {"a": null, "b": "NaN", "c": 1e308}
```

This would give users full control over how each special value is converted.

## Other Ideas

- **Fuzzing with hypothesis** - Property-based testing for edge cases
- **Pretty-printing option** - Output formatted JSON instead of compact
- **Streaming parser** - Handle very large files without loading into memory
- **Mismatched quotes** - Handle `{"x': 5}` style errors
- **Position mapping** - Map output positions back to input positions for error reporting
- **Schema-aware recovery** - Use JSON schema hints to make smarter recovery decisions
