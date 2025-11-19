"""
Memory Controller for NIRE
Orchestrates hybrid memory (vector + graph) with user rule integration.
"""

from typing import List, Dict, Optional
import structlog
from datetime import datetime

from backend.memory.vector_store import VectorStore
from backend.memory.graph_store import GraphStore
from backend.memory.embeddings import EmbeddingGenerator
from backend.memory.user_rule_system import UserRuleSystem

logger = structlog.get_logger()


class MemoryController:
    """
    Hybrid memory controller combining vector and graph stores.
    
    Integrates with unrestricted NIRE through user rule system.
    """
    
    def __init__(
        self,
        neo4j_driver,
        user_id: str = "user_001"
    ):
        """
        Initialize memory controller.
        
        Args:
            neo4j_driver: Neo4j driver instance
            user_id: Default user ID
        """
        self.user_id = user_id
        
        # Initialize stores
        self.vector_store = VectorStore()
        self.graph_store = GraphStore(neo4j_driver)
        self.embedder = EmbeddingGenerator()
        self.rule_system = UserRuleSystem(neo4j_driver)
        
        logger.info(
            "MemoryController initialized",
            user_id=user_id
        )
    
    # ===== MEMORY STORAGE =====
    
    async def process_conversation(
        self,
        user_message: str,
        assistant_response: str,
        context: Optional[str] = None
    ) -> Dict:
        """
        Process conversation turn and store in memory.
        
        This is the main entry point for memory storage.
        
        Args:
            user_message: User's message
            assistant_response: Assistant's response
            context: Optional context ID
            
        Returns:
            Dict with stored memory IDs
        """
        
        logger.info("Processing conversation for memory storage")
        
        # 1. Extract facts from conversation
        facts = await self._extract_facts(user_message, assistant_response)
        
        # 2. Store in both vector and graph
        stored_memories = {
            "vector_ids": [],
            "fact_ids": [],
            "entity_ids": []
        }
        
        for fact in facts:
            # Generate embedding
            embedding = await self.embedder.encode(fact["content"])
            
            # Store in vector store
            vector_id = await self.vector_store.add_memory(
                text=fact["content"],
                embedding=embedding,
                metadata={
                    "category": fact["category"],
                    "confidence": fact["confidence"],
                    "source": "conversation",
                    "context": context if context is not None else "general"
                }
            )
            stored_memories["vector_ids"].append(vector_id)
            
            # Store in graph store
            fact_id = await self.graph_store.create_fact(
                user_id=self.user_id,
                content=fact["content"],
                category=fact["category"],
                confidence=fact["confidence"],
                source="conversation",
                context=context
            )
            stored_memories["fact_ids"].append(fact_id)
            
            # Extract and link entities
            if "entities" in fact:
                for entity in fact["entities"]:
                    entity_id = await self.graph_store.create_entity(
                        name=entity["name"],
                        entity_type=entity["type"]
                    )
                    stored_memories["entity_ids"].append(entity_id)
                    
                    # Link fact to entity
                    await self.graph_store.link_fact_to_entity(
                        fact_id=fact_id,
                        entity_name=entity["name"]
                    )
        
        logger.info(
            "Conversation processed",
            facts_stored=len(facts),
            entities_extracted=len(stored_memories["entity_ids"])
        )
        
        return stored_memories
    
    async def _extract_facts(
        self,
        user_message: str,
        assistant_response: str
    ) -> List[Dict]:
        """
        Extract facts from conversation.
        
        Simplified version for MVP - uses heuristics.
        In production, use LLM for better extraction.
        
        Args:
            user_message: User's message
            assistant_response: Assistant's response
            
        Returns:
            List of extracted facts
        """
        
        facts = []
        
        # Simple heuristic-based extraction
        # In production, use LLM with structured output
        
        # Check for preference statements
        preference_keywords = ["like", "prefer", "love", "hate", "dislike", "enjoy"]
        user_lower = user_message.lower()
        
        for keyword in preference_keywords:
            if keyword in user_lower:
                facts.append({
                    "content": user_message,
                    "category": "preference",
                    "confidence": 0.8,
                    "entities": []
                })
                break
        
        # Check for factual statements ("I am", "My name is", etc.)
        factual_keywords = ["i am", "my name is", "i work", "i live"]
        
        for keyword in factual_keywords:
            if keyword in user_lower:
                facts.append({
                    "content": user_message,
                    "category": "knowledge",
                    "confidence": 0.9,
                    "entities": []
                })
                break
        
        # If no specific pattern, store as general context
        if not facts:
            facts.append({
                "content": user_message,
                "category": "context",
                "confidence": 0.6,
                "entities": []
            })
        
        return facts
    
    # ===== MEMORY RETRIEVAL =====
    
    async def retrieve_context(
        self,
        query: str,
        k: int = 5,
        context: Optional[str] = None,
        check_rules: bool = True
    ) -> Dict:
        """
        Hybrid retrieval: Combine vector search + graph traversal.
        
        Integrates with user rule system for unrestricted mode.
        
        Args:
            query: Query text
            k: Number of results
            context: Optional context filter
            check_rules: Whether to check user rules
            
        Returns:
            Retrieved context with memories, facts, and user rules
        """
        
        logger.info("Retrieving context", query=query[:50])
        
        # 1. Check user rules if enabled
        active_rules = []
        if check_rules:
            active_rules = self.rule_system.get_active_rules(
                user_id=self.user_id,
                context=context
            )
            
            # Check for conflicts
            conflicts = self.rule_system.check_conflicts(
                user_id=self.user_id,
                user_request=query,
                context=context
            )
            
            if conflicts:
                logger.warning(
                    "User rule conflicts detected",
                    conflicts=len(conflicts)
                )
                # Return conflicts for user override decision
                return {
                    "has_conflicts": True,
                    "conflicts": conflicts,
                    "active_rules": active_rules
                }
        
        # 2. Vector search (semantic similarity)
        query_embedding = await self.embedder.encode(query)
        
        vector_results = await self.vector_store.search_similar(
            query_embedding=query_embedding,
            k=k,
            filter_metadata={"context": context} if context else None
        )
        
        # 3. Extract entities from query for graph search
        query_entities = self._extract_entity_names(query)
        
        # 4. Graph traversal (relational context)
        graph_results = {}
        if query_entities:
            graph_results = await self.graph_store.get_relevant_context(
                user_id=self.user_id,
                query_entities=query_entities,
                current_context=context,
                max_hops=2,
                limit=k
            )
        
        # 5. Get user preferences
        preferences = await self.graph_store.get_preferences(
            user_id=self.user_id,
            min_strength=0.5
        )
        
        # 6. Merge results
        context_data = {
            "has_conflicts": False,
            "memories": vector_results,
            "graph_facts": graph_results.get("facts", []),
            "graph_entities": graph_results.get("entities", []),
            "preferences": preferences,
            "active_rules": active_rules,
            "total_results": len(vector_results) + len(graph_results.get("facts", []))
        }
        
        logger.info(
            "Context retrieved",
            memories=len(vector_results),
            graph_facts=len(graph_results.get("facts", [])),
            preferences=len(preferences),
            rules=len(active_rules)
        )
        
        return context_data
    
    def _extract_entity_names(self, text: str) -> List[str]:
        """
        Extract potential entity names from text.
        
        Simplified version - in production use NER model.
        
        Args:
            text: Input text
            
        Returns:
            List of potential entity names
        """
        
        # Simple approach: extract capitalized words
        words = text.split()
        entities = []
        
        for word in words:
            # Remove punctuation
            word = word.strip(".,!?;:")
            
            # Check if capitalized (and not first word)
            if word and word[0].isupper() and len(word) > 2:
                entities.append(word)
        
        return entities
    
    # ===== PREFERENCE MANAGEMENT =====
    
    async def store_preference(
        self,
        key: str,
        value: str,
        strength: float = 1.0,
        explicit: bool = True
    ) -> str:
        """
        Store user preference.
        
        Args:
            key: Preference key
            value: Preference value
            strength: Strength (0.0-1.0)
            explicit: Whether explicitly stated
            
        Returns:
            preference_id
        """
        
        pref_id = await self.graph_store.create_preference(
            user_id=self.user_id,
            key=key,
            value=value,
            strength=strength
        )
        
        logger.info(
            "Preference stored",
            key=key,
            value=value,
            explicit=explicit
        )
        
        return pref_id
    
    async def get_all_preferences(self) -> Dict[str, str]:
        """
        Get all user preferences.
        
        Returns:
            Dict of preferences
        """
        
        return await self.graph_store.get_preferences(
            user_id=self.user_id,
            min_strength=0.5
        )
    
    # ===== STATISTICS & UTILITIES =====
    
    def get_statistics(self) -> Dict:
        """
        Get comprehensive memory statistics.
        
        Returns:
            Statistics dict
        """
        
        vector_stats = self.vector_store.get_statistics()
        graph_stats = self.graph_store.get_statistics(self.user_id)
        rule_stats = self.rule_system.get_rule_statistics(self.user_id)
        
        return {
            "vector_store": vector_stats,
            "graph_store": graph_stats,
            "user_rules": rule_stats,
            "embedding_dimension": self.embedder.get_dimension()
        }
    
    async def export_all_memories(self) -> Dict:
        """
        Export all memories for backup.
        
        Returns:
            Complete memory export
        """
        
        # Get recent vector memories
        vector_memories = await self.vector_store.get_recent_memories(limit=1000)
        
        # Get graph export
        graph_export = await self.graph_store.export_graph(self.user_id)
        
        # Get user rules
        user_rules = self.rule_system.export_rules(self.user_id)
        
        export = {
            "export_date": datetime.now().isoformat(),
            "user_id": self.user_id,
            "vector_memories": vector_memories,
            "graph_data": graph_export,
            "user_rules": user_rules,
            "statistics": self.get_statistics()
        }
        
        logger.info(
            "Complete memory export created",
            vector_count=len(vector_memories),
            graph_facts=len(graph_export.get("facts", [])),
            rules=len(user_rules)
        )
        
        return export
    
    async def clear_all_memories(self, confirm: bool = False) -> bool:
        """
        Clear all memories (dangerous operation!).
        
        Args:
            confirm: Must be True to proceed
            
        Returns:
            True if successful
        """
        
        if not confirm:
            logger.warning("Clear all memories called without confirmation")
            return False
        
        # Clear vector store
        vector_cleared = await self.vector_store.clear_all()
        
        # Note: Graph store clear would require CASCADE DELETE
        # For safety, we don't implement automatic graph clearing
        
        if vector_cleared:
            logger.warning("All vector memories cleared")
        
        return vector_cleared
