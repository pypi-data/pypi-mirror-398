# Auto-Detection

sloppy-json can analyze sample JSON strings and automatically detect which recovery options are needed.

## Basic Usage

```python
from sloppy_json import parse, RecoveryOptions

# Collect samples of broken JSON you've seen
samples = [
    "{'name': 'John'}",
    '{"active": True,}',
    '{key: "value"}',
]

# Detect minimum required options
options = RecoveryOptions.detect_from(samples)

# Now use those options
result = parse(broken_json, options)
```

## What It Detects

| Issue | Detection Pattern |
|-------|-------------------|
| Unquoted keys | `{key:` pattern |
| Single quotes | `'value'` patterns |
| Trailing commas | `,}` or `,]` |
| Missing commas | `" "` or `} {` patterns |
| Unclosed objects | More `{` than `}` |
| Unclosed arrays | More `[` than `]` |
| Unclosed strings | Odd number of quotes |
| Python literals | `True`, `False`, `None` |
| `undefined` | `undefined` keyword |
| `NaN` | `NaN` keyword |
| `Infinity` | `Infinity`, `-Infinity` |
| Comments | `//` or `/*` |
| Code blocks | ``` ` `` ` ``` markers |
| Triple quotes | `"""` or `'''` |
| Extra text | Text before/after JSON |

## Example: LLM Response Analysis

```python
from sloppy_json import parse, RecoveryOptions

# Collect samples from your LLM responses
llm_responses = [
    "Here's the data: {'result': 'success'}",
    '```json\n{"items": [1, 2, 3,]}\n```',
    '{"active": True, "count": None}',
]

# Analyze what options you need
options = RecoveryOptions.detect_from(llm_responses)

print(f"Single quotes: {options.allow_single_quotes}")
print(f"Trailing commas: {options.allow_trailing_commas}")
print(f"Python literals: {options.convert_python_literals}")
print(f"Code blocks: {options.extract_from_code_blocks}")
print(f"Text extraction: {options.extract_json_from_text}")

# Use detected options for future parsing
result = parse(new_response, options)
```

## Nice repr Output

The detected options have a clean representation showing only non-default values:

```python
>>> samples = ["{'key': 'value',}", "{name: True}"]
>>> opts = RecoveryOptions.detect_from(samples)
>>> opts
RecoveryOptions(
    allow_single_quotes=True,
    allow_trailing_commas=True,
    allow_unquoted_keys=True,
    convert_python_literals=True
)
```

## Combining with Manual Options

You can use detected options as a base and add more:

```python
from dataclasses import replace
from sloppy_json import RecoveryOptions

# Detect from samples
options = RecoveryOptions.detect_from(samples)

# Add additional options
options = replace(options, 
    escape_newlines_in_strings=True,
    partial_recovery=True,
)

result = parse(broken_json, options)
```

## Use Cases

### 1. Configuration Discovery

When integrating with a new LLM or data source:

```python
# Collect 10-20 sample responses
samples = collect_samples()

# Analyze what options you need
options = RecoveryOptions.detect_from(samples)

# Print the recommended configuration
print(f"Recommended options: {options}")
```

### 2. Adaptive Parsing

Adjust options based on observed patterns:

```python
from sloppy_json import parse, RecoveryOptions, SloppyJSONDecodeError

class AdaptiveParser:
    def __init__(self):
        self.samples = []
        self.options = RecoveryOptions()
    
    def parse(self, text):
        try:
            return parse(text, self.options)
        except SloppyJSONDecodeError:
            # Failed - add to samples and re-detect
            self.samples.append(text)
            self.options = RecoveryOptions.detect_from(self.samples)
            return parse(text, self.options)
```

### 3. Validation

Check if samples need recovery at all:

```python
options = RecoveryOptions.detect_from(samples)

if repr(options) == "RecoveryOptions()":
    print("All samples are valid JSON!")
else:
    print(f"Samples need recovery: {options}")
```

## Limitations

Detection is heuristic-based and may not catch all issues:

- **False positives**: Pattern might appear in string values
- **False negatives**: Unusual patterns might not be detected
- **Context-dependent**: Some issues only manifest during parsing

For critical applications, consider using default permissive mode or manually configuring options based on known LLM behavior.
