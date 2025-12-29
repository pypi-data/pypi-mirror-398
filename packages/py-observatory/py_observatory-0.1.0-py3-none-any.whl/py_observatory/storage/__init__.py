"""Storage adapters for py-observatory."""

from .base import StorageProtocol
from .memory import MemoryStorage

__all__ = [
    "StorageProtocol",
    "MemoryStorage",
]

# Lazy imports for optional dependencies
def get_redis_storage():
    """Get RedisStorage class (requires redis package)."""
    from .redis import RedisStorage
    return RedisStorage

def get_file_storage():
    """Get FileStorage class (requires aiofiles package)."""
    from .file import FileStorage
    return FileStorage
