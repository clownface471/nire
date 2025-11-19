"""
Vector Store Implementation for NIRE
Handles semantic memory storage and retrieval using ChromaDB.
"""

from typing import List, Dict, Optional, Tuple
import chromadb
from chromadb.config import Settings
from datetime import datetime
import structlog
import uuid

from backend.config import settings

logger = structlog.get_logger()


class VectorStore:
    """
    ChromaDB-based vector store for semantic memory.
    
    Responsibilities:
    - Store conversation memories as embeddings
    - Semantic similarity search
    - Metadata filtering
    - Memory persistence
    """
    
    def __init__(self):
        """Initialize ChromaDB persistent client."""
        logger.info("Initializing VectorStore")
        
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create main collection
        self.collection = self.client.get_or_create_collection(
            name="nire_memories",
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(
            "VectorStore initialized",
            collection=self.collection.name,
            count=self.collection.count()
        )
    
    async def add_memory(
        self,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict] = None,
        memory_id: Optional[str] = None
    ) -> str:
        """
        Store a memory with its embedding.
        
        Args:
            text: The actual text content
            embedding: Vector representation (from embedding model)
            metadata: Additional metadata (timestamp, category, etc.)
            memory_id: Optional custom ID (generated if not provided)
            
        Returns:
            memory_id of stored memory
        """
        
        if memory_id is None:
            memory_id = f"mem_{uuid.uuid4().hex[:16]}"
        
        # Ensure metadata has required fields
        if metadata is None:
            metadata = {}
        
        metadata.setdefault("timestamp", datetime.now().isoformat())
        metadata.setdefault("category", "general")
        
        try:
            self.collection.add(
                documents=[text],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[memory_id]
            )
            
            logger.info(
                "Memory stored",
                memory_id=memory_id,
                category=metadata.get("category")
            )
            
            return memory_id
            
        except Exception as e:
            logger.error(
                "Failed to store memory",
                error=str(e),
                memory_id=memory_id
            )
            raise
    
    async def add_memories_batch(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None
    ) -> List[str]:
        """
        Store multiple memories in batch (more efficient).
        
        Args:
            texts: List of text contents
            embeddings: List of embeddings
            metadatas: List of metadata dicts
            
        Returns:
            List of memory_ids
        """
        
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        # Generate IDs
        memory_ids = [f"mem_{uuid.uuid4().hex[:16]}" for _ in texts]
        
        # Ensure all metadata has timestamp
        for metadata in metadatas:
            metadata.setdefault("timestamp", datetime.now().isoformat())
            metadata.setdefault("category", "general")
        
        try:
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=memory_ids
            )
            
            logger.info(
                "Batch memories stored",
                count=len(memory_ids)
            )
            
            return memory_ids
            
        except Exception as e:
            logger.error(
                "Failed to store batch memories",
                error=str(e),
                count=len(texts)
            )
            raise
    
    async def search_similar(
        self,
        query_embedding: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Find semantically similar memories.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of similar memories with scores
        """
        
        try:
            # Build query
            query_kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": k,
                "include": ["documents", "metadatas", "distances"]
            }
            
            # Add metadata filter if provided
            if filter_metadata:
                query_kwargs["where"] = filter_metadata
            
            results = self.collection.query(**query_kwargs)
            
            # Format results
            memories = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    memory = {
                        "id": results['ids'][0][i],
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i],
                        "similarity": 1 - results['distances'][0][i]  # Convert distance to similarity
                    }
                    memories.append(memory)
            
            logger.info(
                "Similarity search completed",
                results_found=len(memories),
                k=k
            )
            
            return memories
            
        except Exception as e:
            logger.error(
                "Similarity search failed",
                error=str(e),
                k=k
            )
            raise
    
    async def get_memory(self, memory_id: str) -> Optional[Dict]:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: ID of memory to retrieve
            
        Returns:
            Memory dict or None if not found
        """
        
        try:
            result = self.collection.get(
                ids=[memory_id],
                include=["documents", "metadatas", "embeddings"]
            )
            
            if result['ids'] and len(result['ids']) > 0:
                return {
                    "id": result['ids'][0],
                    "content": result['documents'][0],
                    "metadata": result['metadatas'][0],
                    "embedding": result['embeddings'][0] if result['embeddings'] else None
                }
            
            return None
            
        except Exception as e:
            logger.error(
                "Failed to retrieve memory",
                error=str(e),
                memory_id=memory_id
            )
            return None
    
    async def update_memory(
        self,
        memory_id: str,
        text: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Update an existing memory.
        
        Args:
            memory_id: ID of memory to update
            text: New text (optional)
            embedding: New embedding (optional)
            metadata: New/updated metadata (optional)
            
        Returns:
            True if successful
        """
        
        try:
            # Get existing memory
            existing = await self.get_memory(memory_id)
            
            if not existing:
                logger.warning("Memory not found for update", memory_id=memory_id)
                return False
            
            # Prepare update
            update_kwargs = {"ids": [memory_id]}
            
            if text is not None:
                update_kwargs["documents"] = [text]
            
            if embedding is not None:
                update_kwargs["embeddings"] = [embedding]
            
            if metadata is not None:
                # Merge with existing metadata
                updated_metadata = {**existing['metadata'], **metadata}
                updated_metadata["updated_at"] = datetime.now().isoformat()
                update_kwargs["metadatas"] = [updated_metadata]
            
            self.collection.update(**update_kwargs)
            
            logger.info("Memory updated", memory_id=memory_id)
            return True
            
        except Exception as e:
            logger.error(
                "Failed to update memory",
                error=str(e),
                memory_id=memory_id
            )
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            True if successful
        """
        
        try:
            self.collection.delete(ids=[memory_id])
            
            logger.info("Memory deleted", memory_id=memory_id)
            return True
            
        except Exception as e:
            logger.error(
                "Failed to delete memory",
                error=str(e),
                memory_id=memory_id
            )
            return False
    
    async def delete_memories_by_filter(
        self,
        filter_metadata: Dict
    ) -> int:
        """
        Delete multiple memories matching filter.
        
        Args:
            filter_metadata: Metadata filter
            
        Returns:
            Number of memories deleted
        """
        
        try:
            # Get IDs matching filter
            results = self.collection.get(
                where=filter_metadata,
                include=[]
            )
            
            ids_to_delete = results['ids']
            
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                
                logger.info(
                    "Batch deletion completed",
                    count=len(ids_to_delete)
                )
                
                return len(ids_to_delete)
            
            return 0
            
        except Exception as e:
            logger.error(
                "Failed to delete memories by filter",
                error=str(e)
            )
            raise
    
    async def get_memories_by_category(
        self,
        category: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Retrieve all memories of a specific category.
        
        Args:
            category: Category to filter by
            limit: Maximum number to return
            
        Returns:
            List of memories
        """
        
        try:
            results = self.collection.get(
                where={"category": category},
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            memories = []
            if results['ids']:
                for i in range(len(results['ids'])):
                    memory = {
                        "id": results['ids'][i],
                        "content": results['documents'][i],
                        "metadata": results['metadatas'][i]
                    }
                    memories.append(memory)
            
            logger.info(
                "Retrieved memories by category",
                category=category,
                count=len(memories)
            )
            
            return memories
            
        except Exception as e:
            logger.error(
                "Failed to retrieve memories by category",
                error=str(e),
                category=category
            )
            return []
    
    async def get_recent_memories(
        self,
        limit: int = 50,
        since: Optional[str] = None
    ) -> List[Dict]:
        """
        Get most recent memories.
        
        Args:
            limit: Number of memories to return
            since: ISO timestamp to filter from
            
        Returns:
            List of recent memories
        """
        
        try:
            # Build filter
            where_filter = {}
            if since:
                where_filter["timestamp"] = {"$gte": since}
            
            # Get memories
            results = self.collection.get(
                where=where_filter if where_filter else None,
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            memories = []
            if results['ids']:
                for i in range(len(results['ids'])):
                    memory = {
                        "id": results['ids'][i],
                        "content": results['documents'][i],
                        "metadata": results['metadatas'][i]
                    }
                    memories.append(memory)
            
            # Sort by timestamp (most recent first)
            memories.sort(
                key=lambda x: x['metadata'].get('timestamp', ''),
                reverse=True
            )
            
            logger.info(
                "Retrieved recent memories",
                count=len(memories),
                limit=limit
            )
            
            return memories
            
        except Exception as e:
            logger.error(
                "Failed to retrieve recent memories",
                error=str(e)
            )
            return []
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the vector store.
        
        Returns:
            Dict with statistics
        """
        
        total_count = self.collection.count()
        
        # Get category distribution
        all_memories = self.collection.get(
            limit=10000,  # Reasonable limit for stats
            include=["metadatas"]
        )
        
        categories = {}
        if all_memories['metadatas']:
            for metadata in all_memories['metadatas']:
                cat = metadata.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_memories": total_count,
            "categories": categories,
            "collection_name": self.collection.name
        }
    
    async def clear_all(self) -> bool:
        """
        Clear all memories (dangerous operation!).
        
        Returns:
            True if successful
        """
        
        try:
            # Delete collection and recreate
            self.client.delete_collection(self.collection.name)
            
            self.collection = self.client.create_collection(
                name="nire_memories",
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.warning("All memories cleared")
            return True
            
        except Exception as e:
            logger.error("Failed to clear memories", error=str(e))
            return False
