### NAME

`unicode` - Unicode escapes encoding

### DESCRIPTION

Encodes each character with its unicode representation and an optional prefix/suffix.


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

#### --var-length
<div class="option-desc">
Use variable length encoding
</div>

#### --long
<div class="option-desc">
Use 8 hex digits instead of 4
</div>

### EXAMPLES

Sample  |   Encoded
--- | ---
`hello world` | `\u0068\u0065\u006C\u006C\u006F\u0020\u0077\u006F\u0072\u006C\u0064`
`café` | `\u0063\u0061\u0066\u00E9`
`日本語` | `\u65E5\u672C\u8A9E`
`🚀` | `\u1F680`
