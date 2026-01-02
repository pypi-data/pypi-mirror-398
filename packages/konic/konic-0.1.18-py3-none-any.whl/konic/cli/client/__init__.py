from konic.cli.client.api_client import KonicAPIClient


class _LazyClient:
    """
    Lazy initialization wrapper for KonicAPIClient.

    This class defers the instantiation of KonicAPIClient until it's first accessed,
    allowing tests to mock the client before it's created and avoiding the need
    for environment variables during module import.
    """

    _instance: KonicAPIClient | None = None

    def _get_client(self) -> KonicAPIClient:
        if self._instance is None:
            self._instance = KonicAPIClient()
        return self._instance

    def __getattr__(self, name: str):
        return getattr(self._get_client(), name)


client = _LazyClient()

__all__: list[str] = ["KonicAPIClient", "client"]
