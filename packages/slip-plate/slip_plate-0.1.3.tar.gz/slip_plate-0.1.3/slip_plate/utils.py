"""Utility helpers: bits/bytes conversions."""

def bytes_to_bits(b: bytes) -> str:
    return ''.join(f'{byte:08b}' for byte in b)


def bits_to_bytes(bstr: str) -> bytes:
    return bytes(int(bstr[i:i+8], 2) for i in range(0, len(bstr), 8))

