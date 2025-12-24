"""Encryption utils"""

import logging
from hashlib import md5
from pathlib import Path

from ccb_essentials.subprocess import shell_escape, subprocess_command


log = logging.getLogger(__name__)

# todo allow override by caller
OPENSSL = '/opt/local/bin/openssl'


def md5_file(path: Path) -> str:
    """Compute MD5 hash of a file and format it as hex digits."""
    with path.open('rb') as f:
        file_hash = md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def encrypt(source: Path, dest: Path, pass_file: Path) -> bool:
    """Encrypt a file with symmetric key."""
    log.debug('encrypt %s -> %s', source, dest)
    return _crypt(True, source, dest, pass_file)


def decrypt(source: Path, dest: Path, pass_file: Path) -> bool:
    """Decrypt a file with symmetric key."""
    log.debug('decrypt %s -> %s', source, dest)
    return _crypt(False, source, dest, pass_file)


# $ openssl help enc
# Usage: enc [options]
# Valid options are:
#  -help               Display this summary
#  -list               List ciphers
#  -ciphers            Alias for -list
#  -in infile          Input file
#  -out outfile        Output file
#  -pass val           Passphrase source
#  -e                  Encrypt
#  -d                  Decrypt
#  -p                  Print the iv/key
#  -P                  Print the iv/key and exit
#  -v                  Verbose output
#  -nopad              Disable standard block padding
#  -salt               Use salt in the KDF (default)
#  -nosalt             Do not use salt in the KDF
#  -debug              Print debug info
#  -a                  Base64 encode/decode, depending on encryption flag
#  -base64             Same as option -a
#  -A                  Used with -[base64|a] to specify base64 buffer as a single line
#  -bufsize val        Buffer size
#  -k val              Passphrase
#  -kfile infile       Read passphrase from file
#  -K val              Raw key, in hex
#  -S val              Salt, in hex
#  -iv val             IV in hex
#  -md val             Use specified digest to create a key from the passphrase
#  -iter +int          Specify the iteration count and force use of PBKDF2
#  -pbkdf2             Use password-based key derivation function 2
#  -none               Don't encrypt
#  -*                  Any supported cipher
#  -rand val           Load the file(s) into the random number generator
#  -writerand outfile  Write random data to the specified file
#  -z                  Use zlib as the 'encryption'
#  -engine val         Use engine, possibly a hardware device
def _crypt(do_encrypt: bool, source: Path, dest: Path, pass_file: Path) -> bool:
    """Encrypt or decrypt a file."""
    assert source.is_file(), f'source is not a file: {source}'
    assert not dest.exists(), f'failed to overwrite dest: {dest}'
    if not dest.parent.exists():
        dest.parent.mkdir(parents=True)
    mode = '-e' if do_encrypt else '-d'
    # todo expose params
    cmd = f"""{OPENSSL} enc {mode} -in {shell_escape(source)} -out {shell_escape(dest)} \
        -aes-256-cbc -md sha512 -pbkdf2 -iter 100000 -salt -bufsize 524288 \
        -kfile {shell_escape(pass_file)}"""
    log.debug(cmd)
    return subprocess_command(cmd) is not None
