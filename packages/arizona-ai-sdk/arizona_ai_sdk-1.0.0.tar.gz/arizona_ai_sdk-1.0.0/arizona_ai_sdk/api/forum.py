from typing import Optional, List, Union, TYPE_CHECKING
from arizona_ai_sdk.models.forum import (
    ForumServer,
    ForumCategory,
    ForumThread,
    ForumPost,
    ForumMember,
    ForumServersResponse,
    ForumCategoryThreadsResponse,
    ForumThreadPostsResponse,
    ForumSearchResult,
)
from arizona_ai_sdk.types import SearchSort, SearchType

if TYPE_CHECKING:
    from arizona_ai_sdk.http_client import HTTPClient


class ForumAPI:
    def __init__(self, client: "HTTPClient"):
        self._client = client
    
    def get_servers(self) -> List[ForumServer]:
        response = self._client.get("forum/servers")
        servers_response = ForumServersResponse.from_dict(response)
        return servers_response.servers
    
    async def aget_servers(self) -> List[ForumServer]:
        response = await self._client.aget("forum/servers")
        servers_response = ForumServersResponse.from_dict(response)
        return servers_response.servers
    
    def get_category(self, category_id: int) -> ForumCategory:
        response = self._client.get(f"forum/category/{category_id}")
        data = response.get("data", response)
        return ForumCategory.from_dict(data)
    
    async def aget_category(self, category_id: int) -> ForumCategory:
        response = await self._client.aget(f"forum/category/{category_id}")
        data = response.get("data", response)
        return ForumCategory.from_dict(data)
    
    def get_thread(self, thread_id: int) -> ForumThread:
        response = self._client.get(f"forum/thread/{thread_id}")
        data = response.get("data", response)
        return ForumThread.from_dict(data)
    
    async def aget_thread(self, thread_id: int) -> ForumThread:
        response = await self._client.aget(f"forum/thread/{thread_id}")
        data = response.get("data", response)
        return ForumThread.from_dict(data)
    
    def get_post(self, post_id: int) -> ForumPost:
        response = self._client.get(f"forum/post/{post_id}")
        data = response.get("data", response)
        return ForumPost.from_dict(data)
    
    async def aget_post(self, post_id: int) -> ForumPost:
        response = await self._client.aget(f"forum/post/{post_id}")
        data = response.get("data", response)
        return ForumPost.from_dict(data)
    
    def get_member(self, user_id: int) -> ForumMember:
        response = self._client.get(f"forum/member/{user_id}")
        data = response.get("data", response)
        return ForumMember.from_dict(data)
    
    async def aget_member(self, user_id: int) -> ForumMember:
        response = await self._client.aget(f"forum/member/{user_id}")
        data = response.get("data", response)
        return ForumMember.from_dict(data)
    
    def get_category_threads(
        self,
        category_id: int,
        page: int = 1,
    ) -> List[ForumThread]:
        params = {"page": page}
        response = self._client.get(f"forum/category/{category_id}/threads", params=params)
        threads_response = ForumCategoryThreadsResponse.from_dict(response)
        return threads_response.threads
    
    async def aget_category_threads(
        self,
        category_id: int,
        page: int = 1,
    ) -> List[ForumThread]:
        params = {"page": page}
        response = await self._client.aget(f"forum/category/{category_id}/threads", params=params)
        threads_response = ForumCategoryThreadsResponse.from_dict(response)
        return threads_response.threads
    
    def get_thread_posts(
        self,
        thread_id: int,
        page: int = 1,
    ) -> List[ForumPost]:
        params = {"page": page}
        response = self._client.get(f"forum/thread/{thread_id}/posts", params=params)
        posts_response = ForumThreadPostsResponse.from_dict(response)
        return posts_response.posts
    
    async def aget_thread_posts(
        self,
        thread_id: int,
        page: int = 1,
    ) -> List[ForumPost]:
        params = {"page": page}
        response = await self._client.aget(f"forum/thread/{thread_id}/posts", params=params)
        posts_response = ForumThreadPostsResponse.from_dict(response)
        return posts_response.posts
    
    def search_threads(
        self,
        query: str,
        sort: SearchSort = "relevance",
        author: Optional[str] = None,
        nodes: Optional[Union[int, List[int]]] = None,
        include_children: bool = False,
        search_type: SearchType = "post",
    ) -> ForumSearchResult:
        params = {
            "query": query,
            "sort": sort,
            "search_type": search_type,
            "include_children": str(include_children).lower(),
        }
        if author:
            params["author"] = author
        if nodes:
            if isinstance(nodes, list):
                params["nodes"] = ",".join(map(str, nodes))
            else:
                params["nodes"] = str(nodes)
        
        response = self._client.get("forum/search/threads", params=params)
        return ForumSearchResult.from_dict(response)
    
    async def asearch_threads(
        self,
        query: str,
        sort: SearchSort = "relevance",
        author: Optional[str] = None,
        nodes: Optional[Union[int, List[int]]] = None,
        include_children: bool = False,
        search_type: SearchType = "post",
    ) -> ForumSearchResult:
        params = {
            "query": query,
            "sort": sort,
            "search_type": search_type,
            "include_children": str(include_children).lower(),
        }
        if author:
            params["author"] = author
        if nodes:
            if isinstance(nodes, list):
                params["nodes"] = ",".join(map(str, nodes))
            else:
                params["nodes"] = str(nodes)
        
        response = await self._client.aget("forum/search/threads", params=params)
        return ForumSearchResult.from_dict(response)
    
    def search_members(self, nickname: str) -> List[ForumMember]:
        params = {"nickname": nickname}
        response = self._client.get("forum/search/members", params=params)
        data = response.get("data", [])
        return [ForumMember.from_dict(m) for m in data] if isinstance(data, list) else []
    
    async def asearch_members(self, nickname: str) -> List[ForumMember]:
        params = {"nickname": nickname}
        response = await self._client.aget("forum/search/members", params=params)
        data = response.get("data", [])
        return [ForumMember.from_dict(m) for m in data] if isinstance(data, list) else []
