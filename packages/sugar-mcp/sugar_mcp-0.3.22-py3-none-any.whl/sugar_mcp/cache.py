import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

from netmind_sugar.chains import get_chain, LiquidityPool


@dataclass
class CacheConfig:
    """Configuration for the liquidity pools cache."""
    duration_minutes: int = 10
    enabled_chain_ids: Optional[List[str]] = None
    filter_invalid_pools: bool = True

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.duration_minutes <= 0:
            raise ValueError("Cache duration must be positive")
        if self.enabled_chain_ids is not None and len(self.enabled_chain_ids) == 0:
            raise ValueError("enabled_chain_ids cannot be an empty list")


class PoolsCache:
    """Thread-safe cache for liquidity pools data with automatic background updates."""

    def __init__(self, cache_duration_minutes: int = 10, enabled_chain_ids: Optional[List[str]] = None, filter_invalid_pools: bool = True, config: Optional[CacheConfig] = None):
        # Use config if provided, otherwise use individual parameters
        if config is not None:
            cache_duration_minutes = config.duration_minutes
            enabled_chain_ids = config.enabled_chain_ids
            filter_invalid_pools = config.filter_invalid_pools

        self.cache: Dict[str, Dict] = {}
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        # If None, cache all chains. If list provided, only cache specified chains
        self.enabled_chain_ids = enabled_chain_ids
        self.lock = threading.Lock()

        # Background update thread
        self.update_thread: Optional[threading.Thread] = None
        self.update_thread_lock = threading.Lock()
        self.update_running = False

        # Track ongoing fetch operations to prevent cache storms
        self.fetch_locks: Dict[str, threading.Lock] = {}
        self.fetch_lock_lock = threading.Lock()

        # Pool filtering configuration
        self.filter_invalid_pools = filter_invalid_pools

    def get_pools(self, chain_id: str) -> List[LiquidityPool]:
        """Get cached pools for a chain, updating cache if necessary.

        Args:
            chain_id (str): The chain ID

        Returns:
            List[LiquidityPool]: The cached pools data
        """
        # If enabled_chain_ids is set and chain_id is not in the list, fetch directly without caching
        if self.enabled_chain_ids is not None and chain_id not in self.enabled_chain_ids:
            try:
                with get_chain(chain_id) as chain:
                    result = chain.get_pools()
                    if not isinstance(result, list):
                        print(f"Warning: chain.get_pools() returned {type(result)} instead of list for chain {chain_id}")
                        return []
                    return result
            except Exception as e:
                print(f"Failed to get pools from chain {chain_id}: {type(e).__name__}: {str(e)}")
                return []

        # Use double-checked locking with per-chain fetch locks to prevent cache storms
        with self.lock:
            now = datetime.now()

            # Check if we have valid cached data
            if chain_id in self.cache:
                cache_entry = self.cache[chain_id]
                if now - cache_entry["last_updated"] < self.cache_duration:
                    return cache_entry["pools"]

        # Cache is stale or doesn't exist, need to fetch new data
        # Use per-chain lock to prevent multiple concurrent fetches for the same chain
        with self._get_fetch_lock(chain_id):
            # Double-check: another thread might have updated the cache while we waited
            with self.lock:
                if chain_id in self.cache:
                    cache_entry = self.cache[chain_id]
                    now = datetime.now()
                    if now - cache_entry["last_updated"] < self.cache_duration:
                        return cache_entry["pools"]

            # Still need to fetch, do it now
            return self._fetch_and_cache_pools(chain_id, datetime.now())

    def _get_fetch_lock(self, chain_id: str) -> threading.Lock:
        """Get or create a fetch lock for the specified chain."""
        with self.fetch_lock_lock:
            if chain_id not in self.fetch_locks:
                self.fetch_locks[chain_id] = threading.Lock()
            return self.fetch_locks[chain_id]

    def _is_pool_valid(self, pool) -> bool:
        """Check if a pool has required data: reserves with valid prices, amounts, and emissions."""
        if not pool:
            return False

        try:
            # Check reserve0 - must exist and have valid price and amount_in_stable
            if not hasattr(pool, 'reserve0') or pool.reserve0 is None:
                return False
            if not hasattr(pool.reserve0, 'price') or pool.reserve0.price is None:
                return False
            if not hasattr(pool.reserve0.price, 'price') or pool.reserve0.price.price is None:
                return False
            if not isinstance(pool.reserve0.price.price, (int, float)) or pool.reserve0.price.price <= 0:
                return False
            if not hasattr(pool.reserve0, 'amount_in_stable') or pool.reserve0.amount_in_stable is None:
                return False
            if not isinstance(pool.reserve0.amount_in_stable, (int, float)) or pool.reserve0.amount_in_stable <= 0:
                return False

            # Check reserve1 - must exist and have valid price and amount_in_stable
            if not hasattr(pool, 'reserve1') or pool.reserve1 is None:
                return False
            if not hasattr(pool.reserve1, 'price') or pool.reserve1.price is None:
                return False
            if not hasattr(pool.reserve1.price, 'price') or pool.reserve1.price.price is None:
                return False
            if not isinstance(pool.reserve1.price.price, (int, float)) or pool.reserve1.price.price <= 0:
                return False
            if not hasattr(pool.reserve1, 'amount_in_stable') or pool.reserve1.amount_in_stable is None:
                return False
            if not isinstance(pool.reserve1.amount_in_stable, (int, float)) or pool.reserve1.amount_in_stable <= 0:
                return False

            # Check emissions - must exist and be valid
            if not hasattr(pool, 'emissions') or pool.emissions is None:
                return False

            return True

        except Exception as e:
            # If any error occurs during validation, consider pool invalid
            return False

    def _filter_invalid_pools(self, pools: List) -> List:
        """Filter out pools with missing or invalid critical data."""
        if not self.filter_invalid_pools:
            return pools

        valid_pools = []
        invalid_count = 0

        for pool in pools:
            if self._is_pool_valid(pool):
                valid_pools.append(pool)
            else:
                invalid_count += 1

        if invalid_count > 0:
            print(f"Filtered out {invalid_count} invalid pools, kept {len(valid_pools)} valid pools")

        return valid_pools

    def get_pool_by_address(self, chain_id: str, address: str) -> Optional[LiquidityPool]:
        """Get a specific pool by address from cache.

        Args:
            chain_id (str): The chain ID
            address (str): Pool contract address

        Returns:
            Optional[LiquidityPool]: The pool if found, None otherwise
        """
        pools = self.get_pools(chain_id)
        address_lower = address.lower()

        for pool in pools:
            if pool.lp.lower() == address_lower:
                return pool

        return None

    def _fetch_and_cache_pools(self, chain_id: str, timestamp: datetime) -> List[LiquidityPool]:
        """Fetch pools from chain and update cache."""
        try:
            with get_chain(chain_id) as chain:
                pools = chain.get_pools()

            # Validate the result
            if not isinstance(pools, list):
                print(f"Warning: chain.get_pools() returned {type(pools)} instead of list for chain {chain_id}")
                pools = []

            # Filter invalid pools
            pools = self._filter_invalid_pools(pools)

            self.cache[chain_id] = {
                "pools": pools,
                "last_updated": timestamp
            }

            return pools
        except Exception as e:
            print(f"Failed to fetch and cache pools for chain {chain_id}: {type(e).__name__}: {str(e)}")
            # Cache empty list to avoid repeated failures
            self.cache[chain_id] = {
                "pools": [],
                "last_updated": timestamp
            }
            return []

    def start_background_updates(self):
        """Start the background update thread."""
        with self.update_thread_lock:
            if self.update_thread is None or not self.update_thread.is_alive():
                self.update_running = True
                self.update_thread = threading.Thread(target=self._background_worker, daemon=True)
                self.update_thread.start()
                print("🔄 Background cache update thread started")

    def set_enabled_chains(self, chain_ids: Optional[List[str]]):
        """Set which chains should be cached. None means cache all chains.

        Args:
            chain_ids (Optional[List[str]]): List of chain IDs to cache, or None for all chains
        """
        with self.lock:
            self.enabled_chain_ids = chain_ids
            if chain_ids is not None:
                # Remove cached data for chains that are no longer enabled
                chains_to_remove = [chain_id for chain_id in self.cache.keys()
                                  if chain_id not in chain_ids]
                for chain_id in chains_to_remove:
                    del self.cache[chain_id]
                    print(f"Removed cache for disabled chain {chain_id}")

    def set_cache_duration_minutes(self, minutes: int):
        """Set the cache duration in minutes.

        Args:
            minutes (int): Cache duration in minutes
        """
        self.cache_duration = timedelta(minutes=minutes)
        print(f"Cache duration set to {minutes} minutes")

    def set_pool_filtering(self, enabled: bool):
        """Enable or disable pool filtering.

        Args:
            enabled (bool): Whether to filter out invalid pools
        """
        self.filter_invalid_pools = enabled
        print(f"Pool filtering {'enabled' if enabled else 'disabled'}")

    def configure_cache(self, config: CacheConfig):
        """Configure the cache with a CacheConfig object.

        Args:
            config (CacheConfig): The cache configuration
        """
        self.set_cache_duration_minutes(config.duration_minutes)
        self.set_enabled_chains(config.enabled_chain_ids)
        self.set_pool_filtering(config.filter_invalid_pools)

    def stop_background_updates(self):
        """Stop the background update thread."""
        with self.update_thread_lock:
            self.update_running = False
            if self.update_thread and self.update_thread.is_alive():
                self.update_thread.join(timeout=5)

    def _background_worker(self):
        """Background worker that updates all cached chains periodically."""
        while self.update_running:
            try:
                # Sleep for the configured cache duration between cache updates
                time.sleep(self.cache_duration.total_seconds())

                if not self.update_running:
                    break

                updated_count = self._update_all_caches()

                if updated_count > 0:
                    print(f"🔄 Cache updated: {updated_count} entries refreshed")

            except Exception as e:
                print(f"❌ Cache update error: {type(e).__name__}: {str(e)}")

    def _update_all_caches(self):
        """Update all enabled cached chains that are older than cache duration.

        Returns:
            int: Number of cache entries that were updated
        """
        updated_count = 0

        # Get list of chains to potentially update
        with self.lock:
            if self.enabled_chain_ids is None:
                chains_to_check = list(self.cache.keys())
            else:
                chains_to_check = [chain_id for chain_id in self.cache.keys()
                                 if chain_id in self.enabled_chain_ids]

        for chain_id in chains_to_check:
            # Check if update is needed without holding the main lock
            needs_update = False
            with self.lock:
                if chain_id in self.cache:
                    cache_entry = self.cache[chain_id]
                    now = datetime.now()
                    if now - cache_entry["last_updated"] >= self.cache_duration:
                        needs_update = True

            # If update needed, use fetch lock to coordinate with user requests
            if needs_update:
                try:
                    with self._get_fetch_lock(chain_id):
                        # Double-check after acquiring fetch lock
                        with self.lock:
                            if chain_id in self.cache:
                                cache_entry = self.cache[chain_id]
                                now = datetime.now()
                                if now - cache_entry["last_updated"] >= self.cache_duration:
                                    self._fetch_and_cache_pools(chain_id, now)
                                    updated_count += 1
                except Exception as e:
                    print(f"Error updating cache for chain {chain_id}: {type(e).__name__}: {str(e)}")

        return updated_count


