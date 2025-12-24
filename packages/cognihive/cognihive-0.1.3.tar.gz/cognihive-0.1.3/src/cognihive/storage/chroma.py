"""
ChromaDB storage backend for CogniHive.

ChromaDB is the default vector database for storing and querying memories.
"""

from typing import Dict, List, Optional, Any
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from cognihive.storage.base import BaseStorage
from cognihive.core.memory_types import Memory, MemoryVisibility


class ChromaStorage(BaseStorage):
    """ChromaDB-based storage backend.
    
    Uses ChromaDB for vector similarity search and metadata filtering.
    Supports both in-memory and persistent storage.
    """
    
    def __init__(
        self,
        collection_name: str = "cognihive_memories",
        persist_directory: Optional[str] = None,
        embedding_function: Optional[Any] = None
    ):
        """Initialize ChromaDB storage.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Path for persistent storage (None = in-memory)
            embedding_function: Custom embedding function (uses default if None)
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "ChromaDB is required for ChromaStorage. "
                "Install with: pip install chromadb"
            )
        
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_function = embedding_function
        
        self._client: Optional[chromadb.Client] = None
        self._collection: Optional[chromadb.Collection] = None
    
    def initialize(self) -> None:
        """Initialize ChromaDB client and collection."""
        if self.persist_directory:
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self._client = chromadb.Client(
                Settings(anonymized_telemetry=False)
            )
        
        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "CogniHive memories"},
            embedding_function=self.embedding_function
        )
    
    @property
    def collection(self) -> "chromadb.Collection":
        """Get the ChromaDB collection, initializing if needed."""
        if self._collection is None:
            self.initialize()
        return self._collection
    
    def store_memory(self, memory: Memory) -> str:
        """Store a memory in ChromaDB."""
        # Prepare document and metadata
        document = memory.content
        
        metadata = {
            "owner_id": memory.owner_id,
            "owner_name": memory.owner_name,
            "confidence": memory.confidence,
            "importance": memory.importance,
            "visibility": memory.access_policy.visibility.value,
            "is_active": memory.is_active,
            "created_at": memory.created_at.isoformat(),
            "updated_at": memory.updated_at.isoformat(),
        }
        
        # Add topics and keywords as searchable metadata
        if memory.topics:
            metadata["topics"] = ",".join(memory.topics)
        if memory.keywords:
            metadata["keywords"] = ",".join(memory.keywords)
        
        # Store with or without pre-computed embedding
        if memory.embedding is not None:
            self.collection.add(
                ids=[memory.id],
                embeddings=[memory.embedding],
                documents=[document],
                metadatas=[metadata]
            )
        else:
            self.collection.add(
                ids=[memory.id],
                documents=[document],
                metadatas=[metadata]
            )
        
        return memory.id
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Retrieve a memory by ID."""
        try:
            result = self.collection.get(
                ids=[memory_id],
                include=["documents", "metadatas", "embeddings"]
            )
            
            if not result["ids"]:
                return None
            
            return self._result_to_memory(
                id=result["ids"][0],
                document=result["documents"][0] if result["documents"] else "",
                metadata=result["metadatas"][0] if result["metadatas"] else {},
                embedding=result["embeddings"][0] if result.get("embeddings") else None
            )
        except Exception:
            return None
    
    def query_memories(
        self,
        embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """Query memories by embedding similarity."""
        where_clause = self._build_where_clause(filters) if filters else None
        
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "embeddings", "distances"]
        )
        
        memories = []
        if results["ids"] and results["ids"][0]:
            for i, id in enumerate(results["ids"][0]):
                memory = self._result_to_memory(
                    id=id,
                    document=results["documents"][0][i] if results["documents"] else "",
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    embedding=results["embeddings"][0][i] if results.get("embeddings") else None
                )
                # Convert distance to similarity score (1 - distance for L2)
                distance = results["distances"][0][i] if results.get("distances") else 0
                similarity = 1.0 / (1.0 + distance)  # Convert to 0-1 similarity
                memories.append((memory, similarity))
        
        return memories
    
    def query_by_text(
        self,
        query_text: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """Query memories by text (ChromaDB will embed the query)."""
        where_clause = self._build_where_clause(filters) if filters else None
        
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "embeddings", "distances"]
        )
        
        memories = []
        if results["ids"] and results["ids"][0]:
            for i, id in enumerate(results["ids"][0]):
                memory = self._result_to_memory(
                    id=id,
                    document=results["documents"][0][i] if results["documents"] else "",
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    embedding=results["embeddings"][0][i] if results.get("embeddings") else None
                )
                distance = results["distances"][0][i] if results.get("distances") else 0
                similarity = 1.0 / (1.0 + distance)
                memories.append((memory, similarity))
        
        return memories
    
    def query_by_metadata(
        self,
        filters: Dict[str, Any],
        limit: int = 100
    ) -> List[Memory]:
        """Query memories by metadata only."""
        where_clause = self._build_where_clause(filters)
        
        results = self.collection.get(
            where=where_clause,
            limit=limit,
            include=["documents", "metadatas", "embeddings"]
        )
        
        memories = []
        for i, id in enumerate(results["ids"]):
            memory = self._result_to_memory(
                id=id,
                document=results["documents"][i] if results["documents"] else "",
                metadata=results["metadatas"][i] if results["metadatas"] else {},
                embedding=results["embeddings"][i] if results.get("embeddings") else None
            )
            memories.append(memory)
        
        return memories
    
    def update_memory(
        self,
        memory_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a memory's content or metadata."""
        try:
            existing = self.get_memory(memory_id)
            if not existing:
                return False
            
            # Prepare update payload
            update_kwargs = {"ids": [memory_id]}
            
            if "content" in updates:
                update_kwargs["documents"] = [updates["content"]]
            
            if "embedding" in updates:
                update_kwargs["embeddings"] = [updates["embedding"]]
            
            # Handle metadata updates
            metadata_updates = {k: v for k, v in updates.items() 
                              if k not in ["content", "embedding"]}
            if metadata_updates:
                # Get existing metadata and merge
                current_metadata = existing.to_dict()
                current_metadata.update(metadata_updates)
                update_kwargs["metadatas"] = [current_metadata]
            
            self.collection.update(**update_kwargs)
            return True
        except Exception:
            return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception:
            return False
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count memories matching filters."""
        if filters:
            where_clause = self._build_where_clause(filters)
            results = self.collection.get(where=where_clause)
            return len(results["ids"])
        return self.collection.count()
    
    def clear(self) -> None:
        """Clear all memories from storage."""
        # Delete and recreate collection
        if self._client:
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"description": "CogniHive memories"},
                embedding_function=self.embedding_function
            )
    
    def health_check(self) -> bool:
        """Check if ChromaDB is healthy."""
        try:
            self.collection.count()
            return True
        except Exception:
            return False
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict:
        """Build ChromaDB where clause from filters."""
        if not filters:
            return {}
        
        conditions = []
        for key, value in filters.items():
            if isinstance(value, list):
                conditions.append({key: {"$in": value}})
            elif isinstance(value, dict):
                # Already a condition
                conditions.append({key: value})
            else:
                conditions.append({key: {"$eq": value}})
        
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}
    
    def _result_to_memory(
        self,
        id: str,
        document: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> Memory:
        """Convert ChromaDB result to Memory object."""
        memory = Memory(
            id=id,
            content=document,
            embedding=embedding,
            owner_id=metadata.get("owner_id", ""),
            owner_name=metadata.get("owner_name", ""),
            confidence=metadata.get("confidence", 1.0),
            importance=metadata.get("importance", 0.5),
            is_active=metadata.get("is_active", True),
        )
        
        # Parse topics and keywords
        if "topics" in metadata and metadata["topics"]:
            memory.topics = metadata["topics"].split(",")
        if "keywords" in metadata and metadata["keywords"]:
            memory.keywords = metadata["keywords"].split(",")
        
        # Parse visibility
        if "visibility" in metadata:
            try:
                memory.access_policy.visibility = MemoryVisibility(metadata["visibility"])
            except ValueError:
                pass
        
        return memory
