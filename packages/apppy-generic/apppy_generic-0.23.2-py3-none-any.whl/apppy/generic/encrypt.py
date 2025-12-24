from os import urandom

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

BLOCK_SIZE = 16  # AES block size in bytes


class DecryptionFailedError(Exception):
    """Raised when there is an error while trying ot decrypt bytes"""

    def __init__(self):
        super().__init__("unable_to_decrypt")


class BytesEncrypter:
    """
    Service to encrypt data bytes.integers into strings based on a static
    alphabet. This allows the system to ofuscate the integer
    values to outside parties (e.g. database primary keys)
    """

    def __init__(self, passphrase: str, salt: str | bytes) -> None:
        self._passphrase = passphrase
        if isinstance(salt, str):
            self._salt = salt.encode("utf-8")
        else:
            self._salt = salt

        self._encryption_key = self.__derive_encryption_key()

    def __derive_encryption_key(self) -> bytes:
        passphrase_encoded = self._passphrase.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # AES-256 requires 32 bytes
            salt=self._salt,
            iterations=100000,
            backend=default_backend(),
        )
        return kdf.derive(passphrase_encoded)

    def encrypt_bytes(self, data: bytes) -> bytes:
        """
        Encrypt the entire data stream with AES-CBC and PKCS7 padding.
        A new IV is generated for each encryption operation.
        """
        iv = urandom(BLOCK_SIZE)
        cipher = Cipher(
            algorithms.AES(self._encryption_key), modes.CBC(iv), backend=default_backend()
        )
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(BLOCK_SIZE * 8).padder()
        padded_data = padder.update(data) + padder.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        return iv + encrypted_data

    def decrypt_bytes(self, data: bytes) -> bytes:
        """
        Decrypt the data stream with AES-CBC and PKCS7 unpadding.
        The IV is extracted from the first block of the encrypted data.
        """
        iv = data[:BLOCK_SIZE]
        encrypted_data = data[BLOCK_SIZE:]

        cipher = Cipher(
            algorithms.AES(self._encryption_key), modes.CBC(iv), backend=default_backend()
        )
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
        unpadder = padding.PKCS7(BLOCK_SIZE * 8).unpadder()
        try:
            return unpadder.update(decrypted_data) + unpadder.finalize()
        except ValueError as e:
            raise DecryptionFailedError() from e
