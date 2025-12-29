from pyshamir import split, combine
from .utils import bytes_to_bits, bits_to_bytes
from .checksum import add_checksum, determine_checksum_bits, compute_expected_checksum


def prepare_share(s_bytes: bytes) -> str:
    bits = bytes_to_bits(s_bytes)
    return add_checksum(bits)


def split_dek(dek_bytes: bytes, parts: int, threshold: int):
    """Return list of raw share bytes from pyshamir."""
    return split(dek_bytes, parts, threshold)


def recover_dek_from_shares(shares_bin) -> bytes:
    recovery_bytes = []
    for idx, s in enumerate(shares_bin, 1):
        checksum_bits_len = determine_checksum_bits(len(s)-determine_checksum_bits(len(s)))
        if len(s) < checksum_bits_len:
            raise ValueError(f"Share {idx} too short for checksum!")

        data_bits = s[:-checksum_bits_len]
        checksum_bits = s[-checksum_bits_len:]

        expected_checksum = compute_expected_checksum(data_bits, checksum_bits_len)

        if checksum_bits != expected_checksum:
            raise ValueError(f"Checksum invalid on Share {idx}!")

        recovery_bytes.append(bits_to_bytes(data_bits))

    return combine(recovery_bytes)
