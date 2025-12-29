from slip_plate.crypto import generate_dek, encrypt_with_dek, decrypt_with_dek
from slip_plate.shamir import split_dek, prepare_share, recover_dek_from_shares


def test_end_to_end_recovery_and_decrypt():
    dek = generate_dek(256)
    header = b"hdr"
    nonce, ciphertext, _ = encrypt_with_dek(dek, b"hello", header)
    blob = header + nonce + ciphertext

    parts = 3
    threshold = 2
    shares = split_dek(dek, parts, threshold)
    shares_bin = [prepare_share(s) for s in shares]
    recovered = recover_dek_from_shares(shares_bin[:threshold])

    parsed_header = blob[:len(header)]
    parsed_nonce = blob[len(header):len(header)+12]
    parsed_ciphertext = blob[len(header)+12:]
    out = decrypt_with_dek(recovered, parsed_nonce, parsed_ciphertext, parsed_header)
    assert out == b"hello"
