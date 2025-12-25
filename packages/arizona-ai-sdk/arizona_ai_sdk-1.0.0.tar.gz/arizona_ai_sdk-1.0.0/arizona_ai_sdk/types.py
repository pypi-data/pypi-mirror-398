from typing import Literal, Union, List, Dict, Any, TypeVar, Callable, Awaitable

MessageRole = Literal["user", "assistant", "system"]
SearchSort = Literal["relevance", "date"]
SearchType = Literal["post", "thread"]
ConfigScope = Literal["library", "all", "global"]

ModelId = str
ChatId = str
ConfigId = str

T = TypeVar("T")
SyncOrAsync = Union[T, Awaitable[T]]

JSONDict = Dict[str, Any]
JSONList = List[JSONDict]

StreamCallback = Callable[[str], None]
