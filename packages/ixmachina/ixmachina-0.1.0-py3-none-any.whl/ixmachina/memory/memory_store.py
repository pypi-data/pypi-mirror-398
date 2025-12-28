"""
Memory store with SQLite backend for objects and facts.
"""

from typing import Any, Optional, Dict, List, Tuple
from collections import deque
import sqlite3
import pickle
import json
import os

from .memory_object import MemoryObject
from .fact import Fact
from .embeddings import EmbeddingGenerator


class MemoryStore:
    """
    Storage system for objects and facts with relationships.
    
    Uses SQLite for persistent storage with support for:
    - Object storage with metadata and embeddings
    - Fact-based relationships with roles (n-ary relationships)
    - Graph traversal to find related objects
    - Semantic search using embeddings
    
    Args:
        database_path: Path to SQLite database file. If None, uses in-memory database.
        auto_embed: Whether to automatically generate embeddings when saving objects/facts.
        embedding_generator: Custom embedding generator. If None, uses default.
    """
    
    def __init__(
        self,
        database_path: Optional[str] = None,
        auto_embed: bool = True,
        embedding_generator: Optional[EmbeddingGenerator] = None,
    ):
        self.database_path = database_path or ':memory:'
        self.auto_embed = auto_embed
        self.embedding_generator = embedding_generator
        
        # If auto_embed is True but no generator provided, create one
        if self.auto_embed and self.embedding_generator is None:
            self.embedding_generator = EmbeddingGenerator()
        
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row  # Access columns by name
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Create tables and indexes if they don't exist."""
        cursor = self.connection.cursor()
        
        # Objects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS objects (
                object_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                value BLOB,
                object_type TEXT DEFAULT 'text',
                tags TEXT,
                metadata TEXT,
                embedding BLOB,
                name_embedding BLOB,
                created_at TEXT,
                updated_at TEXT,
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT
            )
        """)
        
        # Index on name for searching by name
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_objects_name 
            ON objects(name)
        """)
        
        # Facts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                fact_id TEXT PRIMARY KEY,
                text TEXT,
                relationship_type TEXT,
                metadata TEXT,
                embedding BLOB,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Fact-object associations with roles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fact_objects (
                fact_id TEXT,
                object_id TEXT,
                role TEXT,
                PRIMARY KEY (fact_id, object_id, role),
                FOREIGN KEY (fact_id) REFERENCES facts(fact_id) ON DELETE CASCADE,
                FOREIGN KEY (object_id) REFERENCES objects(object_id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for efficient queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fact_objects_object 
            ON fact_objects(object_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fact_objects_fact 
            ON fact_objects(fact_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_facts_type 
            ON facts(relationship_type)
        """)
        
        self.connection.commit()
    
    # ============================================================================
    # Object operations
    # ============================================================================
    
    def save_object(
        self,
        name: str,
        value: Any,
        description: str = "",
        object_id: Optional[str] = None,
        object_type: str = "text",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[list] = None,
        name_embedding: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Save an object to the store.
        
        If auto_embed is enabled and embeddings are not provided, they will be
        generated automatically for text objects:
        - Primary embedding: name + description combined
        - Name embedding: name only (if name is not empty)
        
        For number and date objects, embeddings are not used; similarity is based
        on distance.
        
        Args:
            name: Name for the object (not necessarily unique).
            value: The object to store.
            description: Human-readable description of the object.
            object_id: Optional unique identifier (auto-generated if not provided).
            object_type: Type of object ("text", "number", "date"). Defaults to "text".
            tags: Optional list of tags.
            metadata: Optional metadata dictionary.
            embedding: Optional primary embedding vector (name + description).
            name_embedding: Optional name-only embedding vector.
            
        Returns:
            Dictionary with success status and object_id.
        """
        try:
            # Auto-generate embeddings only for text objects
            if object_type == "text" and self.auto_embed and self.embedding_generator:
                if embedding is None:
                    embedding = self.embedding_generator.embed_object(
                        name=name,
                        description=description,
                    )
                
                if name_embedding is None and name:
                    name_embedding = self.embedding_generator.embed(text=name)
            
            memory_obj = MemoryObject(
                name=name,
                value=value,
                description=description,
                object_id=object_id,
                object_type=object_type,
                tags=tags,
                metadata=metadata,
                embedding=embedding,
                name_embedding=name_embedding,
            )
            
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO objects 
                (object_id, name, description, value, object_type, tags, metadata, embedding, 
                 name_embedding, created_at, updated_at, access_count, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_obj.object_id,
                memory_obj.name,
                memory_obj.description,
                pickle.dumps(memory_obj.value),
                memory_obj.object_type,
                json.dumps(memory_obj.tags),
                json.dumps(memory_obj.metadata),
                pickle.dumps(memory_obj.embedding) if memory_obj.embedding else None,
                pickle.dumps(memory_obj.name_embedding) if memory_obj.name_embedding else None,
                memory_obj.created_at.isoformat(),
                memory_obj.updated_at.isoformat(),
                memory_obj.access_count,
                memory_obj.last_accessed.isoformat() if memory_obj.last_accessed else None,
            ))
            
            self.connection.commit()
            
            return {
                'success': True,
                'object_id': memory_obj.object_id,
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def load_object(self, object_id: str) -> Dict[str, Any]:
        """
        Load an object from the store by ID.
        
        Args:
            object_id: ID of the object to load.
            
        Returns:
            Dictionary with success status and object data.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM objects WHERE object_id = ?
            """, (object_id,))
            
            row = cursor.fetchone()
            
            if row is None:
                return {
                    'success': False,
                    'error': f"Object with ID '{object_id}' not found",
                }
            
            # Reconstruct MemoryObject
            memory_obj = MemoryObject(
                name=row['name'],
                value=pickle.loads(row['value']),
                description=row['description'],
                object_id=row['object_id'],
                object_type=row['object_type'] if 'object_type' in row.keys() else 'text',  # Default to 'text' for backward compatibility
                tags=json.loads(row['tags']),
                metadata=json.loads(row['metadata']),
                embedding=pickle.loads(row['embedding']) if row['embedding'] else None,
                name_embedding=pickle.loads(row['name_embedding']) if row['name_embedding'] else None,
            )
            
            # Restore timestamps
            from datetime import datetime
            memory_obj.created_at = datetime.fromisoformat(row['created_at'])
            memory_obj.updated_at = datetime.fromisoformat(row['updated_at'])
            memory_obj.access_count = row['access_count']
            if row['last_accessed']:
                memory_obj.last_accessed = datetime.fromisoformat(row['last_accessed'])
            
            # Record access
            memory_obj.record_access()
            
            # Update access count in database
            cursor.execute("""
                UPDATE objects 
                SET access_count = ?, last_accessed = ?
                WHERE object_id = ?
            """, (
                memory_obj.access_count,
                memory_obj.last_accessed.isoformat(),
                object_id,
            ))
            self.connection.commit()
            
            return {
                'success': True,
                'object': memory_obj,
                'value': memory_obj.value,
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def delete_object(self, object_id: str) -> Dict[str, Any]:
        """
        Delete an object from the store.
        
        Args:
            object_id: ID of the object to delete.
            
        Returns:
            Dictionary with success status.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                DELETE FROM objects WHERE object_id = ?
            """, (object_id,))
            
            if cursor.rowcount == 0:
                return {
                    'success': False,
                    'error': f"Object with ID '{object_id}' not found",
                }
            
            self.connection.commit()
            
            return {
                'success': True,
                'object_id': object_id,
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def list_objects(self) -> Dict[str, Any]:
        """
        List all objects in the store with basic info.
        
        Returns:
            Dictionary with success status and list of objects (id, name, description, type).
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT object_id, name, description, object_type FROM objects")
            
            objects = [
                {
                    'object_id': row['object_id'],
                    'name': row['name'],
                    'description': row['description'],
                    'object_type': row['object_type'] if 'object_type' in row.keys() else 'text',
                }
                for row in cursor.fetchall()
            ]
            
            return {
                'success': True,
                'objects': objects,
                'count': len(objects),
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def find_objects_by_name(self, name: str) -> Dict[str, Any]:
        """
        Find all objects with a specific name.
        
        Args:
            name: Name to search for.
            
        Returns:
            Dictionary with success status and list of matching objects.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT object_id, name, description FROM objects
                WHERE name = ?
            """, (name,))
            
            objects = [
                {
                    'object_id': row['object_id'],
                    'name': row['name'],
                    'description': row['description'],
                }
                for row in cursor.fetchall()
            ]
            
            return {
                'success': True,
                'objects': objects,
                'count': len(objects),
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    # ============================================================================
    # Fact operations
    # ============================================================================
    
    def save_fact(
        self,
        text: str,
        relationship_type: str,
        objects: List[Dict[str, str]],
        fact_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Save a fact to the store.
        
        If auto_embed is enabled and embedding is not provided, it will be
        generated automatically from the fact text.
        
        Args:
            text: Natural language statement.
            relationship_type: Type of relationship.
            objects: List of {"object_id": str, "role": str} dictionaries.
            fact_id: Optional unique identifier.
            metadata: Optional metadata dictionary.
            embedding: Optional embedding vector.
            
        Returns:
            Dictionary with success status and fact_id.
        """
        try:
            # Auto-generate embedding if enabled and not provided
            if self.auto_embed and self.embedding_generator and embedding is None and text:
                embedding = self.embedding_generator.embed(text=text)
            
            fact = Fact(
                text=text,
                relationship_type=relationship_type,
                objects=objects,
                fact_id=fact_id,
                metadata=metadata,
                embedding=embedding,
            )
            
            cursor = self.connection.cursor()
            
            # Save fact
            cursor.execute("""
                INSERT OR REPLACE INTO facts 
                (fact_id, text, relationship_type, metadata, embedding, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                fact.fact_id,
                fact.text,
                fact.relationship_type,
                json.dumps(fact.metadata),
                pickle.dumps(fact.embedding) if fact.embedding else None,
                fact.created_at.isoformat(),
                fact.updated_at.isoformat(),
            ))
            
            # Delete old fact-object associations (for REPLACE)
            cursor.execute("""
                DELETE FROM fact_objects WHERE fact_id = ?
            """, (fact.fact_id,))
            
            # Save fact-object associations
            for obj in fact.objects:
                cursor.execute("""
                    INSERT INTO fact_objects (fact_id, object_id, role)
                    VALUES (?, ?, ?)
                """, (
                    fact.fact_id,
                    obj['object_id'],
                    obj['role'],
                ))
            
            self.connection.commit()
            
            return {
                'success': True,
                'fact_id': fact.fact_id,
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def load_fact(self, fact_id: str) -> Dict[str, Any]:
        """
        Load a fact from the store.
        
        Args:
            fact_id: ID of the fact to load.
            
        Returns:
            Dictionary with success status and fact data.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM facts WHERE fact_id = ?
            """, (fact_id,))
            
            row = cursor.fetchone()
            
            if row is None:
                return {
                    'success': False,
                    'error': f"Fact '{fact_id}' not found",
                }
            
            # Get associated objects
            cursor.execute("""
                SELECT object_id, role FROM fact_objects
                WHERE fact_id = ?
            """, (fact_id,))
            
            objects = [
                {'object_id': obj_row['object_id'], 'role': obj_row['role']}
                for obj_row in cursor.fetchall()
            ]
            
            # Reconstruct Fact
            fact = Fact(
                text=row['text'],
                relationship_type=row['relationship_type'],
                objects=objects,
                fact_id=row['fact_id'],
                metadata=json.loads(row['metadata']),
                embedding=pickle.loads(row['embedding']) if row['embedding'] else None,
            )
            
            # Restore timestamps
            from datetime import datetime
            fact.created_at = datetime.fromisoformat(row['created_at'])
            fact.updated_at = datetime.fromisoformat(row['updated_at'])
            
            return {
                'success': True,
                'fact': fact,
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def delete_fact(self, fact_id: str) -> Dict[str, Any]:
        """
        Delete a fact from the store.
        
        Args:
            fact_id: ID of the fact to delete.
            
        Returns:
            Dictionary with success status.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                DELETE FROM facts WHERE fact_id = ?
            """, (fact_id,))
            
            if cursor.rowcount == 0:
                return {
                    'success': False,
                    'error': f"Fact '{fact_id}' not found",
                }
            
            self.connection.commit()
            
            return {
                'success': True,
                'fact_id': fact_id,
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    # ============================================================================
    # Query operations
    # ============================================================================
    
    def find_facts_by_object(
        self,
        object_id: str,
        role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find all facts involving a specific object.
        
        Args:
            object_id: ID of the object.
            role: Optional role filter.
            
        Returns:
            Dictionary with success status and list of facts.
        """
        try:
            cursor = self.connection.cursor()
            
            if role:
                cursor.execute("""
                    SELECT DISTINCT f.fact_id 
                    FROM facts f
                    JOIN fact_objects fo ON f.fact_id = fo.fact_id
                    WHERE fo.object_id = ? AND fo.role = ?
                """, (object_id, role))
            else:
                cursor.execute("""
                    SELECT DISTINCT f.fact_id 
                    FROM facts f
                    JOIN fact_objects fo ON f.fact_id = fo.fact_id
                    WHERE fo.object_id = ?
                """, (object_id,))
            
            fact_ids = [row['fact_id'] for row in cursor.fetchall()]
            
            # Load each fact
            facts = []
            for fact_id in fact_ids:
                result = self.load_fact(fact_id=fact_id)
                if result['success']:
                    facts.append(result['fact'])
            
            return {
                'success': True,
                'facts': facts,
                'count': len(facts),
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def find_objects_by_fact(
        self,
        fact_id: str,
        role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find all objects in a specific fact.
        
        Args:
            fact_id: ID of the fact.
            role: Optional role filter.
            
        Returns:
            Dictionary with success status and list of objects with their info.
        """
        try:
            cursor = self.connection.cursor()
            
            if role:
                cursor.execute("""
                    SELECT fo.object_id, o.name, o.description, fo.role 
                    FROM fact_objects fo
                    JOIN objects o ON fo.object_id = o.object_id
                    WHERE fo.fact_id = ? AND fo.role = ?
                """, (fact_id, role))
            else:
                cursor.execute("""
                    SELECT fo.object_id, o.name, o.description, fo.role 
                    FROM fact_objects fo
                    JOIN objects o ON fo.object_id = o.object_id
                    WHERE fo.fact_id = ?
                """, (fact_id,))
            
            objects = [
                {
                    'object_id': row['object_id'],
                    'name': row['name'],
                    'description': row['description'],
                    'role': row['role'],
                }
                for row in cursor.fetchall()
            ]
            
            return {
                'success': True,
                'objects': objects,
                'count': len(objects),
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def find_facts_by_type(
        self,
        relationship_type: str,
    ) -> Dict[str, Any]:
        """
        Find all facts of a specific type.
        
        Args:
            relationship_type: Type of relationship to find.
            
        Returns:
            Dictionary with success status and list of facts.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT fact_id FROM facts
                WHERE relationship_type = ?
            """, (relationship_type,))
            
            fact_ids = [row['fact_id'] for row in cursor.fetchall()]
            
            # Load each fact
            facts = []
            for fact_id in fact_ids:
                result = self.load_fact(fact_id=fact_id)
                if result['success']:
                    facts.append(result['fact'])
            
            return {
                'success': True,
                'facts': facts,
                'count': len(facts),
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def find_objects_by_role(
        self,
        relationship_type: str,
        role: str,
    ) -> Dict[str, Any]:
        """
        Find all objects with a specific role in a relationship type.
        
        Example: Find all "employers" in "employment" relationships.
        
        Args:
            relationship_type: Type of relationship.
            role: Role to filter by.
            
        Returns:
            Dictionary with success status and list of objects with their info.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT DISTINCT fo.object_id, o.name, o.description
                FROM fact_objects fo
                JOIN facts f ON fo.fact_id = f.fact_id
                JOIN objects o ON fo.object_id = o.object_id
                WHERE f.relationship_type = ? AND fo.role = ?
            """, (relationship_type, role))
            
            objects = [
                {
                    'object_id': row['object_id'],
                    'name': row['name'],
                    'description': row['description'],
                }
                for row in cursor.fetchall()
            ]
            
            return {
                'success': True,
                'objects': objects,
                'count': len(objects),
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    # ============================================================================
    # Graph traversal
    # ============================================================================
    
    def traverse_relationships(
        self,
        start_object_id: str,
        depth_limit: int = 3,
        item_limit: int = 100,
        relationship_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Traverse relationships from a starting object using breadth-first search.
        
        Finds related objects by following facts, stopping at depth_limit or
        when item_limit related objects are found.
        
        Args:
            start_object_id: ID of the starting object.
            depth_limit: Maximum depth to traverse (default 3).
            item_limit: Maximum number of related objects to return (default 100).
            relationship_type: Optional filter for relationship type.
            
        Returns:
            Dictionary with success status and list of related objects with metadata.
            Each result includes: object_id, name, description, role, fact_id, depth.
        """
        try:
            visited_objects = {start_object_id}
            visited_facts = set()
            results = []
            
            # Queue: (object_id, current_depth)
            queue = deque([(start_object_id, 0)])
            
            cursor = self.connection.cursor()
            
            while queue and len(results) < item_limit:
                current_object_id, depth = queue.popleft()
                
                if depth >= depth_limit:
                    continue
                
                # Find facts involving this object
                if relationship_type:
                    cursor.execute("""
                        SELECT DISTINCT fo.fact_id, fo.role, f.relationship_type
                        FROM fact_objects fo
                        JOIN facts f ON fo.fact_id = f.fact_id
                        WHERE fo.object_id = ? AND f.relationship_type = ?
                    """, (current_object_id, relationship_type))
                else:
                    cursor.execute("""
                        SELECT DISTINCT fo.fact_id, fo.role, f.relationship_type
                        FROM fact_objects fo
                        JOIN facts f ON fo.fact_id = f.fact_id
                        WHERE fo.object_id = ?
                    """, (current_object_id,))
                
                fact_rows = cursor.fetchall()
                
                for fact_row in fact_rows:
                    fact_id = fact_row['fact_id']
                    
                    if fact_id in visited_facts:
                        continue
                    
                    visited_facts.add(fact_id)
                    
                    # Get all objects in this fact with their info
                    cursor.execute("""
                        SELECT fo.object_id, o.name, o.description, fo.role 
                        FROM fact_objects fo
                        JOIN objects o ON fo.object_id = o.object_id
                        WHERE fo.fact_id = ?
                    """, (fact_id,))
                    
                    for obj_row in cursor.fetchall():
                        obj_id = obj_row['object_id']
                        
                        if obj_id not in visited_objects:
                            visited_objects.add(obj_id)
                            queue.append((obj_id, depth + 1))
                            
                            results.append({
                                'object_id': obj_id,
                                'name': obj_row['name'],
                                'description': obj_row['description'],
                                'role': obj_row['role'],
                                'fact_id': fact_id,
                                'relationship_type': fact_row['relationship_type'],
                                'depth': depth + 1,
                            })
                            
                            if len(results) >= item_limit:
                                break
                    
                    if len(results) >= item_limit:
                        break
            
            return {
                'success': True,
                'start_object_id': start_object_id,
                'related_objects': results,
                'count': len(results),
                'depth_limit': depth_limit,
                'item_limit': item_limit,
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    # ============================================================================
    # Semantic search
    # ============================================================================
    
    def find_similar_by_query(
        self,
        query_value: Any,
        object_type: str = 'text',
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Find objects similar to a query value (without saving it first).
        
        Args:
            query_value: The value to search for (text, number, or date string).
            object_type: Type of object ('text', 'number', 'date').
            limit: Maximum number of similar objects to return.
            
        Returns:
            Dictionary with keys:
            - success: Whether the operation succeeded.
            - query_value: The original query value.
            - similar_objects: List of similar objects with similarity scores.
            - count: Number of similar objects returned.
            - error: Error message if operation failed (None if successful).
        """
        # Create a temporary MemoryObject for the query (without saving)
        temp_query_obj = MemoryObject(
            object_id='__temp_query__',
            name='__temp__',
            value=query_value,
            object_type=object_type,
        )
        
        # Auto-embed if needed
        if self.auto_embed and object_type == 'text':
            embedding = self.embedding_generator.embed(str(query_value))
            temp_query_obj.embedding = embedding
        
        # Route to appropriate similarity function
        if object_type == 'text':
            result = self._find_similar_text_objects(
                query_obj=temp_query_obj,
                limit=limit,
                exclude_self=False,  # No "self" to exclude for temp object
            )
        elif object_type == 'number':
            result = self._find_similar_number_objects(
                query_obj=temp_query_obj,
                limit=limit,
                exclude_self=False,
            )
        elif object_type == 'date':
            result = self._find_similar_date_objects(
                query_obj=temp_query_obj,
                limit=limit,
                exclude_self=False,
            )
        else:
            return {
                'success': False,
                'error': f"Unsupported object_type: {object_type}",
            }
        
        # Replace query_object_id with query_value in result
        if result.get('success'):
            result['query_value'] = query_value
            result.pop('query_object_id', None)
        
        return result
    
    def find_similar_objects(
        self,
        object_id: str,
        limit: int = 10,
        exclude_self: bool = True,
    ) -> Dict[str, Any]:
        """
        Find objects similar to a given object.
        
        Similarity method depends on object type:
        - text: cosine similarity between embeddings
        - number: distance-based (inverse of absolute difference)
        - date: distance-based (inverse of time difference)
        
        Args:
            object_id: ID of the query object.
            limit: Maximum number of similar objects to return.
            exclude_self: Whether to exclude the query object from results.
            
        Returns:
            Dictionary with success status and list of similar objects.
            Each result includes: object_id, name, description, object_type, similarity (0-1).
        """
        try:
            # Load the query object
            query_result = self.load_object(object_id=object_id)
            if not query_result['success']:
                return query_result
            
            query_obj = query_result['object']
            query_type = query_obj.object_type
            
            # Handle based on object type
            if query_type == "text":
                return self._find_similar_text_objects(
                    query_obj=query_obj,
                    limit=limit,
                    exclude_self=exclude_self,
                )
            elif query_type == "number":
                return self._find_similar_number_objects(
                    query_obj=query_obj,
                    limit=limit,
                    exclude_self=exclude_self,
                )
            elif query_type == "date":
                return self._find_similar_date_objects(
                    query_obj=query_obj,
                    limit=limit,
                    exclude_self=exclude_self,
                )
            else:
                return {
                    'success': False,
                    'error': f"Unknown object type: {query_type}",
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def _find_similar_text_objects(
        self,
        query_obj: MemoryObject,
        limit: int,
        exclude_self: bool,
    ) -> Dict[str, Any]:
        """Find similar text objects using embedding similarity."""
        if query_obj.embedding is None:
            return {
                'success': False,
                'error': f"Object '{query_obj.object_id}' has no embedding. Cannot find similar objects.",
            }
        
        query_embedding = query_obj.embedding
        
        # Get all text objects with embeddings
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT object_id, name, description, object_type, embedding
            FROM objects
            WHERE embedding IS NOT NULL AND object_type = 'text'
        """)
        
        # Calculate similarities
        similarities = []
        
        for row in cursor.fetchall():
            other_id = row['object_id']
            
            # Skip self if requested
            if exclude_self and other_id == query_obj.object_id:
                continue
            
            other_embedding = pickle.loads(row['embedding'])
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(
                embedding_a=query_embedding,
                embedding_b=other_embedding,
            )
            
            similarities.append({
                'object_id': other_id,
                'name': row['name'],
                'description': row['description'],
                'object_type': row['object_type'],
                'similarity': similarity,
            })
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Limit results
        similarities = similarities[:limit]
        
        return {
            'success': True,
            'query_object_id': query_obj.object_id,
            'similar_objects': similarities,
            'count': len(similarities),
        }
    
    def _find_similar_number_objects(
        self,
        query_obj: MemoryObject,
        limit: int,
        exclude_self: bool,
    ) -> Dict[str, Any]:
        """Find similar number objects using distance-based similarity."""
        try:
            query_value = float(query_obj.value)
        except (ValueError, TypeError):
            return {
                'success': False,
                'error': f"Object value is not a valid number: {query_obj.value}",
            }
        
        # Get all number objects
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT object_id, name, description, object_type, value
            FROM objects
            WHERE object_type = 'number'
        """)
        
        # Calculate similarities
        similarities = []
        distances = []
        
        for row in cursor.fetchall():
            other_id = row['object_id']
            
            # Skip self if requested
            if exclude_self and other_id == query_obj.object_id:
                continue
            
            try:
                other_value = float(pickle.loads(row['value']))
                distance = abs(query_value - other_value)
                distances.append(distance)
                
                similarities.append({
                    'object_id': other_id,
                    'name': row['name'],
                    'description': row['description'],
                    'object_type': row['object_type'],
                    'distance': distance,
                })
            except (ValueError, TypeError):
                # Skip objects with invalid number values
                continue
        
        if not similarities:
            return {
                'success': True,
                'query_object_id': query_obj.object_id,
                'similar_objects': [],
                'count': 0,
            }
        
        # Normalize distances to similarity scores (0-1)
        max_distance = max(distances) if distances else 1.0
        if max_distance == 0:
            max_distance = 1.0  # Avoid division by zero
        
        for item in similarities:
            # Similarity = 1 - (distance / max_distance)
            item['similarity'] = 1.0 - (item['distance'] / max_distance)
            del item['distance']  # Remove intermediate distance field
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Limit results
        similarities = similarities[:limit]
        
        return {
            'success': True,
            'query_object_id': query_obj.object_id,
            'similar_objects': similarities,
            'count': len(similarities),
        }
    
    def _find_similar_date_objects(
        self,
        query_obj: MemoryObject,
        limit: int,
        exclude_self: bool,
    ) -> Dict[str, Any]:
        """Find similar date objects using distance-based similarity."""
        from datetime import datetime
        
        # Parse query date (supports "YYYY", "YYYY-MM", "YYYY-MM-DD")
        query_date, query_granularity = self._parse_partial_date_with_granularity(query_obj.value)
        if query_date is None:
            return {
                'success': False,
                'error': f"Object value is not a valid date: {query_obj.value}",
            }
        
        # Get all date objects
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT object_id, name, description, object_type, value
            FROM objects
            WHERE object_type = 'date'
        """)
        
        # Calculate similarities
        similarities = []
        distances = []  # In days
        
        for row in cursor.fetchall():
            other_id = row['object_id']
            
            # Skip self if requested
            if exclude_self and other_id == query_obj.object_id:
                continue
            
            other_value = pickle.loads(row['value'])
            other_date, other_granularity = self._parse_partial_date_with_granularity(other_value)
            
            if other_date is None:
                continue
            
            # Calculate distance considering granularity
            distance = self._calculate_date_distance(
                query_date, query_granularity,
                other_date, other_granularity
            )
            distances.append(distance)
            
            similarities.append({
                'object_id': other_id,
                'name': row['name'],
                'description': row['description'],
                'object_type': row['object_type'],
                'distance': distance,
            })
        
        if not similarities:
            return {
                'success': True,
                'query_object_id': query_obj.object_id,
                'similar_objects': [],
                'count': 0,
            }
        
        # Normalize distances to similarity scores (0-1)
        max_distance = max(distances) if distances else 1.0
        if max_distance == 0:
            max_distance = 1.0  # Avoid division by zero
        
        for item in similarities:
            # Similarity = 1 - (distance / max_distance)
            item['similarity'] = 1.0 - (item['distance'] / max_distance)
            del item['distance']  # Remove intermediate distance field
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Limit results
        similarities = similarities[:limit]
        
        return {
            'success': True,
            'query_object_id': query_obj.object_id,
            'similar_objects': similarities,
            'count': len(similarities),
        }
    
    def _parse_partial_date(self, date_value: Any) -> Optional[Any]:
        """
        Parse a partial date (year, year-month, or full date).
        
        DEPRECATED: Use _parse_partial_date_with_granularity instead.
        This method is kept for backward compatibility.
        
        Args:
            date_value: Date string to parse.
            
        Returns:
            datetime object, or None if parsing fails.
        """
        result = self._parse_partial_date_with_granularity(date_value)
        return result[0] if result[0] is not None else None
    
    def _parse_partial_date_with_granularity(
        self,
        date_value: Any
    ) -> Tuple[Optional[Any], Optional[str]]:
        """
        Parse a partial date and return both the date and its granularity.
        
        Supports formats:
        - "YYYY" (year only) → middle of year (July 1st)
        - "YYYY-MM" (year and month) → middle of month (15th)
        - "YYYY-MM-DD" (full date) → exact date
        
        Args:
            date_value: Date string to parse.
            
        Returns:
            Tuple of (datetime object, granularity) where granularity is
            "year", "month", or "day". Returns (None, None) if parsing fails.
        """
        from datetime import datetime
        
        if not isinstance(date_value, str):
            date_value = str(date_value)
        
        date_value = date_value.strip()
        
        # Try full date
        try:
            dt = datetime.strptime(date_value, "%Y-%m-%d")
            return (dt, "day")
        except ValueError:
            pass
        
        # Try year-month (use middle of month: 15th)
        try:
            dt = datetime.strptime(date_value + "-15", "%Y-%m-%d")
            return (dt, "month")
        except ValueError:
            pass
        
        # Try year only (use middle of year: July 1st)
        try:
            dt = datetime.strptime(date_value + "-07-01", "%Y-%m-%d")
            return (dt, "year")
        except ValueError:
            pass
        
        return (None, None)
    
    def _calculate_date_distance(
        self,
        date1: Any,
        granularity1: str,
        date2: Any,
        granularity2: str,
    ) -> int:
        """
        Calculate distance between two dates considering their granularity.
        
        Rules:
        - If both dates are same year/month (based on coarser granularity), distance is 0
        - Otherwise, calculate day-based distance between the normalized dates
        
        Args:
            date1: First datetime object.
            granularity1: Granularity of first date ("year", "month", "day").
            date2: Second datetime object.
            granularity2: Granularity of second date ("year", "month", "day").
            
        Returns:
            Distance in days.
        """
        # Use the coarser granularity
        if granularity1 == "year" or granularity2 == "year":
            # If either is year-only, check if same year
            if date1.year == date2.year:
                return 0
        elif granularity1 == "month" or granularity2 == "month":
            # If either is month-only, check if same year-month
            if date1.year == date2.year and date1.month == date2.month:
                return 0
        
        # Calculate actual day distance
        return abs((date1 - date2).days)
    
    def _cosine_similarity(
        self,
        embedding_a: List[float],
        embedding_b: List[float],
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding_a: First embedding vector.
            embedding_b: Second embedding vector.
            
        Returns:
            Cosine similarity score (0-1, where 1 is identical).
        """
        import math
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(embedding_a, embedding_b))
        
        # Calculate magnitudes
        magnitude_a = math.sqrt(sum(a * a for a in embedding_a))
        magnitude_b = math.sqrt(sum(b * b for b in embedding_b))
        
        # Avoid division by zero
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = dot_product / (magnitude_a * magnitude_b)
        
        # Clamp to [0, 1] range (in case of floating point errors)
        return max(0.0, min(1.0, similarity))
    
    # ============================================================================
    # Utility methods
    # ============================================================================
    
    def close(self) -> None:
        """Close the database connection."""
        self.connection.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __repr__(self) -> str:
        return f"MemoryStore(database_path='{self.database_path}')"

