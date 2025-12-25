from typing import Callable, Optional


class Provider:
    """
    A provider is a link in a chain, that contains the remaining links.
    Like a linked list!
    Each link contains an initializer for loading configuration values from
    some location
    """

    _store: Optional[dict]
    _next: Optional["Provider"]

    @staticmethod
    def pipe(*initializers: Callable[[], dict]) -> "Provider":
        """
        Some sugar on the .then calls
        Creates a provider for each, and then chains them automatically
        :param initializers:
        :return:
        """
        provider = Provider(lambda: {})
        for initializer in initializers:
            provider.then(initializer)
        return provider

    def __init__(self, initializer: Callable[[], dict]):
        self._next = None
        self._store = None
        self._initializer = initializer

    def _get_here(self, key: str):
        if self._store is None:
            self._store = self._initializer()
            assert isinstance(self._store, dict)
        if self._store.get(key, None) is not None:
            return self._store.get(key)
        return None

    def get(self, key: str):
        """
        Gets a value for 'key' in the provider chain.
        If it was not found in the current provider, then it defers the request to the next provider
        If there are no remaining providers, return None
        :param key:
        :return:
        """
        result = self._get_here(key)
        if result is not None:
            return result
        if self._next is not None:
            return self._next.get(key)
        return None

    def then(self, initializer: Callable[[], dict]) -> None:
        """
        Adds another provider to the chain
        :param initializer:
        :return:
        """
        if self._next is None:
            self._next = Provider(initializer)
        else:
            self._next.then(initializer)
