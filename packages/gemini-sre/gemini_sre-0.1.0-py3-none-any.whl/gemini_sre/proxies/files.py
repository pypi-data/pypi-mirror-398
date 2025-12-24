"""
Files namespace proxy.

Wraps client.files.* methods with SRE features and deduplication.
"""

from typing import Optional


class FilesProxy:
    """Proxy for client.files namespace."""

    def __init__(self, sre_client):
        """Initialize files proxy."""
        self._sre_client = sre_client

    def upload(
        self,
        file: str,
        *,
        request_id: Optional[str] = None,
        enable_deduplication: bool = True,
        **kwargs,
    ):
        """
        Upload file with deduplication.

        By default, uses content hash for deduplication to prevent
        uploading the same file twice on retry.

        Args:
            file: Path to file to upload
            request_id: Optional request ID for tracking
            enable_deduplication: Use deduplication cache (default: True)
            **kwargs: Additional parameters passed to SDK

        Returns:
            Uploaded file object from SDK
        """
        import hashlib
        import os

        # Validate file exists
        if not os.path.exists(file):
            raise FileNotFoundError(f"File not found: {file}")

        # Calculate content hash for deduplication
        content_hash = None
        if enable_deduplication:
            with open(file, "rb") as f:
                content_hash = hashlib.sha256(f.read()).hexdigest()

        # Use deduplication cache if enabled
        if enable_deduplication and self._sre_client._dedup_cache:
            cache_key = f"upload:sha256:{content_hash}"

            def _upload_operation():
                """Upload file (called only on cache miss)."""

                def _operation(client, location):
                    return client.files.upload(file=file, **kwargs)

                return self._sre_client._execute_with_failover(
                    operation_func=_operation,
                    operation_type="non_idempotent",
                    request_id=request_id,
                )

            # Get cached result or create new
            return self._sre_client._dedup_cache.get_or_create(
                cache_key=cache_key,
                factory_func=_upload_operation,
            )

        # No deduplication - direct upload
        def _operation(client, location):
            return client.files.upload(file=file, **kwargs)

        return self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="non_idempotent",
            request_id=request_id,
        )

    def get(self, file: str, *, request_id: Optional[str] = None):
        """Get file metadata with SRE features."""

        def _operation(client, location):
            return client.files.get(file=file)

        return self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )

    def list(
        self,
        config: Optional[dict] = None,
        *,
        request_id: Optional[str] = None,
    ):
        """List files with SRE features."""

        def _operation(client, location):
            return client.files.list(config=config)

        return self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_read",
            request_id=request_id,
        )

    def delete(self, file: str, *, request_id: Optional[str] = None):
        """Delete file with SRE features (idempotent)."""

        def _operation(client, location):
            return client.files.delete(file=file)

        return self._sre_client._execute_with_failover(
            operation_func=_operation,
            operation_type="idempotent_write",
            request_id=request_id,
        )

    # TODO: Implement download()
