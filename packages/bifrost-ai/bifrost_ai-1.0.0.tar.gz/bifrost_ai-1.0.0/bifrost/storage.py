# sdk/python/bifrost/storage.py

from typing import Protocol, List, Dict, Optional
import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# ========== Storage Interface ==========

class StorageBackend(Protocol):
    """Interface for conversation storage backends"""
    
    def save_message(self, conv_id: str, role: str, content: str) -> None:
        """Save a message to conversation"""
        ...
    
    def get_messages(self, conv_id: str) -> List[Dict[str, str]]:
        """Get all messages in conversation"""
        ...
    
    def delete_conversation(self, conv_id: str) -> None:
        """Delete a conversation"""
        ...
    
    def list_conversations(self) -> List[str]:
        """List all conversation IDs"""
        ...


# ========== Memory Storage (Default) ==========

class MemoryStorage:
    """In-memory storage (ephemeral, lost on restart)"""
    
    def __init__(self):
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        logger.info("📦 MemoryStorage initialized")
    
    def save_message(self, conv_id: str, role: str, content: str) -> None:
        """Save message to memory"""
        if conv_id not in self.conversations:
            self.conversations[conv_id] = []
        
        self.conversations[conv_id].append({
            "role": role,
            "content": content
        })
    
    def get_messages(self, conv_id: str) -> List[Dict[str, str]]:
        """Get messages from memory"""
        return self.conversations.get(conv_id, [])
    
    def delete_conversation(self, conv_id: str) -> None:
        """Delete conversation from memory"""
        if conv_id in self.conversations:
            del self.conversations[conv_id]
    
    def list_conversations(self) -> List[str]:
        """List all conversation IDs"""
        return list(self.conversations.keys())


# ========== File Storage ==========

class FileStorage:
    """File-based storage (persistent, JSON file)"""
    
    def __init__(self, filepath: str = "./bifrost_conversations.json"):
        self.filepath = Path(filepath)
        self.data: Dict[str, List[Dict[str, str]]] = {}
        self._load()
        logger.info(f"💾 FileStorage initialized: {self.filepath}")
    
    def _load(self) -> None:
        """Load conversations from file"""
        if self.filepath.exists():
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info(f"📂 Loaded {len(self.data)} conversations from file")
            except Exception as e:
                logger.error(f"Failed to load conversations: {e}")
                self.data = {}
        else:
            self.data = {}
    
    def _save(self) -> None:
        """Save conversations to file"""
        try:
            # Create directory if needed
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save conversations: {e}")
    
    def save_message(self, conv_id: str, role: str, content: str) -> None:
        """Save message to file"""
        if conv_id not in self.data:
            self.data[conv_id] = []
        
        self.data[conv_id].append({
            "role": role,
            "content": content
        })
        
        self._save()
    
    def get_messages(self, conv_id: str) -> List[Dict[str, str]]:
        """Get messages from file"""
        return self.data.get(conv_id, [])
    
    def delete_conversation(self, conv_id: str) -> None:
        """Delete conversation from file"""
        if conv_id in self.data:
            del self.data[conv_id]
            self._save()
    
    def list_conversations(self) -> List[str]:
        """List all conversation IDs"""
        return list(self.data.keys())


# ========== Redis Storage ==========

class RedisStorage:
    """Redis-based storage (distributed, fast)"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        try:
            import redis
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
            logger.info(f"🔴 RedisStorage initialized: {redis_url}")
        except ImportError:
            raise ImportError("redis package required. Install: pip install redis")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    def save_message(self, conv_id: str, role: str, content: str) -> None:
        """Save message to Redis"""
        key = f"bifrost:conv:{conv_id}"
        message = json.dumps({"role": role, "content": content})
        self.redis.rpush(key, message)
        
        # Auto-expire after 30 days
        self.redis.expire(key, 30 * 24 * 60 * 60)
    
    def get_messages(self, conv_id: str) -> List[Dict[str, str]]:
        """Get messages from Redis"""
        key = f"bifrost:conv:{conv_id}"
        messages = self.redis.lrange(key, 0, -1)
        return [json.loads(msg) for msg in messages]
    
    def delete_conversation(self, conv_id: str) -> None:
        """Delete conversation from Redis"""
        key = f"bifrost:conv:{conv_id}"
        self.redis.delete(key)
    
    def list_conversations(self) -> List[str]:
        """List all conversation IDs"""
        keys = self.redis.keys("bifrost:conv:*")
        return [key.split(":")[-1] for key in keys]


# ========== PostgreSQL Storage ==========

class PostgreSQLStorage:
    """PostgreSQL-based storage (enterprise, reliable)"""
    
    def __init__(self, connection_string: str):
        try:
            import psycopg2
            from psycopg2 import sql
            
            self.conn = psycopg2.connect(connection_string)
            self._init_schema()
            logger.info("🐘 PostgreSQLStorage initialized")
        except ImportError:
            raise ImportError("psycopg2 required. Install: pip install psycopg2-binary")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")
    
    def _init_schema(self) -> None:
        """Create tables if they don't exist"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bifrost_messages (
                id SERIAL PRIMARY KEY,
                conversation_id VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bifrost_conv_id 
            ON bifrost_messages(conversation_id)
        """)
        
        self.conn.commit()
        cursor.close()
    
    def save_message(self, conv_id: str, role: str, content: str) -> None:
        """Save message to PostgreSQL"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO bifrost_messages (conversation_id, role, content) VALUES (%s, %s, %s)",
            (conv_id, role, content)
        )
        self.conn.commit()
        cursor.close()
    
    def get_messages(self, conv_id: str) -> List[Dict[str, str]]:
        """Get messages from PostgreSQL"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT role, content FROM bifrost_messages WHERE conversation_id = %s ORDER BY created_at ASC",
            (conv_id,)
        )
        
        messages = [
            {"role": row[0], "content": row[1]}
            for row in cursor.fetchall()
        ]
        cursor.close()
        return messages
    
    def delete_conversation(self, conv_id: str) -> None:
        """Delete conversation from PostgreSQL"""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM bifrost_messages WHERE conversation_id = %s",
            (conv_id,)
        )
        self.conn.commit()
        cursor.close()
    
    def list_conversations(self) -> List[str]:
        """List all conversation IDs"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT DISTINCT conversation_id FROM bifrost_messages ORDER BY MAX(created_at) DESC"
        )
        conversations = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return conversations
    
    def close(self) -> None:
        """Close database connection"""
        if self.conn:
            self.conn.close()


# ========== Storage Factory ==========

def create_storage(storage_config: str) -> StorageBackend:
    """
    Create storage backend from config string.
    
    Examples:
        "memory" -> MemoryStorage()
        "file://conversations.json" -> FileStorage("conversations.json")
        "redis://localhost:6379" -> RedisStorage("redis://localhost:6379")
        "postgresql://user:pass@localhost/db" -> PostgreSQLStorage("...")
    """
    if storage_config == "memory":
        return MemoryStorage()
    
    elif storage_config.startswith("file://"):
        filepath = storage_config[7:]  # Remove "file://"
        return FileStorage(filepath)
    
    elif storage_config.startswith("redis://"):
        return RedisStorage(storage_config)
    
    elif storage_config.startswith("postgresql://") or storage_config.startswith("postgres://"):
        return PostgreSQLStorage(storage_config)
    
    else:
        raise ValueError(
            f"Unknown storage type: {storage_config}\n"
            f"Supported: memory, file://path, redis://url, postgresql://url"
        )