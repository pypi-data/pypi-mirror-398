from slip_plate.utils import bytes_to_bits, bits_to_bytes


def test_bits_bytes_roundtrip():
    b = b"\x01\x02\xFF"
    bits = bytes_to_bits(b)
    # ensure roundtrip conversion is consistent
    assert bits_to_bytes(bits) == b
