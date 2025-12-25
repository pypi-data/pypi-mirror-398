import inspect
import os
from types import TracebackType

import httpx
from openai import AsyncOpenAI, OpenAI
from openai.resources.chat import AsyncChat, Chat
from openai.resources.completions import AsyncCompletions, Completions

from .registry import AsyncRegistryClient, RegistryClient
from .router import AsyncRouterClient, RouterClient

DEFAULT_BASE_URL = "https://api.llmadaptive.uk/v1"
DEFAULT_TIMEOUT_S = 60.0


def _resolve_api_key(api_key: str | None) -> str:
    resolved_key = api_key or os.getenv("NORDLYS_API_KEY")
    if not resolved_key:
        raise ValueError("Nordlys API key is required (set NORDLYS_API_KEY or pass api_key)")
    return resolved_key


class Nordlys:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT_S,
        headers: dict[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._api_key = _resolve_api_key(api_key)
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {self._api_key}"}
        if headers:
            self._headers.update(headers)
        self._http_client = http_client or httpx.Client(timeout=timeout)
        self._openai = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            default_headers=self._headers,
        )
        self.registry = RegistryClient(self._http_client, self._base_url, self._headers)
        self.router = RouterClient(self._http_client, self._base_url, self._headers)

    @property
    def chat(self) -> Chat:
        return self._openai.chat

    @property
    def completions(self) -> Completions:
        return self._openai.completions

    def close(self) -> None:
        self._http_client.close()
        close = getattr(self._openai, "close", None)
        if callable(close):
            close()

    def __enter__(self) -> "Nordlys":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class AsyncNordlys:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT_S,
        headers: dict[str, str] | None = None,
        async_http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = _resolve_api_key(api_key)
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {self._api_key}"}
        if headers:
            self._headers.update(headers)
        self._http_client = async_http_client or httpx.AsyncClient(timeout=timeout)
        self._openai = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            default_headers=self._headers,
        )
        self.registry = AsyncRegistryClient(self._http_client, self._base_url, self._headers)
        self.router = AsyncRouterClient(self._http_client, self._base_url, self._headers)

    @property
    def chat(self) -> AsyncChat:
        return self._openai.chat

    @property
    def completions(self) -> AsyncCompletions:
        return self._openai.completions

    async def aclose(self) -> None:
        await self._http_client.aclose()
        close = getattr(self._openai, "close", None)
        if callable(close):
            result = close()
            if inspect.isawaitable(result):
                await result

    async def __aenter__(self) -> "AsyncNordlys":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()
