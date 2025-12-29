"""
ProofNest Cryptography Module

Implements quantum-proof cryptography per NIST FIPS 204 (ML-DSA).
Reference: https://csrc.nist.gov/pubs/fips/204/final
"""

from .constants import (
    AlgorithmID,
    CONTAINER_SIZES,
    DILITHIUM_SIZES,
    MAGIC,
    VERSION,
)
from .container import SignatureContainer
from .kdf import HonestKDF
from .dilithium import (
    generate_ml_dsa_keypair,
    ml_dsa_sign,
    ml_dsa_verify,
)

__all__ = [
    "AlgorithmID",
    "CONTAINER_SIZES",
    "DILITHIUM_SIZES",
    "MAGIC",
    "VERSION",
    "SignatureContainer",
    "HonestKDF",
    "generate_ml_dsa_keypair",
    "ml_dsa_sign",
    "ml_dsa_verify",
]
