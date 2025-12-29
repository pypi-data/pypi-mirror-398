from slip_plate.checksum import add_checksum, determine_checksum_bits, compute_expected_checksum


def test_add_checksum_length():
    bits = '0' * 128
    out = add_checksum(bits)
    exp_len = 128 + determine_checksum_bits(128)
    assert len(out) == exp_len


def test_compute_expected_checksum():
    bits = '1010'
    c = compute_expected_checksum(bits, 8)
    assert isinstance(c, str) and len(c) == 8
