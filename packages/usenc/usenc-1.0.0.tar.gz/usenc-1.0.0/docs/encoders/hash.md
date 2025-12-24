### NAME

`hash` - Base hash encoder using python hashlib

### DESCRIPTION

This encoder computes cryptographic hashes of input bytes and outputs
the resulting hex digest. Hash functions are one-way operations and
cannot be decoded.

Can be used directly with --hash-name parameter. Supports any hash in
your OpenSSL installation (`openssl list -digest-algorithms`)


### OPTIONS


#### --algorithm
<div class="option-desc">
Hash algorithm name (e.g., md5, sha256, sha512)
</div>

#### --lowercase
<div class="option-desc">
Output hex digest in lowercase
</div>

### EXAMPLES

Sample  |   Encoded
--- | ---
`hello world (md5)` | `5EB63BBBE01EEED093CB22BB8F5ACDC3`
`hello world (ripemd)` | `98C615784CCB5FE5936FBC0CBE9DFDB408D92F0F`
`hello world (sha3-224)` | `DFB7F18C77E928BB56FAEB2DA27291BD790BC1045CDE45F3210BB6C5`
