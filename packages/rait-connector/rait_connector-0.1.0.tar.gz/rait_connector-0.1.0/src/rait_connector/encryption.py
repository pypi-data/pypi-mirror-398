"""Encryption helper for the package.

This module provides an `Encryptor` class which performs
RSA-OAEP (to encrypt the AES key) together with AES-256-GCM
(to encrypt the payload). The class accepts keys in multiple
formats (PEM bytes/str or already-loaded key objects) to make
it convenient when fetching keys from an API.

Package format used (same as existing utilities):
- 4 bytes little-endian unsigned int: length of RSA-encrypted AES key
- encrypted AES key (variable)
- 12 bytes: AES-GCM nonce
- 16 bytes: AES-GCM auth tag
- ciphertext (variable)
"""

from __future__ import annotations

import os
import struct
from typing import Optional, Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptorError(Exception):
    """Raised for encryption/decryption errors produced by `Encryptor`."""


class Encryptor:
    """Perform RSA-OAEP + AES-GCM encryption and decryption.

    Key inputs supported for `public_key` / `private_key`:
    - PEM `bytes` or `str` containing the key
    - A loaded `RSAPublicKey` or `RSAPrivateKey` object from
      `cryptography.hazmat.primitives.asymmetric.rsa`

    Typical usage:
        encryptor = Encryptor(public_key=pem_bytes)
        package = encryptor.encrypt(b"secret data")

        decryptor = Encryptor(private_key=private_pem)
        plaintext = decryptor.decrypt(package)
    """

    AES_KEY_BYTES = 32
    GCM_NONCE_BYTES = 12
    GCM_TAG_BYTES = 16

    def __init__(
        self,
        public_key: Optional[Union[bytes, str, object]] = None,
        private_key: Optional[Union[bytes, str, object]] = None,
        private_key_password: Optional[bytes] = None,
    ) -> None:
        self._public_key = None
        self._private_key = None

        if public_key is not None:
            self._public_key = self._load_public_key(public_key)
        if private_key is not None:
            self._private_key = self._load_private_key(
                private_key, private_key_password
            )

    def _load_public_key(self, key: Union[bytes, str, object]):
        if isinstance(key, str):
            key = key.encode()

        if isinstance(key, (bytes, bytearray)):
            try:
                return serialization.load_pem_public_key(key, backend=default_backend())
            except Exception as exc:
                raise EncryptorError(f"Failed to load public key: {exc}") from exc

        return key

    def _load_private_key(
        self, key: Union[bytes, str, object], password: Optional[bytes]
    ):
        if isinstance(key, str):
            key = key.encode()

        if isinstance(key, (bytes, bytearray)):
            try:
                return serialization.load_pem_private_key(
                    key, password=password, backend=default_backend()
                )
            except Exception as exc:
                raise EncryptorError(f"Failed to load private key: {exc}") from exc

        return key

    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """Encrypt `data` and return packed bytes.

        Args:
            data: plaintext bytes or string

        Returns:
            Packaged encrypted payload

        Raises:
            EncryptorError: On failure or missing public key
        """
        if self._public_key is None:
            raise EncryptorError("Public key not provided for encryption")

        try:
            plaintext = (
                data
                if isinstance(data, (bytes, bytearray))
                else str(data).encode("utf-8")
            )

            aes_key = os.urandom(self.AES_KEY_BYTES)
            aesgcm = AESGCM(aes_key)
            nonce = os.urandom(self.GCM_NONCE_BYTES)
            encrypted = aesgcm.encrypt(nonce, plaintext, None)

            ciphertext = encrypted[: -self.GCM_TAG_BYTES]
            tag = encrypted[-self.GCM_TAG_BYTES :]

            encrypted_aes_key = self._public_key.encrypt(
                aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            encrypted_key_length = len(encrypted_aes_key)
            package = (
                struct.pack("<I", encrypted_key_length)
                + encrypted_aes_key
                + nonce
                + tag
                + ciphertext
            )

            return package

        except Exception as exc:
            raise EncryptorError(f"Encryption failed: {exc}") from exc

    def decrypt(self, package: bytes) -> bytes:
        """Decrypt a packaged payload created by `encrypt`.

        Args:
            package: Bytes previously produced by `encrypt`

        Returns:
            Plaintext

        Raises:
            EncryptorError: On failure or missing private key
        """
        if self._private_key is None:
            raise EncryptorError("Private key not provided for decryption")

        try:
            if len(package) < 4:
                raise EncryptorError("Invalid package: too short")

            (enc_key_len,) = struct.unpack_from("<I", package, 0)
            offset = 4
            end_enc_key = offset + enc_key_len

            if len(package) < end_enc_key + self.GCM_NONCE_BYTES + self.GCM_TAG_BYTES:
                raise EncryptorError("Invalid package: truncated")

            encrypted_aes_key = package[offset:end_enc_key]
            offset = end_enc_key
            nonce = package[offset : offset + self.GCM_NONCE_BYTES]
            offset += self.GCM_NONCE_BYTES
            tag = package[offset : offset + self.GCM_TAG_BYTES]
            offset += self.GCM_TAG_BYTES
            ciphertext = package[offset:]

            aes_key = self._private_key.decrypt(
                encrypted_aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            encrypted_blob = ciphertext + tag

            aesgcm = AESGCM(aes_key)
            plaintext = aesgcm.decrypt(nonce, encrypted_blob, None)

            return plaintext

        except Exception as exc:
            raise EncryptorError(f"Decryption failed: {exc}") from exc


__all__ = ["Encryptor", "EncryptorError"]
