from slip_plate.plate import bits_to_plate


def test_plate_output_contains_rows_and_separators():
    bits = '01' * 12
    plate = bits_to_plate(bits, bits_per_row=12, group=4)
    assert '|' in plate
    assert '─' in plate
