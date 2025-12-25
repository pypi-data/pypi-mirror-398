import httpx

from .errors import NordlysError
from .models import SelectModelRequest, SelectModelResponse


class RouterClient:
    def __init__(self, client: httpx.Client, base_url: str, headers: dict[str, str]) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._headers = headers

    def select_model(self, request: SelectModelRequest) -> SelectModelResponse:
        url = f"{self._base_url}/select-model"
        response = self._client.post(
            url,
            json=request.model_dump(exclude_none=True),
            headers=self._headers,
        )
        if response.is_success:
            return SelectModelResponse.model_validate(response.json())
        raise NordlysError(
            "Nordlys router select_model failed",
            status_code=response.status_code,
            payload=_safe_json(response),
        )


class AsyncRouterClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str, headers: dict[str, str]) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._headers = headers

    async def select_model(self, request: SelectModelRequest) -> SelectModelResponse:
        url = f"{self._base_url}/select-model"
        response = await self._client.post(
            url,
            json=request.model_dump(exclude_none=True),
            headers=self._headers,
        )
        if response.is_success:
            return SelectModelResponse.model_validate(response.json())
        raise NordlysError(
            "Nordlys router select_model failed",
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
