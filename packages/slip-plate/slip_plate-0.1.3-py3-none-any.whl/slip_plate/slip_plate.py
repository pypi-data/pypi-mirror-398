import random
import sys

from .crypto import generate_dek, encrypt_with_dek, decrypt_with_dek
from .shamir import split_dek, prepare_share, recover_dek_from_shares
from .plate import bits_to_plate


def main(dek_size=256, parts=3, threshold=2):
    try:
        plaintext = b"Secret message encrypted with DEK"
        dek = generate_dek(dek_size)
        header = b"ENC1v1AESGCM256"

        nonce, ciphertext, _ = encrypt_with_dek(dek, plaintext, header)
        blob = header + nonce + ciphertext
        print("Encrypted blob (hex):", blob.hex())

        shares_bytes = split_dek(dek, parts, threshold)
        shares_bin = [prepare_share(s) for s in shares_bytes]

        print(f"\n=== Shares OneKey-style ===")
        for idx, sh in enumerate(shares_bin, 1):
            print(f"\n=== KEK Share {idx} ===")
            print(bits_to_plate(sh))

        random.shuffle(shares_bin)
        recovery_bin = shares_bin[:threshold]
        recovered_dek = recover_dek_from_shares(recovery_bin)

        parsed_header = blob[:len(header)]
        parsed_nonce = blob[len(header):len(header)+12]
        parsed_ciphertext = blob[len(header)+12:]
        decrypted = decrypt_with_dek(recovered_dek, parsed_nonce, parsed_ciphertext, parsed_header)

        print("\nDecrypted plaintext:", decrypted)
        print("Recovery and decryption successful:", decrypted == plaintext)
    except KeyboardInterrupt:
            print("\nOprit de utilizator.")
            sys.exit(0)

if __name__ == "__main__":
    main()