"""
Material Text Cache Module

Provides caching for large PDF extracted text to improve access performance.
Uses in-memory LRU cache with optional disk persistence.
"""

import os
import hashlib
import json
import pickle
from functools import lru_cache
from typing import Optional, Dict
from pathlib import Path
import time

# Cache configuration
CACHE_DIR = Path(__file__).parent / ".material_cache"
CACHE_DIR.mkdir(exist_ok=True)
MAX_CACHE_SIZE_MB = 500  # Maximum cache size in MB
CACHE_EXPIRY_HOURS = 24 * 7  # Cache expires after 7 days

# In-memory cache with size limit
# Using a dictionary-based LRU cache
_cache: Dict[int, tuple] = {}  # material_id -> (text, timestamp, size_bytes)
_cache_access_order: list = []  # Track access order for LRU eviction
_total_cache_size = 0  # Total size in bytes


def _get_cache_file_path(material_id: int) -> Path:
    """Get the disk cache file path for a material"""
    return CACHE_DIR / f"material_{material_id}.cache"


def _get_cache_metadata_path() -> Path:
    """Get the cache metadata file path"""
    return CACHE_DIR / "cache_metadata.json"


def _get_text_size(text: str) -> int:
    """Calculate the size of text in bytes"""
    return len(text.encode('utf-8'))


def _load_cache_metadata() -> Dict:
    """Load cache metadata from disk"""
    metadata_path = _get_cache_metadata_path()
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache metadata: {e}")
    return {}


def _save_cache_metadata(metadata: Dict):
    """Save cache metadata to disk"""
    metadata_path = _get_cache_metadata_path()
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
    except Exception as e:
        print(f"Error saving cache metadata: {e}")


def _is_cache_expired(timestamp: float) -> bool:
    """Check if cache entry is expired"""
    return time.time() - timestamp > (CACHE_EXPIRY_HOURS * 3600)


def _evict_lru_if_needed(new_size: int):
    """Evict least recently used entries if cache is too large"""
    global _total_cache_size, _cache, _cache_access_order
    
    max_size_bytes = MAX_CACHE_SIZE_MB * 1024 * 1024
    
    # Remove expired entries first
    expired_ids = []
    for material_id in list(_cache.keys()):
        text, timestamp, size = _cache[material_id]
        if _is_cache_expired(timestamp):
            expired_ids.append(material_id)
    
    for material_id in expired_ids:
        _remove_from_cache(material_id)
    
    # If still too large, evict LRU entries
    while _total_cache_size + new_size > max_size_bytes and _cache_access_order:
        lru_id = _cache_access_order.pop(0)
        if lru_id in _cache:
            _remove_from_cache(lru_id)


def _remove_from_cache(material_id: int):
    """Remove an entry from the cache"""
    global _total_cache_size, _cache, _cache_access_order
    
    if material_id in _cache:
        _, _, size = _cache[material_id]
        _total_cache_size -= size
        del _cache[material_id]
        if material_id in _cache_access_order:
            _cache_access_order.remove(material_id)


def get_cached_text(material_id: int) -> Optional[str]:
    """
    Get cached extracted text for a material.
    Returns None if not cached or expired.
    """
    global _cache, _cache_access_order
    
    # Check in-memory cache first
    if material_id in _cache:
        text, timestamp, size = _cache[material_id]
        
        # Check if expired
        if _is_cache_expired(timestamp):
            _remove_from_cache(material_id)
            # Also remove from disk
            cache_file = _get_cache_file_path(material_id)
            if cache_file.exists():
                cache_file.unlink()
            return None
        
        # Update access order (move to end)
        if material_id in _cache_access_order:
            _cache_access_order.remove(material_id)
        _cache_access_order.append(material_id)
        
        return text
    
    # Check disk cache
    cache_file = _get_cache_file_path(material_id)
    if cache_file.exists():
        try:
            # Load metadata to check timestamp
            metadata = _load_cache_metadata()
            cache_info = metadata.get(str(material_id), {})
            timestamp = cache_info.get('timestamp', 0)
            
            if _is_cache_expired(timestamp):
                cache_file.unlink()
                if str(material_id) in metadata:
                    del metadata[str(material_id)]
                    _save_cache_metadata(metadata)
                return None
            
            # Load from disk
            with open(cache_file, 'rb') as f:
                text = pickle.load(f)
            
            # Add to in-memory cache
            text_size = _get_text_size(text)
            _evict_lru_if_needed(text_size)
            _cache[material_id] = (text, timestamp, text_size)
            _total_cache_size += text_size
            _cache_access_order.append(material_id)
            
            return text
        except Exception as e:
            print(f"Error loading cache from disk for material {material_id}: {e}")
            # Remove corrupted cache file
            if cache_file.exists():
                cache_file.unlink()
    
    return None


