from typing import Protocol


class CredentialsCache(Protocol):
    def get(self) -> str | None:
        """
        Retrieve cached credentials.

        Returns:
            The cached credentials as a JSON string, or None if not found.
        """
        ...

    def set(self, value: str) -> None:
        """
        Store credentials in the cache.

        Args:
            value: The credentials to store as a JSON string.
        """
        ...
