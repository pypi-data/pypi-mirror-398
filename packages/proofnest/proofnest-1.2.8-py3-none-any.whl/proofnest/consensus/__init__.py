"""
ProofNest - Consensus Module (EXPERIMENTAL)

WARNING: This module is experimental and not part of the stable API.

Implements PoS + BFT consensus foundations:
- Conservative PoS base with BFT finality (2/3+ stake)
- PoUW as task marketplace layer (not consensus weight)

Key components:
- Block structure with Dilithium signatures
- Validator management with staking
- BFT finality gadget (2/3+ stake)
- VRF for leader selection
- Slashing for misbehavior
"""

from .block import (
    Block,
    BlockHeader,
    BlockBody,
    Transaction,
    TransactionType,
    Receipt,
    ReceiptStatus,
    create_genesis_block,
    GENESIS_TIMESTAMP,
)

__all__ = [
    'Block',
    'BlockHeader',
    'BlockBody',
    'Transaction',
    'TransactionType',
    'Receipt',
    'ReceiptStatus',
    'create_genesis_block',
    'GENESIS_TIMESTAMP',
]