def cache_text(material_id: int, text: str):
    """
    Cache extracted text for a material.
    Saves to both in-memory and disk cache.
    """
    global _cache, _cache_access_order, _total_cache_size
    
    if not text:
        return
    
    text_size = _get_text_size(text)
    timestamp = time.time()
    
    # Evict if needed before adding
    _evict_lru_if_needed(text_size)
    
    # Remove old entry if exists
    if material_id in _cache:
        _remove_from_cache(material_id)
    
    # Add to in-memory cache
    _cache[material_id] = (text, timestamp, text_size)
    _total_cache_size += text_size
    if material_id in _cache_access_order:
        _cache_access_order.remove(material_id)
    _cache_access_order.append(material_id)
    
    # Save to disk cache
    cache_file = _get_cache_file_path(material_id)
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(text, f)
        
        # Update metadata
        metadata = _load_cache_metadata()
        metadata[str(material_id)] = {
            'timestamp': timestamp,
            'size_bytes': text_size,
            'title': f"Material {material_id}"  # Can be updated with actual title
        }
        _save_cache_metadata(metadata)
    except Exception as e:
        print(f"Error saving cache to disk for material {material_id}: {e}")


def invalidate_cache(material_id: int):
    """
    Invalidate cache for a specific material.
    Removes from both in-memory and disk cache.
    """
    _remove_from_cache(material_id)
    
    # Remove from disk
    cache_file = _get_cache_file_path(material_id)
    if cache_file.exists():
        cache_file.unlink()
    
    # Update metadata
    metadata = _load_cache_metadata()
    if str(material_id) in metadata:
        del metadata[str(material_id)]
        _save_cache_metadata(metadata)


def clear_all_cache():
    """Clear all cached materials"""
    global _cache, _cache_access_order, _total_cache_size
    
    _cache.clear()
    _cache_access_order.clear()
    _total_cache_size = 0
    
    # Clear disk cache
    if CACHE_DIR.exists():
        for cache_file in CACHE_DIR.glob("material_*.cache"):
            cache_file.unlink()
    
    # Clear metadata
    metadata_path = _get_cache_metadata_path()
    if metadata_path.exists():
        metadata_path.unlink()


def get_cache_stats() -> Dict:
    """Get cache statistics"""
    global _cache, _total_cache_size
    
    metadata = _load_cache_metadata()
    disk_cache_count = len([f for f in CACHE_DIR.glob("material_*.cache")])
    
    return {
        'in_memory_entries': len(_cache),
        'total_size_mb': round(_total_cache_size / (1024 * 1024), 2),
        'disk_cache_entries': disk_cache_count,
        'max_size_mb': MAX_CACHE_SIZE_MB,
        'cache_dir': str(CACHE_DIR)
    }


def preload_system_materials(db_session, system_user_id: str = "SYSTEM"):
    """
    Preload system materials extracted text into cache.
    Useful for warming up the cache on server startup.
    """
    from database import Material

    try:
        system_materials = db_session.query(Material).filter(
            Material.user_id == system_user_id,
            Material.status == "processed",
            Material.extracted_text.isnot(None)
        ).all()

        loaded_count = 0
        for material in system_materials:
            if material.extracted_text:
                cache_text(material.id, material.extracted_text)
                loaded_count += 1

        print(f"Preloaded {loaded_count} system materials text into cache")
        return loaded_count
    except Exception as e:
        print(f"Error preloading system materials: {e}")
        return 0


