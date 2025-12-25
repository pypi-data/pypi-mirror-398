#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 01-Nov-2025

Metrics exporters for cache monitoring.
Performance Priority #4 - Observability and monitoring integration.
"""

from typing import Any, Optional
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.caching.metrics_exporter")


class PrometheusExporter:
    """
    Export cache metrics in Prometheus format.
    
    Provides cache statistics in Prometheus-compatible format for monitoring.
    
    Example:
        from exonware.xwsystem.caching import LRUCache, PrometheusExporter
        
        cache = LRUCache(capacity=1000, name="user_cache")
        exporter = PrometheusExporter(cache)
        
        # Get metrics in Prometheus format
        metrics = exporter.export_metrics()
        print(metrics)
        
        # Expose via HTTP endpoint (with Flask/FastAPI)
        @app.get("/metrics")
        def metrics_endpoint():
            return Response(exporter.export_metrics(), media_type="text/plain")
    """
    
    def __init__(self, cache: Any, metric_prefix: str = "xwcache"):
        """
        Initialize Prometheus exporter.
        
        Args:
            cache: Cache instance to export metrics from
            metric_prefix: Prefix for metric names
        """
        self.cache = cache
        self.metric_prefix = metric_prefix
    
    def export_metrics(self) -> str:
        """
        Export metrics in Prometheus format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        stats = self.cache.get_stats()
        cache_name = stats.get('name', 'unknown')
        cache_type = stats.get('type', 'unknown')
        
        lines = []
        
        # HELP and TYPE declarations
        lines.append(f"# HELP {self.metric_prefix}_size Current number of entries in cache")
        lines.append(f"# TYPE {self.metric_prefix}_size gauge")
        lines.append(f'{self.metric_prefix}_size{{cache="{cache_name}",type="{cache_type}"}} {stats.get("size", 0)}')
        
        lines.append(f"# HELP {self.metric_prefix}_capacity Maximum cache capacity")
        lines.append(f"# TYPE {self.metric_prefix}_capacity gauge")
        lines.append(f'{self.metric_prefix}_capacity{{cache="{cache_name}",type="{cache_type}"}} {stats.get("capacity", 0)}')
        
        lines.append(f"# HELP {self.metric_prefix}_hits_total Total cache hits")
        lines.append(f"# TYPE {self.metric_prefix}_hits_total counter")
        lines.append(f'{self.metric_prefix}_hits_total{{cache="{cache_name}",type="{cache_type}"}} {stats.get("hits", 0)}')
        
        lines.append(f"# HELP {self.metric_prefix}_misses_total Total cache misses")
        lines.append(f"# TYPE {self.metric_prefix}_misses_total counter")
        lines.append(f'{self.metric_prefix}_misses_total{{cache="{cache_name}",type="{cache_type}"}} {stats.get("misses", 0)}')
        
        lines.append(f"# HELP {self.metric_prefix}_evictions_total Total cache evictions")
        lines.append(f"# TYPE {self.metric_prefix}_evictions_total counter")
        lines.append(f'{self.metric_prefix}_evictions_total{{cache="{cache_name}",type="{cache_type}"}} {stats.get("evictions", 0)}')
        
        lines.append(f"# HELP {self.metric_prefix}_hit_rate Cache hit rate (0.0 to 1.0)")
        lines.append(f"# TYPE {self.metric_prefix}_hit_rate gauge")
        lines.append(f'{self.metric_prefix}_hit_rate{{cache="{cache_name}",type="{cache_type}"}} {stats.get("hit_rate", 0.0)}')
        
        # Additional metrics based on cache type
        if 'memory_used_mb' in stats:
            lines.append(f"# HELP {self.metric_prefix}_memory_mb Memory used in megabytes")
            lines.append(f"# TYPE {self.metric_prefix}_memory_mb gauge")
            lines.append(f'{self.metric_prefix}_memory_mb{{cache="{cache_name}",type="{cache_type}"}} {stats["memory_used_mb"]}')
        
        return '\n'.join(lines) + '\n'
    
    def export_dict(self) -> dict[str, Any]:
        """
        Export metrics as dictionary.
        
        Returns:
            Dictionary of metrics
        """
        stats = self.cache.get_stats()
        
        return {
            'cache_name': stats.get('name', 'unknown'),
            'cache_type': stats.get('type', 'unknown'),
            'size': stats.get('size', 0),
            'capacity': stats.get('capacity', 0),
            'hits': stats.get('hits', 0),
            'misses': stats.get('misses', 0),
            'evictions': stats.get('evictions', 0),
            'hit_rate': stats.get('hit_rate', 0.0),
            'stats': stats
        }


class StatsCollector:
    """
    Collect statistics from multiple caches.
    
    Example:
        collector = StatsCollector()
        collector.register('users', user_cache)
        collector.register('products', product_cache)
        
        # Get all stats
        all_stats = collector.collect_all()
        
        # Export for monitoring
        metrics = collector.export_prometheus()
    """
    
    def __init__(self):
        """Initialize stats collector."""
        self._caches: dict[str, Any] = {}
    
    def register(self, name: str, cache: Any) -> None:
        """
        Register cache for monitoring.
        
        Args:
            name: Unique name for this cache
            cache: Cache instance
        """
        self._caches[name] = cache
        logger.info(f"Registered cache '{name}' for monitoring")
    
    def unregister(self, name: str) -> None:
        """
        Unregister cache.
        
        Args:
            name: Name of cache to unregister
        """
        if name in self._caches:
            del self._caches[name]
    
    def collect_all(self) -> dict[str, dict[str, Any]]:
        """
        Collect stats from all registered caches.
        
        Returns:
            Dictionary of cache stats
        """
        all_stats = {}
        for name, cache in self._caches.items():
            try:
                all_stats[name] = cache.get_stats()
            except Exception as e:
                logger.error(f"Failed to get stats from {name}: {e}")
        
        return all_stats
    
    def export_prometheus(self) -> str:
        """
        Export all cache metrics in Prometheus format.
        
        Returns:
            Prometheus-formatted metrics
        """
        metrics_lines = []
        
        for name, cache in self._caches.items():
            exporter = PrometheusExporter(cache, metric_prefix=f"xwcache_{name}")
            metrics_lines.append(exporter.export_metrics())
        
        return '\n'.join(metrics_lines)


__all__ = [
    'PrometheusExporter',
    'StatsCollector',
]

