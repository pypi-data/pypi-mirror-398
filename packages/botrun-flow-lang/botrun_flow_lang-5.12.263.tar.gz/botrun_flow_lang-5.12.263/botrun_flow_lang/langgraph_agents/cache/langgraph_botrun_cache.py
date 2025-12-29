"""
Botrun ID-based cache for LangGraph React Agent graphs.
Provides session isolation with parameter validation for graph caching.
"""

import hashlib
import json
import time
from typing import Dict, Any, Optional
from botrun_flow_lang.utils.botrun_logger import get_default_botrun_logger

logger = get_default_botrun_logger()


class LangGraphBotrunCache:
    """
    Botrun ID-based cache for LangGraph React Agent graphs.

    Cache structure:
    {
        "botrun_id_1": {
            "graph": <graph_instance>,
            "params_hash": "abc123...",
            "created_at": <timestamp>
        },
        "botrun_id_2": {
            "graph": <graph_instance>,
            "params_hash": "def456...",
            "created_at": <timestamp>
        }
    }
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_params_hash(
        self,
        system_prompt: str,
        botrun_flow_lang_url: str,
        user_id: str,
        model_name: str,
        lang: str,
        mcp_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate MD5 hash from parameters for cache validation.

        Args:
            system_prompt: The system prompt to use for the agent
            botrun_flow_lang_url: URL for botrun flow lang
            user_id: User ID
            model_name: Model name to use
            lang: Language code (e.g., "en", "zh-TW")
            mcp_config: MCP servers configuration dict

        Returns:
            str: MD5 hash of parameters
        """
        # Create a stable representation of all parameters
        cache_data = {
            "system_prompt": system_prompt,
            "botrun_flow_lang_url": botrun_flow_lang_url,
            "user_id": user_id,
            "model_name": model_name,
            "lang": lang,
            "mcp_config": mcp_config or {},
        }

        # Convert to JSON string for consistent hashing
        cache_str = json.dumps(cache_data, sort_keys=True)

        # Generate MD5 hash
        return hashlib.md5(cache_str.encode("utf-8")).hexdigest()

    def get_cached_graph(self, botrun_id: str, params_hash: str) -> Optional[Any]:
        """
        Get cached graph if botrun_id exists and params_hash matches.

        Args:
            botrun_id: The botrun ID to look up
            params_hash: Expected parameter hash for validation

        Returns:
            Cached graph instance if found and valid, None otherwise
        """
        if botrun_id not in self._cache:
            logger.debug(f"Botrun ID {botrun_id} not found in cache")
            return None

        cache_entry = self._cache[botrun_id]
        cached_hash = cache_entry.get("params_hash")

        if cached_hash != params_hash:
            logger.info(
                f"Parameter hash mismatch for botrun_id {botrun_id}. "
                f"Cached: {cached_hash[:8]}..., Current: {params_hash[:8]}... "
                f"Cache will be invalidated."
            )
            # Clear cache for this botrun_id since parameters changed
            self.clear_botrun_cache(botrun_id)
            return None

        logger.info(f"Cache hit for botrun_id {botrun_id}")
        return cache_entry.get("graph")

    def cache_graph(self, botrun_id: str, params_hash: str, graph: Any):
        """
        Cache graph for specific botrun_id with parameter hash.

        Args:
            botrun_id: The botrun ID to cache for
            params_hash: Parameter hash for validation
            graph: Graph instance to cache
        """
        self._cache[botrun_id] = {
            "graph": graph,
            "params_hash": params_hash,
            "created_at": time.time(),
        }
        logger.info(
            f"Graph cached for botrun_id {botrun_id} with hash {params_hash[:8]}..."
        )

    def clear_botrun_cache(self, botrun_id: str):
        """
        Clear cache for specific botrun_id.

        Args:
            botrun_id: The botrun ID to clear cache for
        """
        if botrun_id in self._cache:
            del self._cache[botrun_id]
            logger.info(f"Cache cleared for botrun_id {botrun_id}")

    def cleanup_old_cache(self, max_age_hours: int = 24):
        """
        Remove old cache entries to prevent memory buildup.

        Args:
            max_age_hours: Maximum age in hours before cache entry is removed
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        botrun_ids_to_remove = []

        for botrun_id, cache_entry in self._cache.items():
            created_at = cache_entry.get("created_at", 0)
            if current_time - created_at > max_age_seconds:
                botrun_ids_to_remove.append(botrun_id)

        for botrun_id in botrun_ids_to_remove:
            del self._cache[botrun_id]
            logger.info(f"Removed old cache entry for botrun_id {botrun_id}")

        if botrun_ids_to_remove:
            logger.info(f"Cleaned up {len(botrun_ids_to_remove)} old cache entries")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.

        Returns:
            Dict with cache statistics
        """
        current_time = time.time()
        total_entries = len(self._cache)

        if total_entries == 0:
            return {
                "total_entries": 0,
                "oldest_entry_age_hours": 0,
                "newest_entry_age_hours": 0,
                "average_age_hours": 0,
            }

        ages = []
        for cache_entry in self._cache.values():
            created_at = cache_entry.get("created_at", current_time)
            age_hours = (current_time - created_at) / 3600
            ages.append(age_hours)

        return {
            "total_entries": total_entries,
            "oldest_entry_age_hours": max(ages),
            "newest_entry_age_hours": min(ages),
            "average_age_hours": sum(ages) / len(ages),
        }


# Global cache instance
_global_cache = LangGraphBotrunCache()


def get_botrun_cache() -> LangGraphBotrunCache:
    """Get the global botrun cache instance."""
    return _global_cache
