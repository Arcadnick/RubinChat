"""
CryptoProvider: GOST 34.10-2012 (signature), 34.11-2012 (Streebog), 28147-89 (CTR).
All heavy work run in thread pool to avoid blocking event loop.
"""
import asyncio
import base64
import os
from typing import Tuple

from pygost import gost34112012512
from pygost.gost28147 import cnt
from pygost.gost3410 import (
    CURVES,
    prv_unmarshal,
    pub_marshal,
    pub_unmarshal,
    public_key,
    sign as gost_sign,
    verify as gost_verify,
)

# GOST 28147-89 key size 256 bits = 32 bytes, block 64 bits = 8 bytes
GOST28147_KEYSIZE = 32
GOST28147_BLOCKSIZE = 8
GOST3410_PRIVATE_SIZE = 64
CURVE_NAME = "id-tc26-gost-3410-12-512-paramSetA"


def _curve():
    return CURVES[CURVE_NAME]


def _hash_sync(data: bytes) -> bytes:
    """Streebog 512 (GOST 34.11-2012)."""
    return gost34112012512.new(data).digest()


def _hash_for_sign_sync(data: bytes) -> bytes:
    """Digest for GOST 34.10-2012: Streebog and reverse byte order."""
    return _hash_sync(data)[::-1]


def _generate_keypair_sync() -> Tuple[bytes, bytes]:
    """Returns (private_key_64_bytes, public_key_marshalled_bytes)."""
    curve = _curve()
    raw = os.urandom(GOST3410_PRIVATE_SIZE)
    prv = prv_unmarshal(raw)
    pub = public_key(curve, prv)
    return raw, pub_marshal(pub, mode=2012)


def _sign_sync(private_key_bytes: bytes, data: bytes) -> bytes:
    """Sign data with GOST 34.10-2012. Returns signature bytes."""
    curve = _curve()
    prv = prv_unmarshal(private_key_bytes)
    dgst = _hash_for_sign_sync(data)
    sig = gost_sign(curve, prv, dgst, mode=2012)
    return sig


def _verify_sync(public_key_bytes: bytes, data: bytes, signature: bytes) -> bool:
    """Verify GOST 34.10-2012 signature."""
    curve = _curve()
    pub = pub_unmarshal(public_key_bytes, mode=2012)
    dgst = _hash_for_sign_sync(data)
    return gost_verify(curve, pub, dgst, signature, mode=2012)


def _encrypt_sync(key: bytes, plaintext: bytes, nonce: bytes) -> bytes:
    """GOST 28147-89 CTR. key 32 bytes, nonce 8 bytes."""
    if len(key) != GOST28147_KEYSIZE:
        raise ValueError("Key must be 32 bytes")
    if len(nonce) != GOST28147_BLOCKSIZE:
        raise ValueError("Nonce must be 8 bytes")
    return cnt(key, plaintext, iv=nonce)


def _decrypt_sync(key: bytes, ciphertext: bytes, nonce: bytes) -> bytes:
    """GOST 28147-89 CTR (same as encrypt)."""
    return _encrypt_sync(key, ciphertext, nonce)


class CryptoProvider:
    """Async wrapper over pygost. All methods are async."""

    async def generate_keypair(self) -> Tuple[bytes, bytes]:
        """Returns (private_key_64_bytes, public_key_marshalled_bytes)."""
        return await asyncio.to_thread(_generate_keypair_sync)

    async def hash(self, data: bytes) -> bytes:
        """Streebog 512 (GOST 34.11-2012)."""
        return await asyncio.to_thread(_hash_sync, data)

    async def sign(self, private_key_bytes: bytes, data: bytes) -> bytes:
        """Sign data. Returns signature bytes."""
        return await asyncio.to_thread(_sign_sync, private_key_bytes, data)

    async def verify(self, public_key_bytes: bytes, data: bytes, signature: bytes) -> bool:
        """Verify signature."""
        return await asyncio.to_thread(_verify_sync, public_key_bytes, data, signature)

    async def encrypt(self, key: bytes, plaintext: bytes, nonce: bytes) -> bytes:
        """GOST 28147-89 CTR. key 32 bytes, nonce 8 bytes."""
        return await asyncio.to_thread(_encrypt_sync, key, plaintext, nonce)

    async def decrypt(self, key: bytes, ciphertext: bytes, nonce: bytes) -> bytes:
        """GOST 28147-89 CTR."""
        return await asyncio.to_thread(_decrypt_sync, key, ciphertext, nonce)

    @staticmethod
    def generate_nonce() -> bytes:
        """Generate 8-byte nonce for CTR."""
        return os.urandom(GOST28147_BLOCKSIZE)

    async def encrypt_key_with_master(self, master_key: bytes, plaintext: bytes) -> str:
        """Encrypt key material with master key. Returns base64(nonce + ciphertext)."""
        nonce = self.generate_nonce()
        ct = await self.encrypt(master_key, plaintext, nonce)
        return base64.b64encode(nonce + ct).decode("ascii")

    async def decrypt_key_with_master(self, master_key: bytes, encrypted_b64: str) -> bytes:
        """Decrypt key material. Input is base64(nonce + ciphertext)."""
        raw = base64.b64decode(encrypted_b64.encode("ascii"))
        nonce, ct = raw[:GOST28147_BLOCKSIZE], raw[GOST28147_BLOCKSIZE:]
        return await self.decrypt(master_key, ct, nonce)
