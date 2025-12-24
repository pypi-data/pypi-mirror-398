# crypto.py

Tools to simplify cryptographic operations on the filesystem.

- **MD5 hashing**: Generate the MD5 hash for a file.
- **Encryption & decryption**: Encrypt and decrypt files with a symmetric key stored in a password file.

## Example Usage

### Calculate the MD5 fingerprint/checksum for a file

*python*

```python
f = pathlib.Path('output.txt')
print("Hello, World!", file=open(f, 'w'))
print(md5_file(f))  # bea8252ff4e80f41719ea13cdf007273
```

*shell*

```shell
$ md5 output.txt 
MD5 (output.txt) = bea8252ff4e80f41719ea13cdf007273
```

### Encrypt a file

This is an opinionated wrapper around the `openssl` command-line tool.

*python*

```python
secret = pathlib.Path('secret.txt')  # Secret is plain text: store it somewhere safe!
print("This is my secret password", file=open(secret, 'w'))
plain_text_in = pathlib.Path('plain_text_in.txt')
print("This is plain text", file=open(plain_text_in, 'w'))
encrypted = pathlib.Path('plain_text.enc')  # Go ahead and send this one out over the internet.
assert encrypt(plain_text_in, encrypted, secret)
```

### Decrypt a file

*python*

```python
plain_text_out = pathlib.Path('plain_text_out.txt')
assert decrypt(encrypted, plain_text_out, secret)
print(open(plain_text_out, 'r').read())  # This is plain text.
```
