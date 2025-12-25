# mehdashti-hashing

Fast hashing utilities for business keys (xxHash128) and data integrity (BLAKE3).

## Features

- ✅ **xxHash128**: Ultra-fast non-cryptographic hashing (20 GB/s)
- ✅ **BLAKE3**: Fast cryptographic hashing
- ✅ Business key hashing for identity resolution
- ✅ Data change detection
- ✅ File integrity verification
- ✅ Dictionary hashing with stable ordering

## Installation

```bash
pip install mehdashti-hashing
# or
uv add mehdashti-hashing
```

## Quick Start

### Business Key Hashing (xxHash128)

Use for identity resolution, deduplication, and caching keys:

```python
from mehdashti_hashing import hash_business_key

# Single value
part_hash = hash_business_key("PART-12345")

# Composite key
order_hash = hash_business_key("ORDER-001", "SITE-A", "2025-01-01")

# Use as dictionary key or database index
cache_key = hash_business_key(user_id, resource_type, action)
```

**⚠️ Note**: xxHash is NOT cryptographically secure. Do not use for passwords!

### Data Hashing (BLAKE3)

Use for change detection and data integrity:

```python
from mehdashti_hashing import hash_dict, hash_data

# Hash dictionary (for change detection)
record = {"name": "Widget", "price": 99.99, "qty": 10}
record_hash = hash_dict(record)

# Later, check if data changed
current_hash = hash_dict(current_record)
if current_hash != record_hash:
    print("Data was modified!")

# Hash string or bytes
text_hash = hash_data("Important message")
binary_hash = hash_data(b"\x00\x01\x02")
```

### File Hashing

```python
from mehdashti_hashing import hash_file

# Calculate file hash
file_hash = hash_file("document.pdf")

# Verify file integrity later
current_hash = hash_file("document.pdf")
if current_hash != file_hash:
    print("File was corrupted or modified!")
```

## Use Cases

### 1. Identity Resolution (SyncFlow Pattern)

```python
from mehdashti_hashing import hash_business_key, hash_dict

# Create stable identity hash
part_no = "PART-123"
site = "WAREHOUSE-A"
key_hash = hash_business_key(part_no, site)

# Create data hash for change detection
data = {"name": "Widget", "price": 99.99, "stock": 100}
data_hash = hash_dict(data)

# Store in database
await db.execute(
    """
    INSERT INTO items (key_hash, data_hash, part_no, site, data)
    VALUES ($1, $2, $3, $4, $5)
    ON CONFLICT (key_hash)
    DO UPDATE SET
        data = EXCLUDED.data,
        data_hash = EXCLUDED.data_hash
    WHERE items.data_hash != EXCLUDED.data_hash
    """,
    key_hash, data_hash, part_no, site, data
)
```

### 2. Cache Keys

```python
from mehdashti_hashing import hash_business_key

def get_user_cache_key(user_id: str, resource: str) -> str:
    return f"cache:{hash_business_key(user_id, resource)}"

# Use with Redis
cache_key = get_user_cache_key("user-123", "profile")
await redis.set(cache_key, json.dumps(user_profile), ex=3600)
```

### 3. Deduplication

```python
from mehdashti_hashing import hash_dict

seen_hashes = set()

for record in incoming_records:
    record_hash = hash_dict(record)

    if record_hash in seen_hashes:
        print(f"Duplicate found: {record}")
        continue

    seen_hashes.add(record_hash)
    process_record(record)
```

## API Reference

### `hash_business_key(*args) -> str`

Generate xxHash128 hash of business key components.

- **Args**: Variable number of arguments to hash
- **Returns**: 32-character hex string
- **Use for**: Identity resolution, deduplication, caching
- **⚠️ NOT cryptographically secure**

### `hash_dict(data: dict) -> str`

Generate BLAKE3 hash of dictionary.

- **Args**: Dictionary to hash
- **Returns**: 64-character hex string
- **Use for**: Change detection, data integrity
- **Note**: Keys are sorted for consistency

### `hash_data(data: str | bytes) -> str`

Generate BLAKE3 hash of string or bytes.

- **Args**: String or bytes to hash
- **Returns**: 64-character hex string
- **Use for**: General-purpose hashing

### `hash_file(file_path: str | Path, chunk_size: int = 8192) -> str`

Generate BLAKE3 hash of file.

- **Args**:
  - `file_path`: Path to file
  - `chunk_size`: Read chunk size (default 8KB)
- **Returns**: 64-character hex string
- **Use for**: File integrity verification

## Performance

### xxHash128

- **Speed**: ~20 GB/s (depends on hardware)
- **Collision Resistance**: 2^128 (extremely low probability)
- **Best for**: High-throughput applications, caching, deduplication

### BLAKE3

- **Speed**: ~10 GB/s (faster than SHA-256)
- **Security**: Cryptographically secure
- **Best for**: Change detection, data integrity, secure hashing

## Comparison

| Use Case | Algorithm | Function | Cryptographically Secure |
|----------|-----------|----------|--------------------------|
| Business keys | xxHash128 | `hash_business_key()` | ❌ No |
| Cache keys | xxHash128 | `hash_business_key()` | ❌ No |
| Data change detection | BLAKE3 | `hash_dict()` | ✅ Yes |
| File integrity | BLAKE3 | `hash_file()` | ✅ Yes |
| General hashing | BLAKE3 | `hash_data()` | ✅ Yes |

## Requirements

- Python 3.13+
- xxhash 3.5+
- blake3 0.4+

## License

MIT License

## Author

Mahdi Ashti <mahdi@mehdashti.com>

## Links

- **Repository**: https://github.com/mehdashti/smart-platform
- **Issues**: https://github.com/mehdashti/smart-platform/issues
