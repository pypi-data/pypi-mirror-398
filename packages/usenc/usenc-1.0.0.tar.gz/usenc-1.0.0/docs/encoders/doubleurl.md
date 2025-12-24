### NAME

`doubleurl` - Double URL encoding (RFC 3986 percent encoding)

### DESCRIPTION

Apply the URL Encoder twice on the input string.

It is the same as doing `echo hello | usenc url | usenc url`


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
`hello world` | `hello%2520world`
`http://example.org` | `http%253A%252F%252Fexample.org`
`index.php?key=value&other=1` | `index.php%253Fkey%253Dvalue%2526other%253D1`
`<div>hello</div>` | `%253Cdiv%253Ehello%253C%252Fdiv%253E`
