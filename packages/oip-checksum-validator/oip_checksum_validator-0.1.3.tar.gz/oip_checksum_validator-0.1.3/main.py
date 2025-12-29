import os
import sys
import time
from blake3 import blake3
from pathlib import Path
import logging

import argparse

from dataclasses import dataclass
import math


@dataclass
class Stats:
    file_count: int = 0
    total_size: int = 0


def represent_size(size_in_bytes: int) -> str:
    """
    Converts a size in bytes to a Kubernetes-compatible PVC size string.

    Args:
        size_in_bytes: The size in bytes.

    Returns:
        A string representing the size in a Kubernetes-compatible format
        (e.g., "1.5Gi", "500Mi").
    """
    if size_in_bytes < 0 or size_in_bytes == 0:
        return "0"

    units = ["KB", "MB", "GB", "TB", "PB"]
    base = 1024
    if size_in_bytes < base:
        return f"{size_in_bytes}B"

    power = int(math.log(size_in_bytes, base))
    power = min(power, len(units))

    unit_index = power - 1
    value = size_in_bytes / (base**power)

    if value.is_integer():
        return f"{int(value)}{units[unit_index]}"
    else:
        return f"{value:.2f}{units[unit_index]}"


def hash_directory(path: Path, stats: Stats, logger: logging.Logger) -> str:
    """Recursively hash a directory tree."""
    try:
        entries = sorted(os.scandir(path), key=lambda e: e.name)
    except OSError as exc:
        logger.error(f"Unable to read directory {path}: {exc}")
        raise

    parts = []
    for entry in entries:
        if entry.name in {".", ".."}:
            continue
        entry_path = entry.path
        try:
            if entry.is_symlink():
                # Record symlink target
                target = Path(os.readlink(entry.path)).as_posix()
                parts.append(f"l:{entry.name}:{target}")
                stats.file_count += 1
            elif entry.is_dir():
                # Recursively hash subdirectory
                parts.append(
                    f"d:{entry.name}:{hash_directory(Path(entry.path), stats, logger)}"
                )
            elif entry.is_file():
                # Hash file content
                logger.info(f"Start hashing: {entry.name}")
                file_hash = (
                    blake3(max_threads=blake3.AUTO).update_mmap(entry_path).hexdigest()
                )
                parts.append(f"f:{entry.name}:{file_hash}")
                stats.file_count += 1
                stats.total_size += entry.stat().st_size
        except PermissionError as exc:
            logger.error(f"Permission denied accessing {entry_path}: {exc}")
            raise
        except OSError as exc:
            logger.error(f"Error accessing {entry_path}: {exc}")
            raise

    parts.sort()
    return blake3("\0".join(parts).encode()).hexdigest()


def validate_path(path: str):
    base_path = Path(path)
    if not base_path.exists():
        print(f"❌ Error: {path} does not exist")
        sys.exit(1)

    if not base_path.is_dir():
        print(f"❌ Error: {base_path} should be a directory")
        sys.exit(1)


class ArgumentParserWithHelp(argparse.ArgumentParser):
    def error(self, message):
        """Override to show help message on error"""
        self.print_help()
        self.exit(2, f"\n{self.prog}: ❌ Error: {message}\n")


def main():
    parser = ArgumentParserWithHelp(
        prog="oic", description="Generate checksum to verify with OICM platform"
    )
    parser.add_argument(
        "path", help="Directory to scan when generating the checksum (recursive)"
    )
    parser.add_argument(
        "-c",
        "--checksum",
        help="The reference checksum to compare with the computed value",
    )
    parser.add_argument(
        "-s",
        "--silent",
        action="store_true",
        help="Run in silent mode",
    )
    args = parser.parse_args()
    validate_path(args.path)

    log_level = logging.WARNING if args.silent else logging.INFO
    logging.basicConfig(level=log_level)
    logger = logging.getLogger("OICM_Checksum")

    stats = Stats()
    start_time = time.perf_counter()

    checksum = hash_directory(args.path, stats, logger)
    end_time = time.perf_counter()
    execution_time = end_time - start_time

    if not args.silent:
        print("=" * 100)
    print("Files:", stats.file_count)
    print("Size:", represent_size(stats.total_size))
    print(f"Time: {execution_time:.4f} seconds")
    print("Checksum:", checksum)
    if args.checksum and args.checksum == checksum:
        print("\n✅ Checksum verified")

    if not args.silent:
        print("=" * 100)


if __name__ == "__main__":
    main()
