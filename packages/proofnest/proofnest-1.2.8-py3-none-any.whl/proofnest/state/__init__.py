"""
ProofNest - State Management Module (EXPERIMENTAL)

WARNING: This module is experimental and not part of the stable API.

Implements minimal L1 state with:
- Verkle tree for efficient proofs
- State rent and expiry
- Commitment storage
- Archival snapshots

Design: Minimal L1 state with commitments, application state to rollups.
"""

from .verkle import (
    VerkleTree,
    VerkleNode,
    VerkleProof,
    StateCommitment,
    hash_key,
    EMPTY_ROOT,
)

__all__ = [
    'VerkleTree',
    'VerkleNode',
    'VerkleProof',
    'StateCommitment',
    'hash_key',
    'EMPTY_ROOT',
]
