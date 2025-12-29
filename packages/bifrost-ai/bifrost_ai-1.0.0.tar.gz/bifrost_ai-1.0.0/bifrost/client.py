# sdk/python/bifrost/client.py
"""
BifrostAI Python SDK
A unified client for multiple AI providers with automatic conversation management
✅ NOW WITH FILE SUPPORT!
"""

import os
import json
import httpx
import base64
from typing import Optional, List, Dict, Any, Union, AsyncGenerator
from dataclasses import dataclass
from pathlib import Path
import asyncio
import logging

# Import storage backends
from .storage import StorageBackend, create_storage

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Chat message"""
    role: str  # "system", "user", or "assistant"
    content: Union[str, List[Dict[str, Any]]]
    
    def to_dict(self):
        return {"role": self.role, "content": self.content}


@dataclass
class ChatCompletion:
    """Chat completion response"""
    id: str
    model: str
    content: str
    role: str = "assistant"
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    provider: Optional[str] = None
    files_processed: Optional[int] = None  # ✅ NEW
    
    @classmethod
    def from_response(cls, response: Dict[str, Any]):
        """Create from API response"""
        choice = response["choices"][0] if response.get("choices") else {}
        message = choice.get("message", {})
        
        return cls(
            id=response.get("id", ""),
            model=response.get("model", ""),
            content=message.get("content", ""),
            role=message.get("role", "assistant"),
            finish_reason=choice.get("finish_reason"),
            usage=response.get("usage"),
            provider=response.get("provider"),
            files_processed=response.get("files_processed")  # ✅ NEW
        )


# ✅ NEW: File attachment helper
@dataclass
class FileAttachment:
    """File attachment for chat requests"""
    filename: str
    content_type: str
    data: str  # Base64-encoded
    size: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to API format"""
        result = {
            "filename": self.filename,
            "content_type": self.content_type,
            "data": self.data
        }
        if self.size is not None:
            result["size"] = self.size
        return result
    
    @classmethod
    def from_file(cls, file_path: str, content_type: Optional[str] = None):
        """
        Create FileAttachment from a file path
        
        Args:
            file_path: Path to the file
            content_type: MIME type (auto-detected if None)
        
        Example:
            attachment = FileAttachment.from_file("document.pdf")
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read and encode file
        with open(path, "rb") as f:
            file_bytes = f.read()
            file_data = base64.b64encode(file_bytes).decode('utf-8')
        
        # Auto-detect content type if not provided
        if content_type is None:
            content_type = cls._detect_content_type(path.suffix)
        
        return cls(
            filename=path.name,
            content_type=content_type,
            data=file_data,
            size=len(file_bytes)
        )
    
    @classmethod
    def from_bytes(
        cls,
        filename: str,
        file_bytes: bytes,
        content_type: Optional[str] = None
    ):
        """
        Create FileAttachment from bytes
        
        Args:
            filename: Name of the file
            file_bytes: File content as bytes
            content_type: MIME type (auto-detected if None)
        
        Example:
            attachment = FileAttachment.from_bytes(
                "data.json",
                json.dumps(data).encode(),
                "application/json"
            )
        """
        file_data = base64.b64encode(file_bytes).decode('utf-8')
        
        if content_type is None:
            ext = Path(filename).suffix
            content_type = cls._detect_content_type(ext)
        
        return cls(
            filename=filename,
            content_type=content_type,
            data=file_data,
            size=len(file_bytes)
        )
    
    @staticmethod
    def _detect_content_type(extension: str) -> str:
        """Auto-detect MIME type from file extension"""
        ext = extension.lower().lstrip('.')
        
        mime_types = {
            # Documents
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'md': 'text/markdown',
            
            # Code
            'py': 'text/x-python',
            'js': 'text/javascript',
            'ts': 'text/typescript',
            'java': 'text/x-java',
            'cpp': 'text/x-c++',
            'c': 'text/x-c',
            'go': 'text/x-go',
            'rs': 'text/x-rust',
            
            # Data
            'json': 'application/json',
            'csv': 'text/csv',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls': 'application/vnd.ms-excel',
            
            # Images
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp',
        }
        
        return mime_types.get(ext, 'application/octet-stream')


class BifrostAI:
    """
    BifrostAI client with automatic conversation management and file support.
    
    Usage modes:
    
    1. Low-level (manual context):
        client = BifrostAI(api_key="...")
        response = client.create_chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}]
        )
    
    2. High-level (automatic context):
        client = BifrostAI(api_key="...", storage="memory")
        response = client.chat("conv1", "Hello", model="gpt-4")
        response = client.chat("conv1", "How are you?")  # Context remembered!
    
    3. With files:
        client = BifrostAI(api_key="...", storage="memory")
        
        # Using file path
        response = client.chat_with_files(
            conversation_id="conv1",
            message="Analyze this document",
            files=["document.pdf"],
            model="gpt-4-turbo"
        )
        
        # Or using FileAttachment
        attachment = FileAttachment.from_file("code.py")
        response = client.chat_with_files(
            conversation_id="conv1",
            message="Review this code",
            files=[attachment]
        )
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.bifrost.ai",
        storage: Optional[Union[str, StorageBackend]] = None,
        openai_key: Optional[str] = None,
        anthropic_key: Optional[str] = None,
        gemini_key: Optional[str] = None,
        google_key: Optional[str] = None,
        timeout: float = 120.0  # ✅ Increased for file uploads
    ):
        """
        Initialize BifrostAI client
        
        Args:
            api_key: Your BifrostAI API key
            base_url: API base URL
            storage: Storage backend for conversations
            openai_key: OpenAI API key (optional)
            anthropic_key: Anthropic API key (optional)
            gemini_key: Google Gemini API key (optional)
            google_key: Alternative name for Gemini key (optional)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("BIFROST_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        # Storage for conversation management
        self.storage = self._init_storage(storage) if storage else None
        
        # Provider keys
        self.provider_keys = {
            "openai": openai_key or os.getenv("OPENAI_API_KEY"),
            "anthropic": anthropic_key or os.getenv("ANTHROPIC_API_KEY"),
            "google": gemini_key or google_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        }
        
        # HTTP clients
        self.client = httpx.Client(timeout=self.timeout)
        self.async_client = httpx.AsyncClient(timeout=self.timeout)
        
        # Convenience namespaces (backward compatibility)
        self.chat_ns = ChatNamespace(self)
        self.models = ModelsNamespace(self)
    
    def _init_storage(self, storage: Union[str, StorageBackend]) -> StorageBackend:
        """Initialize storage backend"""
        if isinstance(storage, str):
            return create_storage(storage)
        else:
            return storage
    
    @classmethod
    def from_env(cls, storage: Optional[str] = None):
        """Create client with all keys from environment variables"""
        return cls(
            api_key=os.getenv("BIFROST_API_KEY"),
            openai_key=os.getenv("OPENAI_API_KEY"),
            anthropic_key=os.getenv("ANTHROPIC_API_KEY"),
            gemini_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            storage=storage
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add Bifrost API key
        if self.api_key:
            headers["X-Bifrost-Key"] = self.api_key
        
        # Add provider keys
        if self.provider_keys["openai"]:
            headers["X-OpenAI-Key"] = self.provider_keys["openai"]
        if self.provider_keys["anthropic"]:
            headers["X-Anthropic-Key"] = self.provider_keys["anthropic"]
        if self.provider_keys["google"]:
            headers["X-Gemini-Key"] = self.provider_keys["google"]
        
        return headers
    
    # ========== High-Level API (Automatic Context Management) ==========
    
    def chat(
        self,
        conversation_id: str,
        message: str,
        model: str = "gpt-3.5-turbo",
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletion:
        """
        Send a message in a conversation with automatic context management.
        
        Args:
            conversation_id: Unique conversation identifier
            message: User message to send
            model: AI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
        
        Returns:
            ChatCompletion response
        
        Example:
            client = BifrostAI(api_key="...", storage="memory")
            response = client.chat("conv1", "What's 2+2?", model="gpt-4")
            print(response.content)
        """
        if not self.storage:
            raise ValueError(
                "Storage not configured. Initialize with storage parameter:\n"
                "  client = BifrostAI(api_key='...', storage='memory')"
            )
        
        # Save user message
        self.storage.save_message(conversation_id, "user", message)
        
        # Get full conversation history
        messages = self.storage.get_messages(conversation_id)
        
        # Call API with full context
        response = self.create_chat_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Save assistant response
        self.storage.save_message(conversation_id, "assistant", response.content)
        
        return response
    
    async def achat(
        self,
        conversation_id: str,
        message: Union[str, List[Dict[str, Any]]],  # ✅ Support multimodal
        model: str = "gpt-3.5-turbo",
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletion:
        """Async version of chat()"""
        if not self.storage:
            raise ValueError(
                "Storage not configured. Initialize with storage parameter:\n"
                "  client = BifrostAI(api_key='...', storage='memory')"
            )
        
        # Save user message (convert to string if multimodal)
        message_text = message if isinstance(message, str) else json.dumps(message)
        self.storage.save_message(conversation_id, "user", message_text)
        
        # Get full conversation history
        messages = self.storage.get_messages(conversation_id)
        
        # Call API with full context
        response = await self.acreate_chat_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Save assistant response
        self.storage.save_message(conversation_id, "assistant", response.content)
        
        return response
    
    # ✅ NEW: High-level file support
    def chat_with_files(
        self,
        conversation_id: str,
        message: str,
        files: List[Union[str, FileAttachment]],
        model: str = "gpt-4-turbo",
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletion:
        """
        Send a message with file attachments.
        
        Args:
            conversation_id: Conversation ID
            message: User message
            files: List of file paths or FileAttachment objects
            model: AI model (use vision-capable for images)
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
        
        Returns:
            ChatCompletion response
        
        Example:
            # With file paths
            response = client.chat_with_files(
                conversation_id="conv1",
                message="Analyze these files",
                files=["document.pdf", "image.png"],
                model="gpt-4-turbo"
            )
            
            # With FileAttachment objects
            attachment = FileAttachment.from_file("code.py")
            response = client.chat_with_files(
                conversation_id="conv1",
                message="Review this code",
                files=[attachment]
            )
        """
        if not self.storage:
            raise ValueError("Storage not configured")
        
        # Convert file paths to FileAttachment objects
        attachments = []
        for file in files:
            if isinstance(file, str):
                attachments.append(FileAttachment.from_file(file))
            elif isinstance(file, FileAttachment):
                attachments.append(file)
            else:
                raise ValueError(f"Invalid file type: {type(file)}")
        
        # Save user message
        self.storage.save_message(conversation_id, "user", message)
        
        # Get conversation history
        messages = self.storage.get_messages(conversation_id)
        
        # Call API with files
        response = self.create_chat_completion(
            model=model,
            messages=messages,
            files=attachments,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Save assistant response
        self.storage.save_message(conversation_id, "assistant", response.content)
        
        return response
    
    async def achat_with_files(
        self,
        conversation_id: str,
        message: str,
        files: List[Union[str, FileAttachment]],
        model: str = "gpt-4-turbo",
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletion:
        """Async version of chat_with_files()"""
        if not self.storage:
            raise ValueError("Storage not configured")
        
        # Convert file paths to FileAttachment objects
        attachments = []
        for file in files:
            if isinstance(file, str):
                attachments.append(FileAttachment.from_file(file))
            elif isinstance(file, FileAttachment):
                attachments.append(file)
            else:
                raise ValueError(f"Invalid file type: {type(file)}")
        
        # Save user message
        self.storage.save_message(conversation_id, "user", message)
        
        # Get conversation history
        messages = self.storage.get_messages(conversation_id)
        
        # Call API with files
        response = await self.acreate_chat_completion(
            model=model,
            messages=messages,
            files=attachments,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Save assistant response
        self.storage.save_message(conversation_id, "assistant", response.content)
        
        return response
    
    # ========== Conversation Management ==========
    
    def get_conversation(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get full conversation history"""
        if not self.storage:
            raise ValueError("Storage not configured")
        return self.storage.get_messages(conversation_id)
    
    def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation"""
        if not self.storage:
            raise ValueError("Storage not configured")
        self.storage.delete_conversation(conversation_id)
    
    def list_conversations(self) -> List[str]:
        """List all conversation IDs"""
        if not self.storage:
            raise ValueError("Storage not configured")
        return self.storage.list_conversations()
    
    # ========== Low-Level API (Manual Context Management) ==========
    
    def create_chat_completion(
        self,
        model: str,
        messages: List[Union[Message, Dict[str, Any]]],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        files: Optional[List[FileAttachment]] = None,  # ✅ NEW
        **kwargs
    ) -> Union[ChatCompletion, AsyncGenerator]:
        """
        Create a chat completion (low-level API).
        
        Args:
            model: Model ID
            messages: List of messages (full conversation history)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            files: Optional file attachments
            **kwargs: Additional parameters
        
        Returns:
            ChatCompletion object or stream generator
        
        Example:
            # Without files
            response = client.create_chat_completion(
                model="gpt-4",
                messages=[{"role": "user", "content": "Hello"}]
            )
            
            # With files
            attachment = FileAttachment.from_file("document.pdf")
            response = client.create_chat_completion(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": "Analyze this"}],
                files=[attachment]
            )
        """
        # Convert messages to dicts
        message_dicts = []
        for msg in messages:
            if isinstance(msg, Message):
                message_dicts.append(msg.to_dict())
            else:
                message_dicts.append(msg)
        
        # Build request
        request_data = {
            "model": model,
            "messages": message_dicts,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens:
            request_data["max_tokens"] = max_tokens
        
        # ✅ Add files if provided
        if files:
            request_data["files"] = [f.to_dict() for f in files]
        
        # Add any additional parameters
        request_data.update(kwargs)
        
        if stream:
            return self._stream_chat_completion(request_data)
        else:
            response = self.client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self._get_headers(),
                json=request_data
            )
            
            if response.status_code != 200:
                raise BifrostError(f"API error: {response.text}")
            
            return ChatCompletion.from_response(response.json())
    
    async def acreate_chat_completion(
        self,
        model: str,
        messages: List[Union[Message, Dict[str, Any]]],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        files: Optional[List[FileAttachment]] = None,  # ✅ NEW
        **kwargs
    ) -> Union[ChatCompletion, AsyncGenerator]:
        """Async version of create_chat_completion"""
        # Convert messages to dicts
        message_dicts = []
        for msg in messages:
            if isinstance(msg, Message):
                message_dicts.append(msg.to_dict())
            else:
                message_dicts.append(msg)
        
        # Build request
        request_data = {
            "model": model,
            "messages": message_dicts,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens:
            request_data["max_tokens"] = max_tokens
        
        # ✅ Add files if provided
        if files:
            request_data["files"] = [f.to_dict() for f in files]
        
        request_data.update(kwargs)
        
        if stream:
            return self._astream_chat_completion(request_data)
        else:
            response = await self.async_client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self._get_headers(),
                json=request_data
            )
            
            if response.status_code != 200:
                raise BifrostError(f"API error: {response.text}")
            
            return ChatCompletion.from_response(response.json())
    
    def _stream_chat_completion(self, request_data: Dict[str, Any]):
        """Stream chat completion"""
        with self.client.stream(
            "POST",
            f"{self.base_url}/v1/chat/completions",
            headers=self._get_headers(),
            json=request_data
        ) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    chunk_str = line[6:]
                    if chunk_str == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(chunk_str)
                        yield chunk
                    except json.JSONDecodeError:
                        continue
    
    async def _astream_chat_completion(self, request_data: Dict[str, Any]):
        """Async stream chat completion"""
        async with self.async_client.stream(
            "POST",
            f"{self.base_url}/v1/chat/completions",
            headers=self._get_headers(),
            json=request_data
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    chunk_str = line[6:]
                    if chunk_str == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(chunk_str)
                        yield chunk
                    except json.JSONDecodeError:
                        continue
    
    # ========== Models API ==========
    
    def list_models(self) -> Dict[str, Any]:
        """List available models"""
        response = self.client.get(
            f"{self.base_url}/v1/models",
            headers=self._get_headers()
        )
        
        if response.status_code != 200:
            raise BifrostError(f"API error: {response.text}")
        
        return response.json()
    
    async def alist_models(self) -> Dict[str, Any]:
        """Async list available models"""
        response = await self.async_client.get(
            f"{self.base_url}/v1/models",
            headers=self._get_headers()
        )
        
        if response.status_code != 200:
            raise BifrostError(f"API error: {response.text}")
        
        return response.json()
    
    # ========== Context Managers ==========
    
    def close(self):
        """Close HTTP clients"""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.async_client.aclose()


# ========== Convenience Namespaces (Backward Compatibility) ==========

class ChatNamespace:
    """Chat completions namespace for convenience"""
    
    def __init__(self, client: BifrostAI):
        self.client = client
        self.completions = ChatCompletionsNamespace(client)


class ChatCompletionsNamespace:
    """Chat completions sub-namespace"""
    
    def __init__(self, client: BifrostAI):
        self.client = client
    
    def create(self, **kwargs) -> ChatCompletion:
        """Create a chat completion"""
        return self.client.create_chat_completion(**kwargs)
    
    async def acreate(self, **kwargs) -> ChatCompletion:
        """Async create a chat completion"""
        return await self.client.acreate_chat_completion(**kwargs)


class ModelsNamespace:
    """Models namespace for convenience"""
    
    def __init__(self, client: BifrostAI):
        self.client = client
    
    def list(self) -> Dict[str, Any]:
        """List available models"""
        return self.client.list_models()
    
    async def alist(self) -> Dict[str, Any]:
        """Async list available models"""
        return await self.client.alist_models()


class BifrostError(Exception):
    """BifrostAI API error"""
    pass