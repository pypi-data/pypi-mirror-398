# OI Checksum Validator

OICM checksum generator for data verification.

## Installation

```bash
pip install oip-checksum-validator
```

## Usage

Generate a checksum:
```bash
oic /path/to/directory

# OR invoke oip-checksum-validator via uvx, no permanent install needed
uvx --from oip-checksum-validator oic /path/to/directory
```

Verify against a reference checksum:
```bash
oic /path/to/directory -c <expected_checksum>

# OR invoke oip-checksum-validator via uvx, no permanent install needed
uvx --from oip-checksum-validator oic /path/to/directory -c <expected_checksum>
```

Run silently:

```bash
oic /path/to/directory -s

# OR invoke oip-checksum-validator via uvx, no permanent install needed
uvx --from oip-checksum-validator oic /path/to/directory -s
```

## How it works

The tool creates a deterministic hash by:
1. Sorting directory entries alphabetically
2. Recursively processing subdirectories
3. Hashing file contents with BLAKE3
4. Recording symlink targets
5. Combining all hashes into a final checksum

## Requirements

- `Python>=3.12`
- `blake3`
