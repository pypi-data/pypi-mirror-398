"""
Abstract base class for storage backends.

All storage implementations (ChromaDB, Qdrant, etc.) must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from cognihive.core.memory_types import Memory


class BaseStorage(ABC):
    """Abstract base class for CogniHive storage backends.
    
    Implementers must provide methods for storing, querying,
    updating, and deleting memories.
    """
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the storage backend."""
        pass
    
    @abstractmethod
    def store_memory(self, memory: Memory) -> str:
        """Store a memory and return its ID.
        
        Args:
            memory: The Memory object to store
            
        Returns:
            The memory ID
        """
        pass
    
    @abstractmethod
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Retrieve a memory by ID.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            The Memory if found, None otherwise
        """
        pass
    
    @abstractmethod
    def query_memories(
        self,
        embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """Query memories by embedding similarity.
        
        Args:
            embedding: Query embedding vector
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of (Memory, similarity_score) tuples
        """
        pass
    
    @abstractmethod
    def query_by_metadata(
        self,
        filters: Dict[str, Any],
        limit: int = 100
    ) -> List[Memory]:
        """Query memories by metadata only.
        
        Args:
            filters: Metadata filter conditions
            limit: Maximum number of results
            
        Returns:
            List of matching memories
        """
        pass
    
    @abstractmethod
    def update_memory(
        self,
        memory_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a memory's content or metadata.
        
        Args:
            memory_id: The ID of the memory to update
            updates: Dictionary of fields to update
            
        Returns:
            True if update was successful
        """
        pass
    
    @abstractmethod
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Returns:
            True if deletion was successful
        """
        pass
    
    @abstractmethod
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count memories matching filters.
        
        Args:
            filters: Optional metadata filters
            
        Returns:
            Number of matching memories
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all memories from storage."""
        pass
    
    def health_check(self) -> bool:
        """Check if storage is healthy and accessible.
        
        Returns:
            True if storage is healthy
        """
        return True
