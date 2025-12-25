#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Cache serialization utilities.
Usability Priority #2 - Persist and restore cache state.
"""

import pickle
import json
from pathlib import Path
from typing import Any, Union
from .lru_cache import LRUCache
from .lfu_optimized import OptimizedLFUCache
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.caching.serializable")


class SerializableCache(LRUCache):
    """
    LRU Cache with serialization support.
    
    Allows saving cache state to disk and loading it back.
    
    Example:
        cache = SerializableCache(capacity=1000)
        cache.put('key1', 'value1')
        cache.put('key2', 'value2')
        
        # Save to disk
        cache.save_to_file('cache_backup.pkl')
        
        # Later... load from disk
        cache2 = SerializableCache.load_from_file('cache_backup.pkl')
        assert cache2.get('key1') == 'value1'
    """
    
    def save_to_file(self, file_path: Union[str, Path], format: str = 'pickle') -> bool:
        """
        Save cache to file.
        
        Args:
            file_path: Path to save cache
            format: Serialization format ('pickle' or 'json')
            
        Returns:
            True if saved successfully
        """
        try:
            file_path = Path(file_path)
            
            # Collect cache data
            cache_data = {
                'capacity': self.capacity,
                'ttl': self.ttl,
                'name': self.name,
                'items': dict(self.items()),
                'stats': self.get_stats()
            }
            
            if format == 'pickle':
                with open(file_path, 'wb') as f:
                    pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            elif format == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}. Use 'pickle' or 'json'")
            
            logger.info(f"Cache saved to {file_path} ({format} format)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cache to {file_path}: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, file_path: Union[str, Path], format: str = 'pickle') -> 'SerializableCache':
        """
        Load cache from file.
        
        Args:
            file_path: Path to load cache from
            format: Serialization format ('pickle' or 'json')
            
        Returns:
            Loaded cache instance
        """
        try:
            file_path = Path(file_path)
            
            if format == 'pickle':
                with open(file_path, 'rb') as f:
                    cache_data = pickle.load(f)
            elif format == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Create cache instance
            cache = cls(
                capacity=cache_data.get('capacity', 128),
                ttl=cache_data.get('ttl'),
                name=cache_data.get('name')
            )
            
            # Restore items
            for key, value in cache_data.get('items', {}).items():
                cache.put(key, value)
            
            logger.info(f"Cache loaded from {file_path} with {cache.size()} entries")
            return cache
            
        except Exception as e:
            logger.error(f"Failed to load cache from {file_path}: {e}")
            raise
    
    def backup(self, backup_path: Union[str, Path]) -> bool:
        """
        Create backup of cache.
        
        Args:
            backup_path: Path for backup file
            
        Returns:
            True if backed up successfully
        """
        return self.save_to_file(backup_path, format='pickle')
    
    def restore(self, backup_path: Union[str, Path]) -> bool:
        """
        Restore cache from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if restored successfully
        """
        try:
            loaded_cache = self.load_from_file(backup_path, format='pickle')
            
            # Clear current cache
            self.clear()
            
            # Restore items
            for key, value in loaded_cache.items():
                self.put(key, value)
            
            logger.info(f"Cache restored from {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore from {backup_path}: {e}")
            return False


__all__ = [
    'SerializableCache',
]

