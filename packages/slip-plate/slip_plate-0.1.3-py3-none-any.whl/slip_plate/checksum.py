import hashlib


def determine_checksum_bits(bits_len: int) -> int:
    """Decide dynamic checksum bits based on share size"""
    if bits_len <= 144:    # 128-bit DEK
        return 8
    elif bits_len <= 204:  # 192-bit DEK
        return 16
    else:                  # 256-bit DEK
        return 24


def determine_plate_checksum_bits(bits_len: int) -> int:
    """Decide dynamic checksum bits based on plate share size"""
    if bits_len <= 144:    # 128-bit DEK
        return 8
    elif bits_len <= 216:  # 192-bit DEK
        return 16
    else:                  # 256-bit DEK
        return 24


def add_checksum(bits: str) -> str:
    """Append a truncated sha256 checksum to the bitstring."""
    checksum_bits_len = determine_checksum_bits(len(bits))
    h = hashlib.sha256(bits.encode()).hexdigest()
    checksum_bits = bin(int(h, 16))[2:].zfill(256)[:checksum_bits_len]
    return bits + checksum_bits


def compute_expected_checksum(bits: str, checksum_bits_len: int) -> str:
    h = hashlib.sha256(bits.encode()).hexdigest()
    return bin(int(h, 16))[2:].zfill(256)[:checksum_bits_len]
