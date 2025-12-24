"""
Caches namespace proxy.

Wraps client.caches.* methods with SRE features.
"""


class CachesProxy:
    """Proxy for client.caches namespace."""

    def __init__(self, sre_client):
        """Initialize caches proxy."""
        self._sre_client = sre_client

    # TODO: Implement caches methods
    # - create() with deduplication
    # - get()
    # - list()
    # - update()
    # - delete()