# Global cache instance
_cache = PoolsCache()


def _get_cached_pools(chain_id: str) -> List[LiquidityPool]:
    """Get cached pools for a chain."""
    import time
    start_time = time.time()
    result = _cache.get_pools(chain_id)
    duration = time.time() - start_time

    # Log slow requests (>1 second)
    if duration > 1.0:
        print(f"Slow cache request for chain {chain_id}: {duration:.2f}s")
    return result


def _get_pool_from_cache(chain_id: str, address: str) -> Optional[LiquidityPool]:
    """Get a specific pool by address from cache."""
    return _cache.get_pool_by_address(chain_id, address)


def _get_pools_from_chain(chain_id: str) -> List[LiquidityPool]:
    """Get pools directly from chain without using cache."""
    try:
        with get_chain(chain_id) as chain:
            result = chain.get_pools()
            # Ensure we got a list back
            if not isinstance(result, list):
                print(f"Warning: chain.get_pools() returned {type(result)} instead of list for chain {chain_id}")
                return []
            # Filter invalid pools
            filtered_result = _cache._filter_invalid_pools(result)
            return filtered_result
    except Exception as e:
        print(f"Failed to get pools from chain {chain_id}: {type(e).__name__}: {str(e)}")
        return []


def _get_pool_from_chain(chain_id: str, address: str) -> Optional[LiquidityPool]:
    """Get a specific pool directly from chain without using cache."""
    try:
        with get_chain(chain_id) as chain:
            return chain.get_pool_by_address(address)
    except Exception as e:
        print(f"Failed to get pool {address} from chain {chain_id}: {type(e).__name__}: {str(e)}")
        return None


