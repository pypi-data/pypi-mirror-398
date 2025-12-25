import base64
import mimetypes
from pathlib import Path
from typing import Optional
from arizona_ai_sdk.models.chat import Attachment


def file_to_attachment(
    file_path: str,
    name: Optional[str] = None,
    mime_type: Optional[str] = None,
) -> Attachment:
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if name is None:
        name = path.name
    
    if mime_type is None:
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type is None:
            mime_type = "application/octet-stream"
    
    with open(path, "rb") as f:
        file_bytes = f.read()
    
    base64_data = base64.b64encode(file_bytes).decode("utf-8")
    
    return Attachment(name=name, type=mime_type, base64=base64_data)


def bytes_to_attachment(
    data: bytes,
    name: str,
    mime_type: str,
) -> Attachment:
    base64_data = base64.b64encode(data).decode("utf-8")
    return Attachment(name=name, type=mime_type, base64=base64_data)


def format_messages(
    messages: list,
    system_prompt: Optional[str] = None,
) -> list:
    from arizona_ai_sdk.models.chat import Message
    
    formatted = []
    
    if system_prompt:
        formatted.append(Message.system(system_prompt))
    
    for msg in messages:
        if isinstance(msg, Message):
            formatted.append(msg)
        elif isinstance(msg, dict):
            formatted.append(Message.from_dict(msg))
        elif isinstance(msg, str):
            formatted.append(Message.user(msg))
        elif isinstance(msg, tuple) and len(msg) == 2:
            role, content = msg
            formatted.append(Message(role=role, content=content))
    
    return formatted


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
