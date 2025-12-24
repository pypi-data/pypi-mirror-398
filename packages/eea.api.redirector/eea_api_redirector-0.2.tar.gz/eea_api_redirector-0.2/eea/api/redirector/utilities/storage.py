"""Storage utilities"""

import os
import re
import logging
from redis import Redis
from zope.interface import implementer
from zope.component import getUtility
from zope.component.hooks import getSite
from eea.api.redirector.interfaces import IStorageUtility

logger = logging.getLogger("eea.api.redirector")


def patched_redirection_storage_get(self, old_path, default=None):
    """Get redirection target for old_path, checking also Redis.

    We can not register a custom utility for this as all existing aliases would be lost.
    """
    value = self._old_get(old_path, default)
    if value:
        return value

    # Check Redis storage
    rs = getUtility(IStorageUtility)
    site_id = getSite().getId()
    if old_path.startswith("/" + site_id):
        old_path = old_path[len(site_id) + 1 :]
    value = rs.get(old_path)
    if value:
        logger.debug("Found redis value for %s: %s", old_path, value)
        value = value.decode("utf-8")
        if value.startswith("http://") or value.startswith("https://"):
            return value
        if value.startswith("/") and not value.startswith("/" + site_id):
            value = "/" + site_id + value
        return value
    return default