def start_background_updates():
    """Start the background update thread."""
    _cache.start_background_updates()


def set_enabled_chains(chain_ids: Optional[List[str]]):
    """Set which chains should be cached. None means cache all chains.

    Args:
        chain_ids (Optional[List[str]]): List of chain IDs to cache, or None for all chains
    """
    _cache.set_enabled_chains(chain_ids)

def set_pool_filtering(enabled: bool):
    """Enable or disable pool filtering.

    Args:
        enabled (bool): Whether to filter out invalid pools
    """
    _cache.set_pool_filtering(enabled)

def set_cache_duration_minutes(minutes: int):
    """Set the cache duration in minutes.

    Args:
        minutes (int): Cache duration in minutes
    """
    _cache.set_cache_duration_minutes(minutes)

def configure_cache(config: CacheConfig):
    """Configure the cache with a CacheConfig object.

    Args:
        config (CacheConfig): The cache configuration
    """
    _cache.configure_cache(config)

def stop_background_updates():
    """Stop the background update thread."""
    _cache.stop_background_updates()


def start_cache_system(cache_config: CacheConfig):
    """Configure and start the cache system with the given configuration."""
    # Apply configuration and show summary
    configure_cache(cache_config)
    print(f"🔧 Cache configured: {cache_config.duration_minutes}min duration, chains: {cache_config.enabled_chain_ids}, filtering: {'enabled' if cache_config.filter_invalid_pools else 'disabled'}")

    # Start background cache updates
    start_background_updates()

    # Pre-populate cache for enabled chains
    print("📦 Initializing cache...")
    enabled_chains = cache_config.enabled_chain_ids or []
    for chain_id in enabled_chains:
        try:
            pools = _get_cached_pools(chain_id)
            if pools and len(pools) > 0:
                print(f"✅ Cached {len(pools)} pools for chain {chain_id}")
            else:
                print(f"⚠️  No pools found for chain {chain_id}")
        except Exception as e:
            print(f"❌ Failed to cache chain {chain_id}: {type(e).__name__}: {str(e)}")

    print("🚀 Server ready!")
