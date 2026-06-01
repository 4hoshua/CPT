#!/usr/bin/python3

""" ptexplorer.py: Convert Packet Tracer files (.pkt/.pka) to XML and vice versa"""

__author__ = 'axcheron'
__license__ = 'MIT License'
__version__ = '0.1'

import argparse
import importlib
import site
import sys
import zlib

TwofishFactory = None


NEW_KEY = bytes([137] * 16)
NEW_IV = bytes([16] * 16)
BLOCK_SIZE = 16


def _attempt_install(package: str) -> bool:
    """Try to install a package for the current interpreter."""
    import subprocess

    try:
        print(f"[*] Attempting to install missing dependency '{package}' for {sys.executable}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        importlib.invalidate_caches()
        _ensure_user_site_on_path()
        return True
    except Exception as exc:  # pragma: no cover - best effort helper
        print(f"[!] Automatic installation of '{package}' failed: {exc}")
        return False


def _xor_with_length(data: bytes) -> bytes:
    """XOR each byte with (len(data) - index)."""
    length = len(data)
    result = bytearray(data)
    for i in range(length):
        result[i] ^= (length - i) & 0xFF
    return bytes(result)


def _reverse_obfuscate(data: bytes) -> bytes:
    """Stage 4 obfuscation used by modern Packet Tracer files."""
    length = len(data)
    length_mod = length & 0xFF
    output = bytearray(length)
    for i, byte in enumerate(data):
        key = ((1 - i) & 0xFF) * length_mod & 0xFF
        output[length - 1 - i] = byte ^ key
    return bytes(output)


def _reverse_deobfuscate(obfuscated: bytes) -> bytes:
    """Inverse of _reverse_obfuscate."""
    length = len(obfuscated)
    length_mod = length & 0xFF
    output = bytearray(length)
    for i in range(length):
        key = ((1 - i) & 0xFF) * length_mod & 0xFF
        output[i] = obfuscated[length - 1 - i] ^ key
    return bytes(output)


def _read_zlib_payload(payload: bytes) -> bytes:
    """Extract and inflate a zlib payload prefixed with the uncompressed size."""
    if len(payload) < 4:
        raise ValueError("payload too small to contain size prefix")

    expected_size = int.from_bytes(payload[:4], byteorder="big")
    xml = zlib.decompress(payload[4:])
    if expected_size != len(xml):
        print(f"[!] Warning: expected XML size {expected_size} bytes but got {len(xml)} bytes")
    return xml


def _build_zlib_payload(xml_bytes: bytes) -> bytes:
    """Compress XML and prepend the original size."""
    return len(xml_bytes).to_bytes(4, "big") + zlib.compress(xml_bytes)


def is_legacy_format(data: bytes) -> bool:
    """Heuristic detection for pre-7.3 Packet Tracer files."""
    length = len(data)
    if length <= 5:
        return True

    check_4 = (data[4] ^ ((length - 4) & 0xFF)) == 0x78
    check_5 = (data[5] ^ ((length - 5) & 0xFF)) == 0x9C
    return check_4 or check_5


def _decode_legacy(data: bytes) -> bytes:
    """Decode legacy Packet Tracer files (simple XOR + zlib)."""
    length = len(data)
    out = bytearray()
    for byte in data:
        out.append(((byte ^ length) & 0xFF))
        length -= 1

    return zlib.decompress(bytes(out[4:]))


def _encode_legacy(xml_bytes: bytes) -> bytes:
    """Encode XML using the legacy Packet Tracer format."""
    payload = _build_zlib_payload(xml_bytes)
    out_data = bytearray(payload)
    length = len(out_data)

    xor_out = bytearray()
    for byte in out_data:
        xor_out.append(((byte ^ length) & 0xFF))
        length -= 1

    return bytes(xor_out)


def _ensure_twofish():
    global TwofishFactory
    if TwofishFactory is not None:
        return

    _ensure_imp_compat()
    _ensure_user_site_on_path()

    try:
        from twofish import Twofish as _Twofish  # type: ignore

        TwofishFactory = lambda key: _Twofish(key)
        return
    except ImportError:
        if _attempt_install("twofish"):
            try:
                from twofish import Twofish as _Twofish  # type: ignore
            except ImportError:
                pass
            else:
                TwofishFactory = lambda key: _Twofish(key)
                return

    try:
        from Crypto.Cipher import Twofish as _CryptoTwofish  # type: ignore

        TwofishFactory = lambda key: _CryptoTwofish.new(key, _CryptoTwofish.MODE_ECB)
        return
    except ImportError:
        if _attempt_install("pycryptodome"):
            try:
                from Crypto.Cipher import Twofish as _CryptoTwofish  # type: ignore
            except ImportError:
                pass
            else:
                TwofishFactory = lambda key: _CryptoTwofish.new(key, _CryptoTwofish.MODE_ECB)
                return

    try:
        from Cryptodome.Cipher import Twofish as _CdomTwofish  # type: ignore

        TwofishFactory = lambda key: _CdomTwofish.new(key, _CdomTwofish.MODE_ECB)
        return
    except ImportError:
        if _attempt_install("pycryptodome"):
            try:
                from Cryptodome.Cipher import Twofish as _CdomTwofish  # type: ignore
            except ImportError:
                pass
            else:
                TwofishFactory = lambda key: _CdomTwofish.new(key, _CdomTwofish.MODE_ECB)
                return

    raise RuntimeError(
        "A Twofish implementation is required for modern Packet Tracer files. Install one via "
        "'python -m pip install twofish' or ensure pycryptodome is available."
    )


def _ensure_user_site_on_path():
    """Ensure user site-packages is on sys.path for the running interpreter."""
    try:
        usersite = site.getusersitepackages()
    except Exception:  # pragma: no cover
        return
    if isinstance(usersite, str):
        paths = [usersite]
    else:
        paths = list(usersite)
    for path in paths:
        if path and path not in sys.path:
            sys.path.append(path)


def _ensure_imp_compat():
    """Provide a minimal imp.find_module implementation for Python 3.13+."""
    if "imp" in sys.modules:
        return

    import types
    import importlib.util
    import os

    imp_module = types.ModuleType("imp")

    def find_module(name, package=None):
        spec = importlib.util.find_spec(name, package)
        if spec is None or spec.origin is None:
            raise ModuleNotFoundError(f"Cannot find module {name}")
        return None, spec.origin, None

    def new_module(name):
        return types.ModuleType(name)

    imp_module.find_module = find_module
    imp_module.new_module = new_module
    imp_module.__dict__["cache_from_source"] = lambda *args, **kwargs: None
    sys.modules["imp"] = imp_module


def _split_cipher_and_tag(processed: bytes) -> tuple[bytes, bytes]:
    if len(processed) < 16:
        raise ValueError("encrypted payload is too short to contain an authentication tag")
    return processed[:-16], processed[-16:]


def _create_twofish():
    _ensure_twofish()
    return TwofishFactory(NEW_KEY)  # type: ignore


def _xor_bytes(a: bytes, b: bytes) -> bytes:
    if len(a) != len(b):
        raise ValueError("xor inputs must have the same length")
    return bytes(x ^ y for x, y in zip(a, b))


def _gf_double(block: bytes) -> bytes:
    """Multiply by 2 in GF(2^128) with polynomial x^128 + x^7 + x^2 + x + 1."""
    assert len(block) == BLOCK_SIZE
    value = int.from_bytes(block, "big")
    overflow = (value >> (BLOCK_SIZE * 8 - 1)) & 1
    value = ((value << 1) & ((1 << (BLOCK_SIZE * 8)) - 1))
    if overflow:
        value ^= 0x87
    return value.to_bytes(BLOCK_SIZE, "big")


def _cmac(message: bytes) -> bytes:
    cipher = _create_twofish()
    L = cipher.encrypt(bytes(BLOCK_SIZE))
    subkey1 = _gf_double(L)
    subkey2 = _gf_double(subkey1)

    full_blocks = len(message) // BLOCK_SIZE
    blocks = [message[i * BLOCK_SIZE:(i + 1) * BLOCK_SIZE] for i in range(full_blocks)]
    remainder = message[full_blocks * BLOCK_SIZE:]

    if len(remainder) == 0 and full_blocks > 0:
        last_block = _xor_bytes(blocks.pop(), subkey1)
    else:
        block = remainder
        block += b"\x80"
        block += b"\x00" * (BLOCK_SIZE - len(block))
        last_block = _xor_bytes(block, subkey2)

    state = bytes(BLOCK_SIZE)
    for block in blocks:
        state = cipher.encrypt(_xor_bytes(block, state))

    return cipher.encrypt(_xor_bytes(last_block, state))


def _omac(tag: int, data: bytes) -> bytes:
    prefix = (b"\x00" * (BLOCK_SIZE - 1)) + bytes([tag & 0xFF])
    return _cmac(prefix + data)


def _ctr_crypt(counter_block: bytes, data: bytes) -> bytes:
    cipher = _create_twofish()
    counter = int.from_bytes(counter_block, "big")
    mask = (1 << (BLOCK_SIZE * 8)) - 1

    result = bytearray(len(data))
    for offset in range(0, len(data), BLOCK_SIZE):
        keystream = cipher.encrypt(counter.to_bytes(BLOCK_SIZE, "big"))
        chunk = data[offset:offset + BLOCK_SIZE]
        for idx, byte in enumerate(chunk):
            result[offset + idx] = byte ^ keystream[idx]
        counter = (counter + 1) & mask

    return bytes(result)


def _twofish_eax_decrypt(cipher_text: bytes, tag: bytes, nonce: bytes) -> bytes:
    nonce_tag = _omac(0, nonce)
    header_tag = _omac(1, b"")
    message_tag = _omac(2, cipher_text)

    if _xor_bytes(_xor_bytes(nonce_tag, header_tag), message_tag) != tag:
        raise ValueError("authentication tag mismatch")

    return _ctr_crypt(nonce_tag, cipher_text)


def _twofish_eax_encrypt(plain: bytes, nonce: bytes) -> tuple[bytes, bytes]:
    nonce_tag = _omac(0, nonce)
    header_tag = _omac(1, b"")
    cipher_text = _ctr_crypt(nonce_tag, plain)
    message_tag = _omac(2, cipher_text)
    tag = _xor_bytes(_xor_bytes(nonce_tag, header_tag), message_tag)
    return cipher_text, tag


def _decode_modern(data: bytes) -> bytes:
    """Decode modern Packet Tracer files (Twofish EAX + obfuscation)."""
    processed = _reverse_deobfuscate(data)
    cipher_text, tag = _split_cipher_and_tag(processed)

    plain = _twofish_eax_decrypt(cipher_text, tag, NEW_IV)

    payload = _xor_with_length(plain)
    return _read_zlib_payload(payload)


def _encode_modern(xml_bytes: bytes) -> bytes:
    """Encode XML using the modern Packet Tracer format."""
    payload = _build_zlib_payload(xml_bytes)
    obfuscated = _xor_with_length(payload)

    cipher_text, tag = _twofish_eax_encrypt(obfuscated, NEW_IV)

    encrypted = cipher_text + tag
    return _reverse_obfuscate(encrypted)

def ptfile_decode(infile, outfile, force_legacy=False):
    with open(infile, 'rb') as f:
        in_data = f.read()

    print("[*] Opening Packet Tracer file '%s' " % infile)
    print("[*] File size compressed = %d bytes" % len(in_data))

    legacy = force_legacy or is_legacy_format(in_data)

    if legacy:
        xml_data = _decode_legacy(in_data)
    else:
        xml_data = _decode_modern(in_data)

    o_size = len(xml_data)
    print("[*] File size uncompressed = %d bytes" % o_size)

    print("[*] Writing XML to '%s'" % outfile)
    with open(outfile, 'wb') as f:
        f.write(xml_data)


def ptfile_encode(infile, outfile, legacy=False):
    with open(infile, 'rb') as f:
        in_data = f.read()

    i_size = len(in_data)

    print("[*] Opening XML file '%s' " % infile)
    print("[*] File size uncompressed = %d bytes" % i_size)

    if legacy:
        pkt_data = _encode_legacy(in_data)
    else:
        pkt_data = _encode_modern(in_data)

    print("[*] File size compressed = %d bytes" % len(pkt_data))
    print("[*] Writing PKT to '%s'" % outfile)
    with open(outfile, 'wb') as f:
        f.write(pkt_data)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Convert Packet Tracer files (.pkt/.pka) to XML and vice versa")

    group = parser.add_mutually_exclusive_group()

    group.add_argument("-d", "--decode", help="Converts Packet Tracer file to XML", action="store_true")
    group.add_argument("-e", "--encode", help="Converts XML to Packet Tracer File", action="store_true")
    parser.add_argument("infile", help="Packet Tracer file", action="store", type=str)
    parser.add_argument("outfile", help="Output file (XML)", action="store", type=str)
    parser.add_argument(
        "--legacy",
        help="Force legacy Packet Tracer format (pre-7.3).",
        action="store_true",
    )

    args = parser.parse_args()

    if args.decode:
        ptfile_decode(args.infile, args.outfile, force_legacy=args.legacy)
    elif args.encode:
        ptfile_encode(args.infile, args.outfile, legacy=args.legacy)
    else:
        parser.print_help()
        exit(1)
