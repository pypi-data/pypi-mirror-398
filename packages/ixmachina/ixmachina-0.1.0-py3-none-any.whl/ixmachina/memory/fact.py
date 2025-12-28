"""
Fact class for representing relationships between objects.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class Fact:
    """
    Represents a fact that connects objects with roles.
    
    Facts are first-class entities that connect multiple objects together,
    where each object has a specific role in the relationship.
    
    Example:
        Fact(
            text="Oxygen combined with Carbon produces CO2",
            relationship_type="chemical_reaction",
            objects=[
                {"object_id": "uuid-1", "role": "reactant_1"},
                {"object_id": "uuid-2", "role": "reactant_2"},
                {"object_id": "uuid-3", "role": "product"}
            ]
        )
    
    Args:
        text: Natural language statement describing the fact.
        relationship_type: Structured type for queries (e.g., "employment", "chemical_reaction").
        objects: List of dictionaries with "object_id" and "role" keys.
        fact_id: Optional unique identifier (auto-generated if not provided).
        metadata: Optional additional metadata dictionary.
        embedding: Optional embedding vector for semantic search.
    """
    
    def __init__(
        self,
        text: str,
        relationship_type: str,
        objects: List[Dict[str, str]],
        fact_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[list] = None,
    ):
        self.fact_id = fact_id or str(uuid.uuid4())
        self.text = text
        self.relationship_type = relationship_type
        self.objects = objects  # List of {"object_id": str, "role": str}
        self.metadata = metadata or {}
        self.embedding = embedding
        
        # Auto-generated metadata
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # Validate objects format
        self._validate_objects()
    
    def _validate_objects(self) -> None:
        """
        Validate that objects list has correct format.
        
        Raises:
            ValueError: If objects format is invalid.
        """
        if not isinstance(self.objects, list):
            raise ValueError("objects must be a list")
        
        for obj in self.objects:
            if not isinstance(obj, dict):
                raise ValueError("Each object must be a dictionary")
            if 'object_id' not in obj or 'role' not in obj:
                raise ValueError("Each object must have 'object_id' and 'role' keys")
    
    def get_objects_by_role(self, role: str) -> List[str]:
        """
        Get all object IDs with a specific role.
        
        Args:
            role: The role to filter by.
            
        Returns:
            List of object IDs with that role.
        """
        return [
            obj['object_id']
            for obj in self.objects
            if obj['role'] == role
        ]
    
    def get_role_for_object(self, object_id: str) -> Optional[str]:
        """
        Get the role of a specific object in this fact.
        
        Args:
            object_id: ID of the object.
            
        Returns:
            Role of the object, or None if object not in fact.
        """
        for obj in self.objects:
            if obj['object_id'] == object_id:
                return obj['role']
        return None
    
    def has_object(self, object_id: str) -> bool:
        """
        Check if this fact involves a specific object.
        
        Args:
            object_id: ID of the object to check.
            
        Returns:
            True if object is involved in this fact.
        """
        return any(obj['object_id'] == object_id for obj in self.objects)
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Update the fact's metadata.
        
        Args:
            metadata: Metadata dictionary to merge with existing.
        """
        self.metadata.update(metadata)
        self.updated_at = datetime.now()
    
    def set_embedding(self, embedding: list) -> None:
        """
        Set the embedding vector.
        
        Args:
            embedding: Embedding vector for semantic search.
        """
        self.embedding = embedding
        self.updated_at = datetime.now()
    
    def get_embedding(self) -> Optional[list]:
        """
        Get the embedding vector.
        
        Returns:
            Embedding vector or None if not set.
        """
        return self.embedding
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation of the fact.
        """
        return {
            'fact_id': self.fact_id,
            'text': self.text,
            'relationship_type': self.relationship_type,
            'objects': self.objects,
            'metadata': self.metadata,
            'embedding': self.embedding,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Fact':
        """
        Create a Fact from a dictionary.
        
        Args:
            data: Dictionary containing fact data.
            
        Returns:
            New Fact instance.
        """
        fact = cls(
            text=data['text'],
            relationship_type=data['relationship_type'],
            objects=data['objects'],
            fact_id=data.get('fact_id'),
            metadata=data.get('metadata', {}),
            embedding=data.get('embedding'),
        )
        
        # Restore timestamps
        if 'created_at' in data:
            fact.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            fact.updated_at = datetime.fromisoformat(data['updated_at'])
        
        return fact
    
    def __repr__(self) -> str:
        object_summary = ', '.join(
            f"{obj['object_id'][:8]}...({obj['role']})"
            for obj in self.objects
        )
        return f"Fact(type='{self.relationship_type}', objects=[{object_summary}])"

