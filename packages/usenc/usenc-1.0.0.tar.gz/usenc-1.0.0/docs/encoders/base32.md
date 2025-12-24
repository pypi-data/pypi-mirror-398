### NAME

`base32` - Standard Base32 encoding (RFC 4648)

### DESCRIPTION

Encodes binary data using 32 ASCII characters (A-Z, 2-7)
Each character represents 5 bits of data.

Alternative alphabets:

- standard: A-Z, 2-7 (default, RFC 4648)
- hex: 0-9, A-V (Base32hex, RFC 4648)
- crockford: 0-9, A-Z excluding I, L, O, U (Crockford Base32)
- z: ybndrfg8ejkmcpqxot1uwisza345h769 (z-base-32, human-oriented)


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
`hello` | `NBSWY3DP`
`hello world` | `NBSWY3DPEB3W64TMMQ======`
