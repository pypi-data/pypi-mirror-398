"""
Memory object wrapper with metadata and embeddings.
"""

from typing import Any, Optional, Dict
from datetime import datetime
import json


class MemoryObject:
    """
    Wrapper class for objects stored in memory.
    
    Contains the object value along with metadata like timestamps, tags,
    access count, and embeddings for semantic search.
    
    Args:
        name: Name for this object (not necessarily unique).
        value: The actual object to store.
        description: Human-readable description of the object.
        object_id: Optional unique identifier (auto-generated if not provided).
        object_type: Type of object ("text", "number", "date"). Defaults to "text".
        tags: Optional list of tags for categorization.
        metadata: Optional additional metadata dictionary.
        embedding: Optional primary embedding (name + description combined).
        name_embedding: Optional specialized embedding for name-only search.
    """
    
    def __init__(
        self,
        name: str,
        value: Any,
        description: str = "",
        object_id: Optional[str] = None,
        object_type: str = "text",
        tags: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[list] = None,
        name_embedding: Optional[list] = None,
    ):
        import uuid
        
        self.object_id = object_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.value = value
        self.object_type = object_type  # "text", "number", or "date"
        self.tags = tags or []
        self.metadata = metadata or {}
        self.embedding = embedding  # Primary: name + description (for text type)
        self.name_embedding = name_embedding  # Specialized: name only (for text type)
        
        # Auto-generated metadata
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.access_count = 0
        self.last_accessed = None
    
    def update_metadata(
        self,
        tags: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update the object's metadata.
        
        Args:
            tags: New tags to add (appends to existing).
            metadata: Metadata dictionary to merge with existing.
        """
        if tags:
            self.tags.extend(tags)
        
        if metadata:
            self.metadata.update(metadata)
        
        self.updated_at = datetime.now()
    
    def record_access(self) -> None:
        """Record that this object was accessed."""
        self.access_count += 1
        self.last_accessed = datetime.now()
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get all metadata as a dictionary.
        
        Returns:
            Dictionary containing all metadata fields.
        """
        return {
            'object_id': self.object_id,
            'name': self.name,
            'description': self.description,
            'object_type': self.object_type,
            'tags': self.tags,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
        }
    
    def get_embedding(self) -> Optional[list]:
        """
        Get the primary embedding vector (name + description).
        
        Returns:
            Embedding vector or None if not set.
        """
        return self.embedding
    
    def set_embedding(
        self,
        embedding: list,
        name_embedding: Optional[list] = None,
    ) -> None:
        """
        Set the embedding vectors.
        
        Args:
            embedding: Primary embedding vector (name + description).
            name_embedding: Optional specialized embedding for name-only search.
        """
        self.embedding = embedding
        if name_embedding is not None:
            self.name_embedding = name_embedding
        self.updated_at = datetime.now()
    
    def get_name_embedding(self) -> Optional[list]:
        """
        Get the name-only embedding vector.
        
        Returns:
            Name embedding vector or None if not set.
        """
        return self.name_embedding
    
    def set_name_embedding(self, name_embedding: list) -> None:
        """
        Set the name-only embedding vector.
        
        Args:
            name_embedding: Embedding vector for name-only search.
        """
        self.name_embedding = name_embedding
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation of the object.
        """
        return {
            'object_id': self.object_id,
            'name': self.name,
            'description': self.description,
            'value': self.value,
            'object_type': self.object_type,
            'tags': self.tags,
            'metadata': self.metadata,
            'embedding': self.embedding,
            'name_embedding': self.name_embedding,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryObject':
        """
        Create a MemoryObject from a dictionary.
        
        Args:
            data: Dictionary containing object data.
            
        Returns:
            New MemoryObject instance.
        """
        obj = cls(
            name=data['name'],
            value=data['value'],
            description=data.get('description', ''),
            object_id=data.get('object_id'),
            object_type=data.get('object_type', 'text'),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            embedding=data.get('embedding'),
            name_embedding=data.get('name_embedding'),
        )
        
        # Restore timestamps
        if 'created_at' in data:
            obj.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            obj.updated_at = datetime.fromisoformat(data['updated_at'])
        if 'access_count' in data:
            obj.access_count = data['access_count']
        if data.get('last_accessed'):
            obj.last_accessed = datetime.fromisoformat(data['last_accessed'])
        
        return obj
    
    def __repr__(self) -> str:
        return f"MemoryObject(id='{self.object_id[:8]}...', name='{self.name}', tags={self.tags})"

