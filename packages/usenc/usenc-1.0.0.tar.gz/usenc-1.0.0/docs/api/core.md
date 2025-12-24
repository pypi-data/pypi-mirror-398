# Core API Reference

The core module provides high-level functions for encoding and decoding.

## Functions

::: usenc.encode

::: usenc.decode


## Python API

usenc can be used as a Python library for programmatic encoding/decoding.

### Basic Usage

```python
from usenc import encode, decode

# Simple encoding
encoded = encode(b'hello world', encoder_name='url')
print(encoded)  # b'hello%20world'

# Simple decoding
decoded = decode(b'hello%20world', encoder_name='url')
print(decoded)  # b'hello world'
```

### Using Custom Parameters

Pass encoder-specific parameters as keyword arguments:

```python
from usenc import encode

# Hex encoding with prefix and lowercase
encoded = encode(
    b'hello',
    encoder_name='hex',
    prefix='0x',
    suffix=',',
    lowercase=True
)
print(encoded)  # b'0x68,0x65,0x6c,0x6c,0x6f,'

# URL encoding with include parameter
encoded = encode(
    b'key=value',
    encoder_name='url',
    include='='
)
print(encoded)  # b'key%3Dvalue'
```

### Charset Parameters

```python
from usenc import encode, decode

# UTF-8 to URL encoding
text = 'café'.encode('utf8')
encoded = encode(
    text,
    encoder_name='url',
    input_charset='utf8',
    output_charset='utf8'
)
print(encoded)  # b'caf%C3%A9'

# Latin-1 to URL encoding
text = 'café'.encode('latin1')
encoded = encode(
    text,
    encoder_name='url',
    input_charset='latin1',
    output_charset='latin1'
)
print(encoded)  # b'caf%E9'
```

### Direct Encoder Access

For advanced use cases, you can access encoders directly:

```python
from usenc.encoders import ENCODERS

# Get an encoder
hex_encoder = ENCODERS['hex']

# Use it directly
encoded = hex_encoder.encode(
    b'test',
    lowercase=True,
    prefix='\\x'
)
print(encoded)  # b'\\x74\\x65\\x73\\x74'

# Check available parameters
print(hex_encoder.params)
# {'prefix': {...}, 'suffix': {...}, 'include': {...}, ...}
```

### Error Handling

```python
from usenc import encode, decode
from usenc.encoders.encoder import EncodeError, DecodeError

try:
    # This might fail if the charset is invalid
    encoded = encode(
        b'\xff\xfe',
        encoder_name='url',
        input_charset='ascii'  # ASCII can't handle these bytes
    )
except EncodeError as e:
    print(f"Encoding failed: {e}")

try:
    # This might fail if the input is malformed
    decoded = decode(
        b'invalid%ZZdata',
        encoder_name='url'
    )
except DecodeError as e:
    print(f"Decoding failed: {e}")
```

### Listing Available Encoders

```python
from usenc.encoders import ENCODERS

# List all encoders
print("Available encoders:")
for name in ENCODERS.keys():
    print(f"  - {name}")

# Get encoder info
encoder = ENCODERS['hex']
print(f"\nEncoder: {encoder.__name__}")
print(f"Docstring: {encoder.__doc__}")
print(f"Parameters: {list(encoder.params.keys())}")
```

## See Also

- [Available Encoders](../encoders/url.md) - List of all encoders
