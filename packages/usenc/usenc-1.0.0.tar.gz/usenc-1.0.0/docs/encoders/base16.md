### NAME

`base16` - Standard Base16 encoding (RFC 4648)

### DESCRIPTION

Encodes binary data using 16 ASCII characters (0-9, A-F)
Each character represents 4 bits of data.

Alternative alphabets:

- upper: 0-9, A-F (default, uppercase)
- lower: 0-9, a-f (lowercase)


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
`hello` | `68656C6C6F`
`hello world` | `68656C6C6F20776F726C64`
