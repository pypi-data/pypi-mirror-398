import time
import threading
from collections import OrderedDict


class LoadingCache:
    """
    A Python implementation of Guava's LoadingCache with:
    - Automatic value loading
    - Time-based expiration (write/access)
    - Size-based eviction (LRU)
    - Thread-safe operations
    """

    def __init__(self, loader, max_size=None, expire_after_write=None, expire_after_access=None):
        """
        Args:
            loader (callable): Function that takes a key and returns a value
            max_size (int, optional): Maximum number of entries before eviction
            expire_after_write (float, optional): Seconds before write expiration
            expire_after_access (float, optional): Seconds before access expiration
        """
        if not callable(loader):
            raise ValueError("Loader must be a callable function")

        self.loader = loader
        self.max_size = max_size
        self.expire_after_write = expire_after_write
        self.expire_after_access = expire_after_access
        self.cache = OrderedDict()
        self.lock = threading.Lock()

    def get(self, key):
        """Get value for key, loading if necessary"""
        with self.lock:
            current_time = time.time()
            if key in self.cache:
                entry = self.cache[key]
                expired = self._is_expired(entry, current_time)

                if not expired:
                    # Update access time and mark as recently used
                    entry['access_time'] = current_time
                    self.cache.move_to_end(key)
                    return entry['value']
                else:
                    del self.cache[key]

            # Load new value
            try:
                value = self.loader(key)
            except Exception as e:
                raise e

            # Store new entry
            new_entry = {
                'value': value,
                'write_time': current_time,
                'access_time': current_time
            }
            self.cache[key] = new_entry

            # Handle size-based eviction
            if self.max_size is not None and len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

            return value

    def get_if_present(self, key):
        """Get value if present and not expired, otherwise return None"""
        with self.lock:
            current_time = time.time()
            if key in self.cache:
                entry = self.cache[key]
                if not self._is_expired(entry, current_time):
                    entry['access_time'] = current_time
                    self.cache.move_to_end(key)
                    return entry['value']
                else:
                    del self.cache[key]
            return None

    def invalidate(self, key):
        """Remove a specific key from the cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]

    def invalidate_all(self):
        """Clear all entries from the cache"""
        with self.lock:
            self.cache.clear()

    def _is_expired(self, entry, current_time):
        """Check if entry is expired based on configured policies"""
        if self.expire_after_write is not None:
            if current_time - entry['write_time'] > self.expire_after_write:
                return True

        if self.expire_after_access is not None:
            if current_time - entry['access_time'] > self.expire_after_access:
                return True

        return False

    def __getitem__(self, key):
        """Support dictionary-style access: cache[key]"""
        return self.get(key)

    def __contains__(self, key):
        """Support 'in' operator with expiration check"""
        return self.get_if_present(key) is not None
