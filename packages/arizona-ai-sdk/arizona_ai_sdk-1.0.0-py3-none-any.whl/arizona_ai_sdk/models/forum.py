from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from arizona_ai_sdk.models.base import BaseModel


@dataclass
class ForumServer(BaseModel):
    id: int = 0
    name: str = ""
    online: Optional[int] = None
    max_online: Optional[int] = None
    status: Optional[str] = None


@dataclass
class ForumCategory(BaseModel):
    id: int = 0
    title: str = ""
    description: Optional[str] = None
    thread_count: Optional[int] = None
    post_count: Optional[int] = None
    parent_id: Optional[int] = None


@dataclass
class ForumThread(BaseModel):
    id: int = 0
    title: str = ""
    category_id: Optional[int] = None
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    post_count: Optional[int] = None
    view_count: Optional[int] = None
    created_at: Optional[str] = None
    last_post_at: Optional[str] = None
    is_pinned: bool = False
    is_closed: bool = False


@dataclass
class ForumPost(BaseModel):
    id: int = 0
    thread_id: Optional[int] = None
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    content: str = ""
    created_at: Optional[str] = None
    edited_at: Optional[str] = None
    is_first_post: bool = False


@dataclass
class ForumMember(BaseModel):
    id: int = 0
    username: str = ""
    avatar_url: Optional[str] = None
    title: Optional[str] = None
    post_count: Optional[int] = None
    reaction_score: Optional[int] = None
    joined_at: Optional[str] = None
    last_seen_at: Optional[str] = None
    is_staff: bool = False
    is_banned: bool = False


@dataclass
class ForumSearchResult(BaseModel):
    status: str = "success"
    threads: List[ForumThread] = field(default_factory=list)
    posts: List[ForumPost] = field(default_factory=list)
    members: List[ForumMember] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ForumSearchResult":
        if data is None:
            data = {}
        results = data.get("data", [])
        
        threads = []
        posts = []
        members = []
        
        if isinstance(results, list):
            for item in results:
                if isinstance(item, dict):
                    if "thread_id" in item or "post_count" in item:
                        threads.append(ForumThread.from_dict(item))
                    elif "content" in item:
                        posts.append(ForumPost.from_dict(item))
                    elif "username" in item:
                        members.append(ForumMember.from_dict(item))
        
        return cls(
            status=data.get("status", "success"),
            threads=threads,
            posts=posts,
            members=members
        )


@dataclass
class ForumServersResponse(BaseModel):
    status: str = "success"
    servers: List[ForumServer] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ForumServersResponse":
        if data is None:
            data = {}
        servers_data = data.get("data", [])
        servers = [ForumServer.from_dict(s) for s in servers_data] if isinstance(servers_data, list) else []
        return cls(
            status=data.get("status", "success"),
            servers=servers
        )


@dataclass
class ForumCategoryThreadsResponse(BaseModel):
    status: str = "success"
    threads: List[ForumThread] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ForumCategoryThreadsResponse":
        if data is None:
            data = {}
        result = data.get("data", {})
        threads_data = result if isinstance(result, list) else result.get("threads", [])
        threads = [ForumThread.from_dict(t) for t in threads_data]
        return cls(
            status=data.get("status", "success"),
            threads=threads
        )


@dataclass
class ForumThreadPostsResponse(BaseModel):
    status: str = "success"
    posts: List[ForumPost] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ForumThreadPostsResponse":
        if data is None:
            data = {}
        result = data.get("data", {})
        posts_data = result if isinstance(result, list) else result.get("posts", [])
        posts = [ForumPost.from_dict(p) for p in posts_data]
        return cls(
            status=data.get("status", "success"),
            posts=posts
        )
