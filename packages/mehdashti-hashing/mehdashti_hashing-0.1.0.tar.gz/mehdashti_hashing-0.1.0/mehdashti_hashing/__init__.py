"""
Fast Hashing Utilities

- xxHash128: Ultra-fast non-cryptographic hashing for business keys and deduplication
- BLAKE3: Fast cryptographic hashing for data integrity and change detection
"""

from mehdashti_hashing.core import (
    hash_business_key,
    hash_data,
    hash_dict,
    hash_file,
)

__all__ = [
    "hash_business_key",
    "hash_data",
    "hash_dict",
    "hash_file",
]

__version__ = "0.1.0"
