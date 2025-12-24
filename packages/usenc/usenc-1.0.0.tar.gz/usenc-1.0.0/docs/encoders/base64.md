### NAME

`base64` - Standard Base64 encoding (RFC 4648)

### DESCRIPTION

Encodes binary data using 64 ASCII characters (A-Z, a-z, 0-9, +, /)
Each character represents 6 bits of data.

Alternative alphabets:

- standard: A-Z, a-z, 0-9, +, / (default)
- url: A-Z, a-z, 0-9, -, _ (URL-safe variant)


### OPTIONS


#### --padding
<div class="option-desc">
Specify the character used as padding
</div>

#### --no-padding
<div class="option-desc">
Do not include a padding character
</div>

#### --alphabet
<div class="option-desc">
Custom alphabet to use for encoding (must have the same length as the base)
</div>

### EXAMPLES

Sample  |   Encoded
--- | ---
`hello` | `aGVsbG8=`
`hello world` | `aGVsbG8gd29ybGQ=`
