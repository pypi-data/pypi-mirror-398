"""Remote scope fetching for scope resolution."""

from daimyo.domain import RemoteScopeClient, RemoteScopeUnavailableError, Scope
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)


class RemoteScopeFetcher:
    """Fetches scopes from remote master server with graceful failure handling."""

    def __init__(self, remote_client: RemoteScopeClient | None, master_url: str | None):
        self.remote_client = remote_client
        self.master_url = master_url

    def fetch_scope(self, scope_name: str) -> Scope | None:
        """Fetch a scope from the configured master server.

        :param scope_name: Name of the scope to fetch
        :type scope_name: str
        :returns: Scope if found, None otherwise
        :rtype: Scope | None
        """
        if not self.remote_client:
            logger.debug("No remote client configured, skipping remote fetch")
            return None

        if not self.master_url or self.master_url.strip() == "":
            logger.debug("No master server URL configured, skipping remote fetch")
            return None

        try:
            logger.debug(f"Fetching scope '{scope_name}' from master server {self.master_url}")
            return self.remote_client.fetch_scope(self.master_url, scope_name)
        except RemoteScopeUnavailableError as e:
            logger.warning(f"Remote scope '{scope_name}' temporarily unavailable: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch scope '{scope_name}' from master server: {e}")
            return None


__all__ = ["RemoteScopeFetcher"]
