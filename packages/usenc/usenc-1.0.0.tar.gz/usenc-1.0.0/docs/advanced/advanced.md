# Advanced Features

This guide covers advanced usage of usenc, including custom encoder parameters, charset handling, character selection, and Python API usage.

## Custom Encoder Parameters

Each encoder can define its own parameters that control encoding behavior. These parameters are exposed both in the CLI and the Python API.

### Common Parameters

Many encoders share common parameters. Here are the most frequently used:

#### Prefix and Suffix

Some encoders support adding custom prefix and suffix strings to each encoded character:

```bash
# Add prefix and suffix to hex encoding
echo "hello" | usenc hex --prefix '0x' --suffix ','
# Output: 0x68,0x65,0x6C,0x6C,0x6F,
```

#### Lowercase

Encoders that produce hexadecimal output support lowercase formatting:

```bash
# Uppercase hex (default)
echo "hello" | usenc hex
# Output: 68656C6C6F

# Lowercase hex
echo "hello" | usenc hex --lowercase
# Output: 68656c6c6f
```

### Character Selection Parameters

Encoders that inherit from the `EscapeEncoder` base class (such as `hex`, `url`, `cstring`, `unicode`, etc.) support fine-grained control over which characters get encoded.

#### Include Parameter

Specify additional characters that should be encoded:

```bash
# Only encode the letter 'e'
echo "hello world" | usenc cstring --include e
# Output: h\x65llo world

# Encode specific special characters
echo "key=value&other=1" | usenc url --include '&='
# Output: key%3Dvalue%26other%3D1
```

Special keywords:
- `all` - Encode all characters
- `ascii` - Encode all ASCII characters (0x00-0x7F)
- `utf8` - Encode all UTF-8 characters (0x80-0x10FFFF)

```bash
# Encode all characters
echo "hello" | usenc hex --include all
# Output: 68656C6C6F

# Encode only UTF-8 (non-ASCII) characters
echo "café" | usenc hex --include utf8
# Output: caf\xC3\xA9
```

#### Exclude Parameter

Specify characters that should NOT be encoded:

```bash
# Encode everything except spaces
echo "hello world" | usenc hex --include all --exclude ' '
# Output: 68656C6C6F 776F726C64

# Standard URL encoding but preserve slashes
echo "path/to/file.txt" | usenc url --exclude '/'
# Output: path/to/file.txt
```

#### Regex Parameter

Advanced users can provide a custom regex pattern to match characters that should be encoded. This overrides both `--include` and `--exclude`:

```bash
# Encode only vowels
echo "hello world" | usenc cstring --regex '[aeiou]'
# Output: h\x65ll\x6F w\x6Frld

# Encode sequences of digits
echo "id123 and id456" | usenc cstring --regex '\d+'
# Output: id\x31\x32\x33 and id\x34\x35\x36
```

**Note**: The regex pattern uses Python regex syntax and is applied to the decoded string.

### Encoder-Specific Parameters

Some encoders have unique parameters:

#### Base Encoders (base16, base32, base64)

```bash
# Custom alphabet for base64
echo "hello" | usenc base64 --alphabet 'custom_alphabet_here...'

# Enable padding
echo "hi" | usenc base64 --padding
```

#### Hash Encoders

```bash
# Specify hash algorithm for generic hash encoder
echo "data" | usenc hash --algorithm sha512
```

### Discovering Parameters

To see all available parameters for an encoder:

```bash
# Show help for a specific encoder
usenc hex --help
usenc url --help
usenc base64 --help
```

## Charset Handling

Understanding charset handling is crucial for working with non-ASCII data and binary encodings.

### How Charsets Work

usenc operates on bytes internally, but many encoders need to interpret these bytes as characters. Two global parameters control this interpretation:

- `--input-charset`: How to decode input bytes into characters
- `--output-charset`: How to encode output characters back into bytes

Both default to `utf8`, which works for most cases.

### Input Charset

The input charset determines how incoming bytes are interpreted:

```bash
# UTF-8 input (default)
echo "café" | usenc url
# Output: caf%C3%A9

# Latin-1 input (single-byte encoding)
printf 'caf\xe9' | usenc url --input-charset latin1
# Output: caf%C3%A9
```

**When to use**: When your input file uses a non-UTF-8 encoding (e.g., ISO-8859-1, Windows-1252, ASCII).

### Output Charset

