from typing import Optional, Dict, Any, AsyncIterator, Union, Callable
import httpx
import json
import asyncio
from arizona_ai_sdk.exceptions import (
    ArizonaAIError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
    StreamError,
    ConnectionError,
    TimeoutError,
)


class HTTPClient:
    DEFAULT_BASE_URL = "https://arizona-ai.ru"
    DEFAULT_TIMEOUT = 60.0
    DEFAULT_MAX_RETRIES = 3
    API_VERSION = "v1"
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        verify_ssl: bool = True,
        custom_headers: Optional[Dict[str, str]] = None,
    ):
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ArizonaAI-Python/1.0.0",
        }
        if custom_headers:
            self._headers.update(custom_headers)
        
        self._sync_client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None
    
    def _get_sync_client(self) -> httpx.Client:
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                base_url=self.base_url,
                headers=self._headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
        return self._sync_client
    
    def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
        return self._async_client
    
    def _build_url(self, endpoint: str) -> str:
        endpoint = endpoint.lstrip("/")
        if not endpoint.startswith(f"api/{self.API_VERSION}"):
            endpoint = f"/api/{self.API_VERSION}/{endpoint}"
        else:
            endpoint = f"/{endpoint}"
        return endpoint
    
    def _handle_response_error(self, response: httpx.Response) -> None:
        status_code = response.status_code
        
        try:
            data = response.json()
            error_message = data.get("error", data.get("message", response.text))
        except (json.JSONDecodeError, ValueError):
            error_message = response.text or f"HTTP {status_code}"
        
        if status_code == 401:
            raise AuthenticationError(error_message, status_code, data if 'data' in dir() else {})
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                error_message, 
                status_code, 
                data if 'data' in dir() else {},
                float(retry_after) if retry_after else None
            )
        elif status_code == 404:
            raise NotFoundError(error_message, status_code, data if 'data' in dir() else {})
        elif status_code == 400:
            raise ValidationError(error_message, status_code, data if 'data' in dir() else {})
        elif status_code >= 500:
            raise ServerError(error_message, status_code, data if 'data' in dir() else {})
        else:
            raise ArizonaAIError(error_message, status_code, data if 'data' in dir() else {})
    
    def _parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        if not response.is_success:
            self._handle_response_error(response)
        
        if response.status_code == 204:
            return {}
        
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError):
            return {"data": response.text}
    
    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        url = self._build_url(endpoint)
        client = self._get_sync_client()
        
        try:
            response = client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            )
            return self._parse_response(response)
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to {self.base_url}: {e}")
        except httpx.TimeoutException as e:
            if retry_count < self.max_retries:
                return self.request(method, endpoint, params, json_data, retry_count + 1)
            raise TimeoutError(f"Request timed out after {self.timeout}s: {e}")
        except httpx.HTTPError as e:
            raise ArizonaAIError(f"HTTP error: {e}")
    
    async def arequest(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        url = self._build_url(endpoint)
        client = self._get_async_client()
        
        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            )
            return self._parse_response(response)
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to {self.base_url}: {e}")
        except httpx.TimeoutException as e:
            if retry_count < self.max_retries:
                await asyncio.sleep(min(2 ** retry_count, 10))
                return await self.arequest(method, endpoint, params, json_data, retry_count + 1)
            raise TimeoutError(f"Request timed out after {self.timeout}s: {e}")
        except httpx.HTTPError as e:
            raise ArizonaAIError(f"HTTP error: {e}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request("POST", endpoint, json_data=json_data)
    
    async def aget(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.arequest("GET", endpoint, params=params)
    
    async def apost(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.arequest("POST", endpoint, json_data=json_data)
    
    async def astream(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        url = self._build_url(endpoint)
        client = self._get_async_client()
        
        try:
            async with client.stream(
                method="POST",
                url=url,
                json=json_data,
            ) as response:
                if not response.is_success:
                    await response.aread()
                    self._handle_response_error(response)
                
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    if line.startswith("data: "):
                        data_str = line[6:]
                        
                        if data_str == "[DONE]":
                            return
                        
                        try:
                            data = json.loads(data_str)
                            yield data
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to {self.base_url}: {e}")
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Stream timed out: {e}")
        except httpx.HTTPError as e:
            raise StreamError(f"Stream error: {e}")
    
    def stream(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> str:
        url = self._build_url(endpoint)
        client = self._get_sync_client()
        full_content = []
        
        try:
            with client.stream(
                method="POST",
                url=url,
                json=json_data,
            ) as response:
                if not response.is_success:
                    response.read()
                    self._handle_response_error(response)
                
                for line in response.iter_lines():
                    if not line:
                        continue
                    
                    if line.startswith("data: "):
                        data_str = line[6:]
                        
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            if callback:
                                callback(data)
                            
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_content.append(content)
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to {self.base_url}: {e}")
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Stream timed out: {e}")
        except httpx.HTTPError as e:
            raise StreamError(f"Stream error: {e}")
        
        return "".join(full_content)
    
    def close(self) -> None:
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
    
    async def aclose(self) -> None:
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None
    
    def __enter__(self) -> "HTTPClient":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
    
    async def __aenter__(self) -> "HTTPClient":
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()
