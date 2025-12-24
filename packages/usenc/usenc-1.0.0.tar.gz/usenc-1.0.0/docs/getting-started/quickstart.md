# Quick Start Guide

This guide will help you get started with usenc quickly.

## Basic Usage

### Command Line

The basic syntax is:

```bash
usenc <encoder> [options]
```

### Encode from stdin

```bash
echo "hello world" | usenc url
# Output: hello%20world
```

### Decode

Use the `-d` or `--decode` flag:

```bash
echo "hello%20world" | usenc url -d
# Output: hello world
```

### File Input/Output

Read from and write to files:

```bash
# Encode file
usenc url -i input.txt -o output.txt

# Decode file
usenc url -d -i encoded.txt -o decoded.txt
```

### Piping

usenc works great with Unix pipes:

```bash
# Encode and decode in a pipeline
echo "test data" | usenc url | usenc url -d

# Process multiple lines
cat file.txt | usenc url > encoded.txt
```

## Encoder-Specific Options

Each encoder may have its own options. Use `--help` after the encoder name to see them:

```bash
usenc url --help
```

For example, the `url` encoder takes `--include` and `--exclude` options

```bash
echo "hello-wor.ld" | usenc url --include "-" --exclude "."
# Output: hello%2Dwor.ld
```

## Advanced examples

```bash
echo "hello world" | usenc hex --prefix '${' --suffix '}' --exclude ' '
# Output: ${68}${65}${6C}${6C}${6F} ${77}${6F}${72}${6C}${64}
```

## Python API

### Basic Encoding

```python
from usenc import encode, decode

# Encode
encoded = encode('hello world', 'url')
print(encoded)  # hello%20world

# Decode
decoded = decode(encoded, 'url')
print(decoded)  # hello world
```

### With Parameters

```python
from usenc import encode, decode

# Include additional characters
encoded = encode('hello-world', 'url', include='-')
print(encoded)  # hello%2Dworld

# Exclude characters from encoding
encoded = encode('path/to/file', 'url', exclude='/')
print(encoded)  # path/to/file
```

## Common Use Cases

### Encoding parameters to use in URL

```bash
echo "name=John Doe&email=john@example.com" | usenc url
# Output: name%3DJohn%20Doe%26email%3Djohn%40example.com
```

### Binary files to text

```bash
cat elf_file | usenc -b base64
# Output: aGVsbG8gd29ybGQ=
```

### Batch Processing

```bash
usenc url -i wordlist.txt -o url_encoded_wordlist.txt
usenc html -i wordlist.txt -o html_escaped_wordlist.txt
```

### Insert string in source code

```bash
echo "日本語" | usenc cstring
# Output: \xE6\x97\xA5\xE6\x9C\xAC\xE8\xAA\x9E
```

### Hash sum of file

```bash
usenc -i file -b md5 --lowercase
# Output: 5eb63bbbe01eeed093cb22bb8f5acdc3
```

## Next Steps

- Learn about all available [Encoders](../encoders/url.md)
- Check the [API Reference](../api/core.md)
- [Add your own encoder](../development/adding-encoders.md)
