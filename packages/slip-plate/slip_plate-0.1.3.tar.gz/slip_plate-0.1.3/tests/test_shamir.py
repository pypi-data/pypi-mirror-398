from slip_plate.shamir import split_dek, prepare_share, recover_dek_from_shares
from slip_plate.utils import bytes_to_bits, bits_to_bytes


def test_shamir_split_and_recover():
    dek = b"\x00" * 32
    parts = 3
    threshold = 2
    shares = split_dek(dek, parts, threshold)
    shares_bin = [prepare_share(s) for s in shares]
    recovered = recover_dek_from_shares(shares_bin[:threshold])
    assert recovered == dek
