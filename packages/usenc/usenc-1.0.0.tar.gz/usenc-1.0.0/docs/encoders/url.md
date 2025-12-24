### NAME

`url` - Standard URL encoding (RFC 3986 percent encoding)

### DESCRIPTION

Encodes special characters and utf8 characters with a percent
prefixed hex value. Produces the same encoding as
javascript `encodeURIComponent` by default.


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
`hello world` | `hello%20world`
`http://example.org` | `http%3A%2F%2Fexample.org`
`index.php?key=value&other=1` | `index.php%3Fkey%3Dvalue%26other%3D1`
`<div>hello</div>` | `%3Cdiv%3Ehello%3C%2Fdiv%3E`
