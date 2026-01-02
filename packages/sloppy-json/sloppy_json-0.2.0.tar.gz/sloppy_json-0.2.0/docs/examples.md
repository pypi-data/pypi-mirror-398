# Examples

Common scenarios and recipes for using sloppy-json.

## LLM Response Parsing

### Basic LLM Output

```python
from sloppy_json import parse
import json

def extract_json_from_llm(response: str) -> dict:
    """Extract and parse JSON from LLM response."""
    json_str = parse(response)  # permissive by default
    return json.loads(json_str)

# Example responses
response = """Sure! Here's the user data you requested:

```json
{
  'name': 'John Doe',
  'age': 30,
  'active': True,
}
```

Let me know if you need anything else!"""

data = extract_json_from_llm(response)
# {'name': 'John Doe', 'age': 30, 'active': True}
```

### Handling Truncated Responses

LLMs often hit token limits and truncate output:

```python
from sloppy_json import parse
import json

truncated = '{"users": [{"name": "Alice", "email": "alice@example.com"}, {"name": "Bob", "email": "bob@'

result = parse(truncated)
# '{"users": [{"name": "Alice", "email": "alice@example.com"}, {"name": "Bob", "email": "bob@"}]}'

data = json.loads(result)
# Partial data is better than no data
```

### Streaming JSON Responses

For streaming LLM responses:

```python
from sloppy_json import parse, RecoveryOptions

def parse_streaming_json(partial_response: str):
    """Parse potentially incomplete JSON from a stream."""
    opts = RecoveryOptions(
        auto_close_objects=True,
        auto_close_arrays=True,
        auto_close_strings=True,
        allow_trailing_commas=True,
    )
    return parse(partial_response, opts)

# As tokens come in
chunks = [
    '{"status": "pro',
    '{"status": "processing", "items": [1, 2',
    '{"status": "processing", "items": [1, 2, 3], "done": fal',
]

for chunk in chunks:
    try:
        result = parse_streaming_json(chunk)
        print(f"Current state: {result}")
    except Exception:
        print("Waiting for more data...")
```

---

## Function Calling / Tool Use

### Parsing Tool Arguments

```python
from sloppy_json import parse, RecoveryOptions
import json

def parse_tool_args(raw_args: str) -> dict:
    """Parse tool call arguments from LLM."""
    opts = RecoveryOptions(
        allow_single_quotes=True,
        allow_trailing_commas=True,
        convert_python_literals=True,
    )
    json_str = parse(raw_args, opts)
    return json.loads(json_str)

# LLM might return Python-style
raw = "{'query': 'weather', 'location': 'NYC', 'units': 'metric',}"
args = parse_tool_args(raw)
# {'query': 'weather', 'location': 'NYC', 'units': 'metric'}
```

### Structured Output Extraction

```python
from sloppy_json import parse
import json
from dataclasses import dataclass

@dataclass
class ExtractedEntity:
    name: str
    entity_type: str
    confidence: float

def extract_entities(llm_response: str) -> list[ExtractedEntity]:
    json_str = parse(llm_response)
    data = json.loads(json_str)
    
    return [
        ExtractedEntity(**entity)
        for entity in data.get('entities', [])
    ]

response = '''Here are the entities I found:
{
  entities: [
    {name: 'Apple Inc.', entity_type: 'COMPANY', confidence: 0.95},
    {name: 'Tim Cook', entity_type: 'PERSON', confidence: 0.87,},
  ]
}'''

entities = extract_entities(response)
```

---

## Configuration Files

### Lenient Config Parsing

```python
from sloppy_json import parse, RecoveryOptions
import json

def load_config(path: str) -> dict:
    """Load a JSON config file with comments and trailing commas."""
    opts = RecoveryOptions(
        allow_comments=True,
        allow_trailing_commas=True,
    )
    
    with open(path) as f:
        content = f.read()
    
    json_str = parse(content, opts)
    return json.loads(json_str)

# config.json:
# {
#   "debug": true,  // Enable debug mode
#   "api_url": "https://api.example.com",
#   "features": [
#     "auth",
#     "logging",  // Note: trailing comma
#   ],
# }

config = load_config("config.json")
```

---

## Data Cleaning

### Cleaning Scraped JSON

```python
from sloppy_json import parse
import json

def clean_json(dirty_json: str) -> str:
    """Clean and normalize messy JSON."""
    return parse(dirty_json)  # permissive by default

# Scraped data with various issues
dirty = """
{
  name: 'Product Name',
  price: undefined,
  inStock: True,
  tags: ['sale', 'new',],
  // old field
  rating: NaN,
}
"""

clean = clean_json(dirty)
# '{"name": "Product Name", "price": null, "inStock": true, "tags": ["sale", "new"], "rating": "NaN"}'
```

### Batch Processing

```python
from sloppy_json import parse, SloppyJSONDecodeError
import json

def process_json_batch(items: list[str]) -> list[dict]:
    """Process a batch of potentially broken JSON strings."""
    results = []
    
    for i, item in enumerate(items):
        try:
            json_str = parse(item)
            results.append(json.loads(json_str))
        except SloppyJSONDecodeError as e:
            print(f"Item {i} failed: {e.message}")
            results.append(None)
    
    return results
```

---

## API Response Handling

### Wrapper for API Clients

```python
from sloppy_json import parse, RecoveryOptions
import json
import httpx

class RobustAPIClient:
    def __init__(self, base_url: str):
        self.client = httpx.Client(base_url=base_url)
        self.opts = RecoveryOptions(
            allow_single_quotes=True,
            allow_trailing_commas=True,
            convert_python_literals=True,
        )
    
    def get_json(self, path: str) -> dict:
        response = self.client.get(path)
        response.raise_for_status()
        
        # Handle potentially broken JSON
        json_str = parse(response.text, self.opts)
        return json.loads(json_str)

# Usage
client = RobustAPIClient("https://api.example.com")
data = client.get_json("/data")
```

---

## Debugging

### Verbose Parsing

```python
from sloppy_json import parse, RecoveryOptions

def parse_verbose(text: str) -> str:
    """Parse with detailed error reporting."""
    opts = RecoveryOptions(
        allow_single_quotes=True,
        allow_trailing_commas=True,
        convert_python_literals=True,
        partial_recovery=True,
    )
    
    result, errors = parse(text, opts)
    
    if errors:
        print(f"Recovered from {len(errors)} error(s):")
        for error in errors:
            print(f"  Line {error.line}, Col {error.column}: {error.message}")
    
    return result

text = '{"a": 1, "b": , "c": undefined, "d": }'
result = parse_verbose(text)
# Recovered from 3 error(s):
#   Line 1, Col 15: Expected value
#   Line 1, Col 22: Unexpected identifier 'undefined'
#   Line 1, Col 37: Expected value
```

---

## Integration Patterns

### Caching Detected Options

```python
from sloppy_json import parse, RecoveryOptions

class SmartParser:
    def __init__(self):
        self._samples: list[str] = []
        self._options: RecoveryOptions | None = None
    
    def add_sample(self, text: str):
        """Add a sample for option detection."""
        self._samples.append(text)
        self._options = None  # Invalidate cache
    
    @property
    def options(self) -> RecoveryOptions:
        if self._options is None:
            if self._samples:
                self._options = RecoveryOptions.detect_from(self._samples)
            else:
                self._options = RecoveryOptions()
        return self._options
    
    def parse(self, text: str) -> str:
        return parse(text, self.options)

# Usage
parser = SmartParser()
parser.add_sample("{'key': 'value'}")
parser.add_sample('{"flag": True,}')

# Now parser.options is optimized for your data
result = parser.parse(new_json)
```
