"""Persistent hash registry for preventing duplicate auto-commits."""

import json
import shutil
import time
from pathlib import Path
from typing import Dict, Optional

from .file_lock import FileLock
from .logging_config import setup_logger

logger = setup_logger('realign.hash_registry', 'hash_registry.log')


class HashRegistry:
    """
    Persistent storage for turn content hashes to prevent duplicate commits.

    This class manages a JSON file that stores MD5 hashes of committed turn content,
    allowing the system to detect and prevent duplicate commits even after process
    restarts.

    Features:
    - Thread-safe operations using file locking
    - Atomic writes using temp file + rename
    - In-memory caching with TTL for performance
    - Automatic cleanup of stale entries
    - Graceful error handling and recovery
    """

    def __init__(self, realign_dir: Path):
        """
        Initialize the hash registry.

        Args:
            realign_dir: Path to the .aline/{project} directory
        """
        self.realign_dir = realign_dir
        self.metadata_dir = realign_dir / ".metadata"
        self.registry_file = self.metadata_dir / "commit_hashes.json"
        self.lock_file = self.metadata_dir / ".hash_registry.lock"

        # In-memory cache (60s TTL)
        self._cache: Optional[Dict] = None
        self._cache_time: float = 0
        self._cache_ttl: float = 60.0

        logger.debug(f"Initialized HashRegistry for {realign_dir}")

    def get_last_hash(self, session_file: Path) -> Optional[str]:
        """
        Get the last committed hash for a session file.

        Args:
            session_file: Path to the session file

        Returns:
            The MD5 hash of the last committed turn content, or None if not found
        """
        try:
            with self._acquire_lock():
                registry = self._load_registry()
                entry = registry.get("hashes", {}).get(str(session_file))
                if entry:
                    logger.debug(f"Found hash for {session_file.name}: {entry['last_hash'][:8]}...")
                    return entry["last_hash"]
                else:
                    logger.debug(f"No hash found for {session_file.name}")
                    return None
        except TimeoutError:
            logger.warning(f"Hash registry lock timeout for {session_file.name} - skipping duplicate check")
            return None  # Fail-safe: allow commit rather than block
        except Exception as e:
            logger.error(f"Error getting hash for {session_file.name}: {e}", exc_info=True)
            return None

    def set_last_hash(
        self,
        session_file: Path,
        hash_value: str,
        commit_sha: str,
        turn_number: int
    ):
        """
        Store the hash of a newly committed turn.

        Args:
            session_file: Path to the session file
            hash_value: MD5 hash of the turn content
            commit_sha: Git commit SHA
            turn_number: Turn number in the session
        """
        try:
            with self._acquire_lock():
                registry = self._load_registry()

                # Update entry
                registry["hashes"][str(session_file)] = {
                    "last_hash": hash_value,
                    "last_commit_sha": commit_sha,
                    "last_turn_number": turn_number,
                    "last_updated": time.time(),
                    "session_name": session_file.name
                }

                self._save_registry(registry)
                logger.debug(f"Stored hash for {session_file.name}: {hash_value[:8]}... (commit: {commit_sha[:8]})")
        except TimeoutError:
            logger.warning(f"Hash registry lock timeout for {session_file.name} - hash not stored")
        except Exception as e:
            logger.error(f"Error storing hash for {session_file.name}: {e}", exc_info=True)

    def cleanup_stale_entries(self, max_age_days: int = 30) -> int:
        """
        Remove entries for sessions that no longer exist or are very old.

        Args:
            max_age_days: Maximum age of entries to keep (default: 30 days)

        Returns:
            Number of entries removed
        """
        try:
            with self._acquire_lock():
                registry = self._load_registry()
                hashes = registry.get("hashes", {})

                current_time = time.time()
                max_age_seconds = max_age_days * 86400

                cleaned = {}
                for session_path, entry in hashes.items():
                    session_file = Path(session_path)

                    # Keep if session file exists and not too old
                    if session_file.exists():
                        age = current_time - entry.get("last_updated", 0)
                        if age < max_age_seconds:
                            cleaned[session_path] = entry

                registry["hashes"] = cleaned
                registry["metadata"]["last_cleanup"] = current_time
                self._save_registry(registry)

                removed_count = len(hashes) - len(cleaned)
                if removed_count > 0:
                    logger.info(f"Cleaned up {removed_count} stale hash entries")
                return removed_count
        except TimeoutError:
            logger.warning("Hash registry lock timeout during cleanup")
            return 0
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
            return 0

    def _load_registry(self) -> Dict:
        """
        Load registry from disk with caching.

        Returns:
            Registry data dictionary
        """
        # Check cache first (60s TTL)
        if self._cache and (time.time() - self._cache_time) < self._cache_ttl:
            logger.debug("Using cached registry")
            return self._cache.copy()

        # Load from disk
        data = self._load_from_disk()

        # Update cache
        self._cache = data
        self._cache_time = time.time()

        return data.copy()

    def _load_from_disk(self) -> Dict:
        """
        Load registry from disk file.

        Returns:
            Registry data dictionary
        """
        if not self.registry_file.exists():
            logger.debug("Registry file doesn't exist, creating new empty registry")
            return self._new_empty_registry()

        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate schema version
            if data.get("version") != 1:
                logger.warning(f"Unknown registry version: {data.get('version')}, migrating...")
                data = self._migrate_schema(data)

            logger.debug(f"Loaded registry with {len(data.get('hashes', {}))} entries")
            return data

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Corrupted hash registry: {e}")

            # Backup corrupted file
            backup_path = self.registry_file.with_suffix(f'.corrupted.{int(time.time())}')
            try:
                shutil.copy(self.registry_file, backup_path)
                logger.warning(f"Backed up corrupted registry to {backup_path}")
            except Exception as backup_error:
                logger.error(f"Failed to backup corrupted registry: {backup_error}")

            # Return empty registry (fail-safe)
            return self._new_empty_registry()

    def _save_registry(self, data: Dict):
        """
        Save registry to disk using atomic write.

        Args:
            data: Registry data to save
        """
        # Ensure metadata directory exists
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        # Write to temporary file first
        temp_file = self.registry_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            # Atomic rename (overwrites existing file)
            temp_file.replace(self.registry_file)
            logger.debug(f"Saved registry with {len(data.get('hashes', {}))} entries")

            # Invalidate cache
            self._cache = None

        except Exception as e:
            logger.error(f"Error saving registry: {e}", exc_info=True)
            # Clean up temp file if it exists
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            raise

    def _acquire_lock(self) -> FileLock:
        """
        Acquire exclusive lock on registry file.

        Returns:
            FileLock context manager

        Raises:
            TimeoutError: If lock cannot be acquired within timeout
        """
        return FileLock(self.lock_file, timeout=5.0)

    def _new_empty_registry(self) -> Dict:
        """
        Create a new empty registry structure.

        Returns:
            Empty registry dictionary
        """
        return {
            "version": 1,
            "hashes": {},
            "metadata": {
                "created_at": time.time(),
                "last_cleanup": time.time()
            }
        }

    def _migrate_schema(self, data: Dict) -> Dict:
        """
        Migrate registry from old schema to current version.

        Args:
            data: Old registry data

        Returns:
            Migrated registry data
        """
        # Currently only version 1 exists, but this method is ready for future migrations
        logger.warning(f"Schema migration not implemented for version {data.get('version')}, creating new registry")
        return self._new_empty_registry()

    def should_cleanup(self, cleanup_interval_hours: int = 24) -> bool:
        """
        Check if cleanup should be performed based on last cleanup time.

        Args:
            cleanup_interval_hours: Minimum hours between cleanups (default: 24)

        Returns:
            True if cleanup should be performed
        """
        try:
            registry = self._load_registry()
            last_cleanup = registry.get("metadata", {}).get("last_cleanup", 0)
            hours_since_cleanup = (time.time() - last_cleanup) / 3600

            should_run = hours_since_cleanup >= cleanup_interval_hours
            if should_run:
                logger.info(f"Cleanup recommended ({hours_since_cleanup:.1f} hours since last cleanup)")
            return should_run
        except Exception as e:
            logger.error(f"Error checking cleanup status: {e}", exc_info=True)
            return False
