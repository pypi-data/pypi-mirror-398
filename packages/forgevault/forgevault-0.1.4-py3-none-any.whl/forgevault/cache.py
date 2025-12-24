"""
ForgeVault SDK - Caching Layer

Copyright (c) 2025 ForgeVault. All Rights Reserved.
"""

import time
import threading
from typing import Optional, Dict, Any


class PromptCache:
    """
    Thread-safe in-memory cache for prompts.
    Supports TTL-based expiration.
    """

    def __init__(self, ttl: int = 300, max_size: int = 100):
        """
        Initialize the cache.
        
        Args:
            ttl: Time-to-live in seconds (default: 5 minutes)
            max_size: Maximum number of items to cache
        """
        self.ttl = ttl
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _make_key(self, prompt_id: str, version: Optional[str] = None) -> str:
        """Generate cache key"""
        return f"{prompt_id}:{version or 'latest'}"

    def get(self, prompt_id: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get a prompt from cache if not expired.
        
        Returns:
            Cached prompt data or None if not found/expired
        """
        key = self._make_key(prompt_id, version)
        
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if time.time() > entry["expires_at"]:
                del self._cache[key]
                return None
            
            return entry["data"]

    def set(self, prompt_id: str, data: Dict[str, Any], version: Optional[str] = None):
        """
        Store a prompt in cache.
        
        Args:
            prompt_id: The prompt ID
            data: The prompt data to cache
            version: Optional version string
        """
        key = self._make_key(prompt_id, version)
        
        with self._lock:
            # Evict oldest entries if at capacity
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            self._cache[key] = {
                "data": data,
                "expires_at": time.time() + self.ttl,
                "cached_at": time.time()
            }

    def invalidate(self, prompt_id: str, version: Optional[str] = None):
        """Remove a prompt from cache"""
        key = self._make_key(prompt_id, version)
        
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def invalidate_all(self):
        """Clear entire cache"""
        with self._lock:
            self._cache.clear()

    def _evict_oldest(self):
        """Remove the oldest entry from cache"""
        if not self._cache:
            return
        
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["cached_at"])
        del self._cache[oldest_key]

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            valid_count = sum(
                1 for entry in self._cache.values()
                if time.time() <= entry["expires_at"]
            )
            return {
                "total_entries": len(self._cache),
                "valid_entries": valid_count,
                "max_size": self.max_size,
                "ttl": self.ttl
            }


class FallbackStore:
    """
    Persistent fallback storage for prompts.
    Used when API is unreachable.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize fallback store.
        
        Args:
            storage_path: Optional path to store fallback data.
                         If None, uses in-memory only.
        """
        self.storage_path = storage_path
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
        if storage_path:
            self._load_from_disk()

    def save(self, prompt_id: str, data: Dict[str, Any], version: Optional[str] = None):
        """Save prompt to fallback store"""
        key = f"{prompt_id}:{version or 'latest'}"
        
        with self._lock:
            self._store[key] = {
                "data": data,
                "saved_at": time.time()
            }
            
            if self.storage_path:
                self._save_to_disk()

    def get(self, prompt_id: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get prompt from fallback store"""
        key = f"{prompt_id}:{version or 'latest'}"
        
        with self._lock:
            entry = self._store.get(key)
            return entry["data"] if entry else None

    def _load_from_disk(self):
        """Load fallback data from disk"""
        import json
        import os
        
        if not os.path.exists(self.storage_path):
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                self._store = json.load(f)
        except (json.JSONDecodeError, IOError):
            self._store = {}

    def _save_to_disk(self):
        """Save fallback data to disk"""
        import json
        import os
        
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(self._store, f)
        except IOError:
            pass  # Fail silently for fallback

