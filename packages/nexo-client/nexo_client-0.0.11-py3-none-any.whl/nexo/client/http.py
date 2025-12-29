import httpx
from contextlib import asynccontextmanager
from typing import AsyncGenerator


class HTTPClientManager:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient()

    async def _client_handler(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        """Async generator for client handling"""
        if self._client is None or (
            self._client is not None and self._client.is_closed
        ):
            self._client = httpx.AsyncClient()
        yield self._client

    async def inject(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        return self._client_handler()

    @asynccontextmanager
    async def get(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        async for client in self._client_handler():
            yield client