@implementer(IStorageUtility)
class RedisStorageUtility:
    """Redis Storage Utility"""

    _timeout = None
    _db = None
    _server = None
    _port = None

    @property
    def timeout(self):
        """Get timeout from environment or default to 5 seconds."""
        if not self._timeout:
            try:
                self._timeout = int(os.environ.get("REDIS_TIMEOUT", 5))
            except ValueError:
                self._timeout = 5
        return self._timeout

    @property
    def db(self):
        """Get Redis DB index from environment or default to 0."""
        if not self._db:
            try:
                self._db = int(os.environ.get("REDIS_DB", 0))
            except ValueError:
                self._db = 0
        return self._db

    @property
    def server(self):
        """Get Redis server address from environment or default to localhost."""
        if not self._server:
            self._server = os.environ.get("REDIS_SERVER", "localhost")
        return self._server

    @property
    def port(self):
        """Get Redis server port from environment or default to 6379."""
        if not self._port:
            try:
                self._port = int(os.environ.get("REDIS_PORT", 6379))
            except Exception:
                self._port = 6379
        return self._port

    def get(self, key):
        """Get a value from Redis by key."""
        if not key:
            return None

        try:
            with Redis(
                host=self.server,
                port=self.port,
                db=self.db,
                socket_connect_timeout=self.timeout,
            ) as conn:
                return conn.get(key)
        except Exception as err:
            logger.exception(err)
            return None

    def set(self, key, value):
        """Set a value in Redis by key."""
        if not key:
            return None

        try:
            with Redis(
                host=self.server,
                port=self.port,
                db=self.db,
                socket_connect_timeout=self.timeout,
            ) as conn:
                return conn.set(key, value)
        except Exception as err:
            logger.exception(err)
            return None

    def delete(self, key):
        """Delete a value from Redis by key."""
        if not key:
            return None

        try:
            with Redis(
                host=self.server,
                port=self.port,
                db=self.db,
                socket_connect_timeout=self.timeout,
            ) as conn:
                return conn.delete(key)
        except Exception as err:
            logger.exception(err)
            return None

    def scan(self, pattern="*", count=100):
        """Scan Redis keys matching pattern.

        Returns an iterator of keys.
        Uses SCAN for efficient iteration over large datasets.
        """
        try:
            with Redis(
                host=self.server,
                port=self.port,
                db=self.db,
                socket_connect_timeout=self.timeout,
            ) as conn:
                cursor = 0
                while True:
                    cursor, keys = conn.scan(cursor=cursor, match=pattern, count=count)
                    for key in keys:
                        yield key
                    if cursor == 0:
                        break
        except Exception as err:
            logger.exception(err)
            return

    def list_paginated(
        self,
        pattern="*",
        query=None,
        batch_size=25,
        batch_start=0,
        search_scope="old_url",
    ):
        """List redirects from Redis with efficient pagination.

        Args:
            pattern: Redis key pattern (default: "*")
            query: Optional search query to filter URLs
            batch_size: Number of items per page
            batch_start: Offset for pagination
            search_scope: Where to search - "old_url", "new_url", or "both" (default: "old_url")

        Returns:
            Tuple of (list of redirects, total count, None)
        """
        # If there's a query, use query-specific method
        if query:
            return self._list_with_query(
                pattern, query, batch_size, batch_start, search_scope
            )

        # For non-query listing, collect all keys first
        matching_keys = []

        try:
            with Redis(
                host=self.server,
                port=self.port,
                db=self.db,
                socket_connect_timeout=self.timeout,
            ) as conn:
                # Collect all keys matching pattern (keys only, no values)
                cursor = 0
                while True:
                    cursor, keys = conn.scan(cursor=cursor, match=pattern, count=1000)

                    for key in keys:
                        try:
                            key_str = (
                                key.decode("utf-8") if isinstance(key, bytes) else key
                            )
                            matching_keys.append(key_str)
                        except Exception as err:
                            logger.warning(f"Error processing key {key}: {err}")
                            continue

                    if cursor == 0:
                        break

                # Sort keys alphabetically for consistent display
                matching_keys.sort()

                total = len(matching_keys)

                # Fetch values only for the requested page
                page_keys = matching_keys[batch_start : batch_start + batch_size]
                items = []

                for key_str in page_keys:
                    try:
                        value = conn.get(key_str)
                        if value is not None:
                            value_str = (
                                value.decode("utf-8")
                                if isinstance(value, bytes)
                                else value
                            )
                            items.append(
                                {
                                    "path": key_str,
                                    "redirect-to": value_str,
                                }
                            )
                    except Exception as err:
                        logger.warning(f"Error fetching value for key {key_str}: {err}")
                        continue

                return items, total, None

        except Exception as err:
            logger.exception(err)
            return [], 0, None

    def get_statistics(self, pattern="*", query=None):
        """Get statistics for redirects matching pattern/query.

        This is a separate method to allow async loading of statistics.
        Uses Redis pipelining to batch GET operations for much better performance.
        Searches on both old URL paths (keys) and new URL paths (values).

        Args:
            pattern: Redis key pattern (default: "*")
            query: Optional search query to filter old or new URL paths (supports regex)

        Returns:
            Dict with statistics: total, internal, external, gone
        """
        stats = {
            "total": 0,
            "internal": 0,
            "external": 0,
            "gone": 0,
        }

        try:
            with Redis(
                host=self.server,
                port=self.port,
                db=self.db,
                socket_connect_timeout=self.timeout,
            ) as conn:
                # Check if query is a regex pattern
                is_regex = False
                regex_pattern = None
                if query:
                    if (
                        query.startswith("^")
                        or query.endswith("$")
                        or any(
                            c in query for c in [".*", ".+", "[", "]", "(", ")", "|"]
                        )
                    ):
                        is_regex = True
                        try:
                            regex_pattern = re.compile(query)
                        except re.error as err:
                            logger.warning(f"Invalid regex pattern '{query}': {err}")
                            is_regex = False

                # Determine search pattern
                if query and query.startswith("/") and not is_regex:
                    search_pattern = f"*{query}*"
                else:
                    search_pattern = pattern

                # Collect all keys
                all_keys = []
                cursor = 0

                while True:
                    cursor, keys = conn.scan(
                        cursor=cursor, match=search_pattern, count=1000
                    )
                    all_keys.extend(keys)

                    if cursor == 0:
                        break

                # Fetch all values in batches using Redis pipeline
                BATCH_SIZE = 1000
                for i in range(0, len(all_keys), BATCH_SIZE):
                    batch_keys = all_keys[i : i + BATCH_SIZE]

                    pipe = conn.pipeline()
                    for key in batch_keys:
                        pipe.get(key)
                    values = pipe.execute()

                    # Filter on both keys and values
                    for key, value in zip(batch_keys, values):
                        if value is not None:
                            key_str = (
                                key.decode("utf-8") if isinstance(key, bytes) else key
                            )
                            value_str = (
                                value.decode("utf-8")
                                if isinstance(value, bytes)
                                else value
                            )

                            # Apply query filter on both old URL path (key) and new URL path (value)
                            if query:
                                key_match = False
                                value_match = False

                                if is_regex:
                                    key_match = (
                                        regex_pattern.search(key_str) is not None
                                    )
                                    value_match = (
                                        regex_pattern.search(value_str) is not None
                                    )
                                else:
                                    key_match = query in key_str
                                    value_match = query in value_str

                                # Skip if neither key nor value matches
                                if not (key_match or value_match):
                                    continue

                            stats["total"] += 1

                            if not value_str or value_str.strip() == "":
                                stats["gone"] += 1
                            elif value_str.startswith(
                                "http://"
                            ) or value_str.startswith("https://"):
                                stats["external"] += 1
                            else:
                                stats["internal"] += 1

                return stats

        except Exception as err:
            logger.exception(err)
            return stats

    def _list_with_query(
        self, pattern, query, batch_size, batch_start, search_scope="old_url"
    ):
        """List redirects with query filter.

        Searches on old URL paths (keys), new URL paths (values), or both using pipelining.
        Collects all keys, fetches values in batches, filters based on scope, then paginates.

        Args:
            pattern: Redis key pattern
            query: Search query to filter URLs (supports regex)
            batch_size: Number of items per page
            batch_start: Offset for pagination
            search_scope: Where to search - "old_url", "new_url", or "both" (default: "old_url")

        Returns:
            Tuple of (list of redirects, total count, None)
        """
        matching_items = []
        try:
            with Redis(
                host=self.server,
                port=self.port,
                db=self.db,
                socket_connect_timeout=self.timeout,
            ) as conn:
                # Check if query is a regex pattern
                is_regex = False
                regex_pattern = None
                if query:
                    if (
                        query.startswith("^")
                        or query.endswith("$")
                        or any(
                            c in query for c in [".*", ".+", "[", "]", "(", ")", "|"]
                        )
                    ):
                        is_regex = True
                        try:
                            regex_pattern = re.compile(query)
                        except re.error as err:
                            logger.warning(f"Invalid regex pattern '{query}': {err}")
                            is_regex = False

                # Use Redis pattern matching for path-based queries
                if query and query.startswith("/") and not is_regex:
                    search_pattern = f"*{query}*"
                else:
                    search_pattern = pattern

                cursor = 0
                all_keys = []

                # Step 1: Collect all keys
                # Note: When searching values, we need all keys. Pipelining makes this fast.
                while True:
                    cursor, keys = conn.scan(
                        cursor=cursor, match=search_pattern, count=1000
                    )
                    all_keys.extend(keys)

                    if cursor == 0:
                        break

                # Step 2: Fetch all values in batches using pipeline
                BATCH_SIZE = 1000
                key_value_pairs = []

                for i in range(0, len(all_keys), BATCH_SIZE):
                    batch_keys = all_keys[i : i + BATCH_SIZE]

                    pipe = conn.pipeline()
                    for key in batch_keys:
                        pipe.get(key)
                    values = pipe.execute()

                    # Pair keys with values
                    for key, value in zip(batch_keys, values):
                        if value is not None:
                            key_str = (
                                key.decode("utf-8") if isinstance(key, bytes) else key
                            )
                            value_str = (
                                value.decode("utf-8")
                                if isinstance(value, bytes)
                                else value
                            )
                            key_value_pairs.append((key_str, value_str))

                # Step 3: Filter based on search scope
                for key_str, value_str in key_value_pairs:
                    try:
                        key_match = False
                        value_match = False

                        # Check matches based on scope
                        if query:
                            if is_regex:
                                key_match = regex_pattern.search(key_str) is not None
                                value_match = (
                                    regex_pattern.search(value_str) is not None
                                )
                            else:
                                key_match = query in key_str
                                value_match = query in value_str

                            # Include based on search scope
                            should_include = False
                            if search_scope == "old_url":
                                should_include = key_match
                            elif search_scope == "new_url":
                                should_include = value_match
                            else:  # both
                                should_include = key_match or value_match

                            if should_include:
                                matching_items.append(
                                    {
                                        "path": key_str,
                                        "redirect-to": value_str,
                                    }
                                )
                        else:
                            # No query, include all
                            matching_items.append(
                                {
                                    "path": key_str,
                                    "redirect-to": value_str,
                                }
                            )

                    except Exception as err:
                        logger.warning(f"Error processing key {key_str}: {err}")
                        continue

                # Sort by old URL path (key) alphabetically
                matching_items.sort(key=lambda x: x["path"])

                total = len(matching_items)

                # Step 4: Paginate the results
                page_items = matching_items[batch_start : batch_start + batch_size]

                return page_items, total, None

        except Exception as err:
            logger.exception(err)
            return [], 0, None
