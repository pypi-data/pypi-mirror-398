import httpx

from .errors import NordlysError
from .models import (
    RegistryModel,
    RegistryModelsQuery,
    RegistryProvider,
    RegistryProvidersQuery,
)


class RegistryClient:
    def __init__(self, client: httpx.Client, base_url: str, headers: dict[str, str]) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._headers = headers

    def models(self, filters: RegistryModelsQuery | None = None) -> list[RegistryModel]:
        url = f"{self._base_url}/models"
        params = filters.model_dump(exclude_none=True) if filters else None
        response = self._client.get(url, params=params, headers=self._headers)
        if response.is_success:
            return [RegistryModel.model_validate(item) for item in response.json()]
        raise NordlysError(
            "Nordlys registry models request failed",
            status_code=response.status_code,
            payload=_safe_json(response),
        )

    def model(self, model_id: str) -> RegistryModel:
        url = f"{self._base_url}/models/{model_id}"
        response = self._client.get(url, headers=self._headers)
        if response.is_success:
            return RegistryModel.model_validate(response.json())
        raise NordlysError(
            f"Nordlys registry model lookup failed for {model_id}",
            status_code=response.status_code,
            payload=_safe_json(response),
        )

    def providers(self, filters: RegistryProvidersQuery | None = None) -> list[RegistryProvider]:
        url = f"{self._base_url}/providers"
        params = filters.model_dump(exclude_none=True) if filters else None
        response = self._client.get(url, params=params, headers=self._headers)
        if response.is_success:
            return [RegistryProvider.model_validate(item) for item in response.json()]
        raise NordlysError(
            "Nordlys registry providers request failed",
            status_code=response.status_code,
            payload=_safe_json(response),
        )


class AsyncRegistryClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str, headers: dict[str, str]) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._headers = headers

    async def models(self, filters: RegistryModelsQuery | None = None) -> list[RegistryModel]:
        url = f"{self._base_url}/models"
        params = filters.model_dump(exclude_none=True) if filters else None
        response = await self._client.get(url, params=params, headers=self._headers)
        if response.is_success:
            return [RegistryModel.model_validate(item) for item in response.json()]
        raise NordlysError(
            "Nordlys registry models request failed",
            status_code=response.status_code,
            payload=_safe_json(response),
        )

    async def model(self, model_id: str) -> RegistryModel:
        url = f"{self._base_url}/models/{model_id}"
        response = await self._client.get(url, headers=self._headers)
        if response.is_success:
            return RegistryModel.model_validate(response.json())
        raise NordlysError(
            f"Nordlys registry model lookup failed for {model_id}",
            status_code=response.status_code,
            payload=_safe_json(response),
        )

    async def providers(
        self, filters: RegistryProvidersQuery | None = None
    ) -> list[RegistryProvider]:
        url = f"{self._base_url}/providers"
        params = filters.model_dump(exclude_none=True) if filters else None
        response = await self._client.get(url, params=params, headers=self._headers)
        if response.is_success:
            return [RegistryProvider.model_validate(item) for item in response.json()]
        raise NordlysError(
            "Nordlys registry providers request failed",
            status_code=response.status_code,
            payload=_safe_json(response),
        )


def _safe_json(response: httpx.Response) -> dict | list | str | None:
    try:
        data = response.json()
    except ValueError:
        return response.text
    if isinstance(data, (dict, list, str)):
        return data
    return str(data)
