from typing import Optional, List, Union, Dict, TYPE_CHECKING
from arizona_ai_sdk.models.tokens import TokenCount
from arizona_ai_sdk.models.chat import Attachment

if TYPE_CHECKING:
    from arizona_ai_sdk.http_client import HTTPClient


class TokensAPI:
    def __init__(self, client: "HTTPClient"):
        self._client = client
    
    def count(
        self,
        content: str,
        model: str = "default",
        attachments: Optional[List[Union[Attachment, Dict[str, str]]]] = None,
    ) -> TokenCount:
        prepared_attachments = None
        if attachments:
            prepared_attachments = []
            for att in attachments:
                if isinstance(att, Attachment):
                    prepared_attachments.append(att.to_dict())
                elif isinstance(att, dict):
                    prepared_attachments.append(att)
        
        payload = {
            "content": content,
            "model": model,
        }
        if prepared_attachments:
            payload["attachments"] = prepared_attachments
        
        response = self._client.post("count-tokens", json_data=payload)
        return TokenCount.from_dict(response)
    
    async def acount(
        self,
        content: str,
        model: str = "default",
        attachments: Optional[List[Union[Attachment, Dict[str, str]]]] = None,
    ) -> TokenCount:
        prepared_attachments = None
        if attachments:
            prepared_attachments = []
            for att in attachments:
                if isinstance(att, Attachment):
                    prepared_attachments.append(att.to_dict())
                elif isinstance(att, dict):
                    prepared_attachments.append(att)
        
        payload = {
            "content": content,
            "model": model,
        }
        if prepared_attachments:
            payload["attachments"] = prepared_attachments
        
        response = await self._client.apost("count-tokens", json_data=payload)
        return TokenCount.from_dict(response)
    
    def count_messages(
        self,
        messages: List[Dict[str, str]],
        model: str = "default",
    ) -> int:
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            token_count = self.count(content, model)
            total += token_count.token_count
        return total
    
    async def acount_messages(
        self,
        messages: List[Dict[str, str]],
        model: str = "default",
    ) -> int:
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            token_count = await self.acount(content, model)
            total += token_count.token_count
        return total
    
    def estimate_cost(
        self,
        content: str,
        model: str = "default",
    ) -> Dict[str, any]:
        token_count = self.count(content, model)
        return {
            "tokens": token_count.token_count,
            "max_request": token_count.max_request_tokens,
            "max_chat": token_count.max_chat_tokens,
            "within_request_limit": not token_count.exceeds_request_limit(),
            "within_chat_limit": not token_count.exceeds_chat_limit(),
        }
    
    async def aestimate_cost(
        self,
        content: str,
        model: str = "default",
    ) -> Dict[str, any]:
        token_count = await self.acount(content, model)
        return {
            "tokens": token_count.token_count,
            "max_request": token_count.max_request_tokens,
            "max_chat": token_count.max_chat_tokens,
            "within_request_limit": not token_count.exceeds_request_limit(),
            "within_chat_limit": not token_count.exceeds_chat_limit(),
        }
