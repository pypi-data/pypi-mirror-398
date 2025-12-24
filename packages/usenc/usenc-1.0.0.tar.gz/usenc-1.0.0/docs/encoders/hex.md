### NAME

`hex` - Hexadecimal string encoding

### DESCRIPTION

Encodes each character with its hex 2-digits representation and an optional prefix/suffix


### OPTIONS


#### --prefix
<div class="option-desc">
Prefix string to each encoded character
</div>

#### --suffix
<div class="option-desc">
Suffix string to each encoded character
</div>

#### --include
<div class="option-desc">
Characters that should be encoded (can contain 'all', 'utf8' or 'ascii')
</div>

#### --exclude
<div class="option-desc">
Characters that should not be encoded
</div>

#### --regex
<div class="option-desc">
Regex override for characters that should be encoded
</div>

#### --lowercase
<div class="option-desc">
Use lowercase hex digits
</div>

### EXAMPLES

Sample  |   Encoded
--- | ---
`hello world` | `68656C6C6F20776F726C64`
`escape "me"` | `65736361706520226D6522`
`café` | `636166C3A9`
`http://example.org` | `687474703A2F2F6578616D706C652E6F7267`
