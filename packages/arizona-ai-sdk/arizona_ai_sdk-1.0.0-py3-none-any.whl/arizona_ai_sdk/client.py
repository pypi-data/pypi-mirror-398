from typing import Optional, Dict, List, Union, AsyncIterator, Callable
from arizona_ai_sdk.http_client import HTTPClient
from arizona_ai_sdk.api.chat import ChatAPI
from arizona_ai_sdk.api.models import ModelsAPI
from arizona_ai_sdk.api.user import UserAPI
from arizona_ai_sdk.api.configs import ConfigsAPI
from arizona_ai_sdk.api.tokens import TokensAPI
from arizona_ai_sdk.api.forum import ForumAPI
from arizona_ai_sdk.models.chat import Message, ChatCompletion, ChatCompletionChunk, Attachment


class ArizonaAIClient:
    DEFAULT_BASE_URL = "https://arizona-ai.ru"
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        verify_ssl: bool = True,
        custom_headers: Optional[Dict[str, str]] = None,
    ):
        if not api_key:
            raise ValueError("API key is required")
        
        self._api_key = api_key
        self._base_url = base_url or self.DEFAULT_BASE_URL
        self._timeout = timeout
        self._max_retries = max_retries
        self._verify_ssl = verify_ssl
        
        self._http_client = HTTPClient(
            api_key=api_key,
            base_url=self._base_url,
            timeout=timeout,
            max_retries=max_retries,
            verify_ssl=verify_ssl,
            custom_headers=custom_headers,
        )
        
        self.chat = ChatAPI(self._http_client)
        self.models = ModelsAPI(self._http_client)
        self.user = UserAPI(self._http_client)
        self.configs = ConfigsAPI(self._http_client)
        self.tokens = TokensAPI(self._http_client)
        self.forum = ForumAPI(self._http_client)
    
    @property
    def api_key(self) -> str:
        return self._api_key
    
    @property
    def base_url(self) -> str:
        return self._base_url
    
    def complete(
        self,
        messages: Union[str, List[Message], List[Dict[str, str]]],
        model: str = "arizona-lm-forum",
        stream: bool = False,
        temperature: Optional[float] = None,
        config_id: Optional[str] = None,
        attachments: Optional[List[Union[Attachment, Dict[str, str]]]] = None,
        callback: Optional[Callable[[str], None]] = None,
    ) -> Union[ChatCompletion, str]:
        return self.chat.create(
            messages=messages,
            model=model,
            stream=stream,
            temperature=temperature,
            config_id=config_id,
            attachments=attachments,
            callback=callback,
        )
    
    async def acomplete(
        self,
        messages: Union[str, List[Message], List[Dict[str, str]]],
        model: str = "arizona-lm-forum",
        stream: bool = False,
        temperature: Optional[float] = None,
        config_id: Optional[str] = None,
        attachments: Optional[List[Union[Attachment, Dict[str, str]]]] = None,
    ) -> Union[ChatCompletion, AsyncIterator[ChatCompletionChunk]]:
        return await self.chat.acreate(
            messages=messages,
            model=model,
            stream=stream,
            temperature=temperature,
            config_id=config_id,
            attachments=attachments,
        )
    
    def ask(
        self,
        question: str,
        model: str = "arizona-lm-forum",
        config_id: Optional[str] = None,
    ) -> str:
        completion = self.chat.completions(
            messages=question,
            model=model,
            config_id=config_id,
        )
        return completion.content
    
    async def aask(
        self,
        question: str,
        model: str = "arizona-lm-forum",
        config_id: Optional[str] = None,
    ) -> str:
        completion = await self.chat.acompletions(
            messages=question,
            model=model,
            config_id=config_id,
        )
        return completion.content
    
    def is_valid(self) -> bool:
        return self.user.is_valid()
    
    async def ais_valid(self) -> bool:
        return await self.user.ais_valid()
    
    def close(self) -> None:
        self._http_client.close()
    
    async def aclose(self) -> None:
        await self._http_client.aclose()
    
    def __enter__(self) -> "ArizonaAIClient":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
    
    async def __aenter__(self) -> "ArizonaAIClient":
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()
    
    def __repr__(self) -> str:
        return f"ArizonaAIClient(base_url={self._base_url!r})"
