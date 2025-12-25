"""
Core Hashing Module

Provides xxHash128 and BLAKE3 hashing utilities.
"""

import json
from pathlib import Path
from typing import Any

import blake3
import xxhash


def hash_business_key(*args: Any) -> str:
    """
    Generate business key hash using xxHash128.

    xxHash128 is extremely fast (20 GB/s) and perfect for:
    - Identity resolution (key_hash)
    - Non-cryptographic hashing
    - Deduplication
    - Better collision resistance with 128-bit output

    Args:
        *args: Business key components (e.g., part_no, site, order_id)

    Returns:
        Hexadecimal hash string (32 characters)

    Example:
        ```python
        # Hash single value
        key_hash = hash_business_key("PART123")

        # Hash composite key
        key_hash = hash_business_key("PART123", "SITE01", "ORDER456")

        # Used in SyncFlow for identity resolution
        key_hash = hash_business_key(part_no, site)
        ```

    Note:
        - xxHash is NOT cryptographically secure
        - Use for deduplication, caching, identity resolution only
        - Do NOT use for passwords or security-sensitive data
    """
    # Concatenate all args with separator
    key_string = "|".join(str(arg) for arg in args)

    # Hash with xxHash128
    h = xxhash.xxh128()
    h.update(key_string.encode("utf-8"))

    return h.hexdigest()


def hash_dict(data: dict[str, Any]) -> str:
    """
    Generate cryptographic hash of dictionary using BLAKE3.

    BLAKE3 is:
    - Faster than SHA-256
    - Cryptographically secure
    - Parallelizable

    Perfect for:
    - Change detection (data_hash)
    - Detecting modifications in payload
    - Data integrity verification

    Args:
        data: Dictionary to hash

    Returns:
        Hexadecimal hash string (64 characters)

    Example:
        ```python
        data = {"name": "Widget", "price": 99.99, "qty": 10}
        data_hash = hash_dict(data)

        # Later check if data changed
        current_hash = hash_dict(current_data)
        if current_hash != data_hash:
            print("Data changed!")
        ```

    Note:
        - Dictionary keys are sorted for consistency
        - Same data will always produce same hash
        - Even tiny changes produce completely different hash
    """
    # Convert dict to stable JSON string (sorted keys)
    json_string = json.dumps(data, sort_keys=True, ensure_ascii=False)

    # Hash with BLAKE3
    return blake3.blake3(json_string.encode("utf-8")).hexdigest()


def hash_data(data: str | bytes) -> str:
    """
    Generate cryptographic hash of string or bytes using BLAKE3.

    Args:
        data: String or bytes to hash

    Returns:
        Hexadecimal hash string (64 characters)

    Example:
        ```python
        # Hash string
        text_hash = hash_data("Hello, World!")

        # Hash bytes
        bytes_hash = hash_data(b"Binary data")
        ```
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    return blake3.blake3(data).hexdigest()


def hash_file(file_path: str | Path, chunk_size: int = 8192) -> str:
    """
    Generate cryptographic hash of file using BLAKE3.

    Reads file in chunks for memory efficiency.

    Args:
        file_path: Path to file
        chunk_size: Size of chunks to read (default: 8KB)

    Returns:
        Hexadecimal hash string (64 characters)

    Example:
        ```python
        # Hash file
        file_hash = hash_file("document.pdf")

        # Later verify file integrity
        current_hash = hash_file("document.pdf")
        if current_hash != file_hash:
            print("File was modified!")
        ```

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If no read permission
    """
    hasher = blake3.blake3()

    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()
