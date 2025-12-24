### NAME

`html` - HTML Entities encoding

### DESCRIPTION

Encodes each character with its html escaped entity, based on the WHATWG HTML Living Standard.
The full list of named character is available at https://html.spec.whatwg.org/multipage/named-characters.html

This encoder uses Python's html.entities module for the named characters, and encodes the
others with their decimal or hexadecimal representation.


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

#### --hex
<div class="option-desc">
Use hexadecimal instead of decimal
</div>

### EXAMPLES

Sample  |   Encoded
--- | ---
`hello world` | `hello world`
`<p>hello</p>` | `&#lt;p&#gt;hello&#lt;/p&#gt;`
`<a href="/hello">hello</a>` | `&#lt;a href=&#quot;/hello&#quot;&#gt;hello&#lt;/a&#gt;`
`café` | `caf&#eacute;`
