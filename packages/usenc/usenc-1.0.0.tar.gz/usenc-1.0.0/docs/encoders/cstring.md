### NAME

`cstring` - C string escaping

### DESCRIPTION

Encodes special characters and utf8 characters with a \x prefixed hex value.


### OPTIONS


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
`hello world` | `hello\x20world`
`escape "me"` | `escape\x20\x22me\x22`
`café` | `caf\xC3\xA9`
`http://example.org` | `http\x3A\x2F\x2Fexample.org`