The output charset determines how encoded characters are converted back to bytes:

```bash
# UTF-8 output (default) - multi-byte encoding
echo "café" | usenc url --output-charset utf8
# Output: caf%C3%A9

# Latin-1 output - single-byte encoding
echo "café" | usenc url --output-charset latin1
# Output: caf%E9
```

### Common Charsets

- `utf8` (default): Universal, supports all Unicode characters
- `latin1` (ISO-8859-1): Western European languages, single-byte
- `ascii`: 7-bit ASCII only
- `cp1252`: Windows Western European
- `utf16`: 16-bit Unicode
- Any encoding supported by Python's `codecs` module

### Decoding with Charsets

When decoding, the charsets work in reverse:

```bash
# Decode UTF-8 encoded URL
echo "caf%C3%A9" | usenc url -d --input-charset utf8
# Output: café

# Decode Latin-1 encoded URL
echo "caf%E9" | usenc url -d --input-charset latin1
# Output: café
```

### Practical Examples

#### Working with Legacy Encodings

```bash
# Convert Latin-1 file to UTF-8 URL encoding
usenc url --input-charset latin1 --output-charset utf8 -i legacy.txt -o modern.txt

# Decode data that was encoded with Latin-1
printf "h\xe9llo" | usenc url -d --input-charset latin1
# Output: héllo
```

#### Binary Data Handling

For pure binary encoders (base64, base32, base16, md5, sha1, sha256), charsets typically don't matter as they operate directly on bytes.

```bash
# Encode binary file
usenc base64 -i binary.dat -o encoded.txt

# MD5 hash of UTF-8 string
echo "hello" | usenc md5
```

## Bulk Mode

By default, usenc processes input line-by-line. Bulk mode (`-b` or `--bulk`) processes the entire input as a single block.

### When to Use Bulk Mode

#### Base Encodings

```bash
# Line-by-line base64 (default)
cat multiline.txt | usenc base64
# Each line is encoded separately

# Bulk base64
cat multiline.txt | usenc base64 --bulk
# Entire file encoded as one block
```

#### Hash Functions

```bash
# Hash a string (bulk is implied for single input)
usenc sha256
# Compute hash for each line of text

# Hash entire file
usenc md5 --bulk -i document.txt
# Equivalent to: md5sum document.txt
```

#### Preserving Structure

```bash
# Preserve newlines in the encoded output
echo -n "line1\nline2" | usenc url --bulk
# Output: line1%0Aline2
```

## Best Practices

### 1. Character Selection Strategy

Start with defaults, then customize:
1. Try the encoder's default character class
2. Add specific characters with `--include`
3. Exclude unwanted characters with `--exclude`
4. Use `--regex` only when include/exclude aren't sufficient

### 2. Bulk vs Line-by-Line

- Use bulk mode for: hashes, base encodings of entire files, preserving structure
- Use line-by-line for: processing logs, stream processing, large files

### 3. Parameter Discovery

Always check encoder-specific help:
```bash
usenc <encoder> --help
```

This shows all available parameters with descriptions.

### 4. Choose the Right Charset

- Use `utf8` (default) unless you have a specific reason not to
- Match input and output charsets to your data source and destination
- Test with non-ASCII characters to verify correct behavior

## Advanced Use Cases

### Custom Character Escaping

```bash
# Escape only special shell characters
echo 'echo $PATH; ls -la' | usenc cstring --include '$;&|><()'

# Create SQL-safe strings
echo "O'Reilly" | usenc hex --include "'" --prefix '\x'
```

### Multi-Stage Encoding

```bash
# Double URL encoding
echo "hello world" | usenc url | usenc url
# Output: hello%2520world

# Or use the doubleurl encoder
echo "hello world" | usenc doubleurl
# Output: hello%2520world
```

### Processing Binary Files

```bash
# View binary file as hex
usenc hex --bulk --suffix ' ' -i binary.dat

# Convert binary to base64 for transmission
usenc base64 --bulk -i image.png -o image.b64

# Extract and decode embedded URL-encoded strings
grep -o 'url=[^&]*' logfile.txt | cut -d= -f2 | usenc url -d
```

## See Also

- [Quickstart Guide](../getting-started/quickstart.md) - Basic usage examples
- [Adding Encoders](../development/adding-encoders.md) - Create custom encoders
- [Encoder Reference](../encoders/base64.md) - Individual encoder documentation
