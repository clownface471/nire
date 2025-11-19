"""
Graph Store Implementation for NIRE
Handles knowledge graph operations using Neo4j.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
from neo4j import GraphDatabase
import structlog
import uuid
import json

logger = structlog.get_logger()


class GraphStore:
    """
    Neo4j-based knowledge graph for relational memory.
    
    Responsibilities:
    - Entity and relationship management
    - Fact storage with provenance
    - Context-aware queries
    - Conflict resolution
    """
    
    def __init__(self, driver):
        """
        Initialize graph store with Neo4j driver.
        
        Args:
            driver: Neo4j driver instance
        """
        self.driver = driver
        logger.info("GraphStore initialized")
    
    # ===== ENTITY OPERATIONS =====
    
    async def create_entity(
        self,
        name: str,
        entity_type: str,
        properties: Optional[Dict] = None
    ) -> str:
        """
        Create or update an entity node.
        
        Args:
            name: Entity name
            entity_type: Type (person, place, thing, concept, event)
            properties: Additional properties
            
        Returns:
            entity_id
        """
        
        entity_id = f"ent_{uuid.uuid4().hex[:16]}"
        
        if properties is None:
            properties = {}
        
        with self.driver.session() as session:
            result = session.run("""
                MERGE (e:Entity {name: $name})
                ON CREATE SET 
                    e.id = $entity_id,
                    e.type = $entity_type,
                    e.first_mentioned = datetime(),
                    e.mention_count = 1
                ON MATCH SET
                    e.mention_count = e.mention_count + 1,
                    e.last_mentioned = datetime()
                SET e += $properties
                RETURN e.id as entity_id
            """,
                name=name,
                entity_id=entity_id,
                entity_type=entity_type,
                properties=properties
            )
            
            actual_id = result.single()["entity_id"]
            
            logger.info(
                "Entity created/updated",
                entity_id=actual_id,
                name=name,
                type=entity_type
            )
            
            return actual_id
    
    async def get_entity(self, name: str) -> Optional[Dict]:
        """
        Retrieve entity by name.
        
        Args:
            name: Entity name
            
        Returns:
            Entity dict or None
        """
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e:Entity {name: $name})
                RETURN e
            """, name=name)
            
            record = result.single()
            
            if record:
                return dict(record["e"])
            
            return None
    
    async def link_entities(
        self,
        entity1_name: str,
        entity2_name: str,
        relationship_type: str,
        properties: Optional[Dict] = None
    ) -> bool:
        """
        Create relationship between two entities.
        
        Args:
            entity1_name: First entity name
            entity2_name: Second entity name
            relationship_type: Type of relationship
            properties: Relationship properties
            
        Returns:
            True if successful
        """
        
        if properties is None:
            properties = {}
        
        properties["created_at"] = datetime.now().isoformat()
        
        with self.driver.session() as session:
            result = session.run(f"""
                MATCH (e1:Entity {{name: $entity1}})
                MATCH (e2:Entity {{name: $entity2}})
                MERGE (e1)-[r:{relationship_type}]->(e2)
                SET r += $properties
                RETURN id(r) as rel_id
            """,
                entity1=entity1_name,
                entity2=entity2_name,
                properties=properties
            )
            
            success = result.single() is not None
            
            if success:
                logger.info(
                    "Entities linked",
                    entity1=entity1_name,
                    entity2=entity2_name,
                    relationship=relationship_type
                )
            
            return success
    
    # ===== FACT OPERATIONS =====
    
    async def create_fact(
        self,
        user_id: str,
        content: str,
        category: str = "knowledge",
        confidence: float = 1.0,
        source: str = "explicit",
        context: Optional[str] = None
    ) -> str:
        """
        Create a fact node.
        
        Args:
            user_id: User ID
            content: Fact content
            category: Category (preference, knowledge, context, opinion)
            confidence: Confidence score (0.0-1.0)
            source: Source (explicit, implicit, inferred)
            context: Context ID if applicable
            
        Returns:
            fact_id
        """
        
        fact_id = f"fact_{uuid.uuid4().hex[:16]}"
        
        with self.driver.session() as session:
            query = """
                MATCH (u:User {id: $user_id})
                CREATE (f:Fact {
                    id: $fact_id,
                    content: $content,
                    category: $category,
                    confidence: $confidence,
                    source: $source,
                    created_at: datetime(),
                    updated_at: datetime(),
                    deprecated: false
                })
                CREATE (u)-[:KNOWS {certainty: $confidence, learned_at: datetime()}]->(f)
            """
            
            # Link to context if provided
            if context:
                query += """
                WITH f
                MATCH (ctx:Context {id: $context})
                CREATE (f)-[:OCCURRED_IN]->(ctx)
                """
            
            query += " RETURN f.id as fact_id"
            
            result = session.run(
                query,
                user_id=user_id,
                fact_id=fact_id,
                content=content,
                category=category,
                confidence=confidence,
                source=source,
                context=context
            )
            
            logger.info(
                "Fact created",
                fact_id=fact_id,
                category=category,
                confidence=confidence
            )
            
            record = result.single()
            if record:
                return record["fact_id"]
            return None
    
    async def link_fact_to_entity(
        self,
        fact_id: str,
        entity_name: str,
        relationship_type: str = "RELATES_TO"
    ) -> bool:
        """
        Link a fact to an entity.
        
        Args:
            fact_id: Fact ID
            entity_name: Entity name
            relationship_type: Relationship type
            
        Returns:
            True if successful
        """
        
        with self.driver.session() as session:
            result = session.run(f"""
                MATCH (f:Fact {{id: $fact_id}})
                MATCH (e:Entity {{name: $entity_name}})
                MERGE (f)-[r:{relationship_type}]->(e)
                RETURN id(r) as rel_id
            """,
                fact_id=fact_id,
                entity_name=entity_name
            )
            
            return result.single() is not None
    
    async def get_facts(
        self,
        user_id: str,
        category: Optional[str] = None,
        context: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 50
    ) -> List[Dict]:
        """
        Retrieve facts with filters.
        
        Args:
            user_id: User ID
            category: Filter by category
            context: Filter by context
            min_confidence: Minimum confidence threshold
            limit: Max results
            
        Returns:
            List of facts
        """
        
        with self.driver.session() as session:
            query = """
                MATCH (u:User {id: $user_id})-[:KNOWS]->(f:Fact)
                WHERE f.deprecated = false
                  AND f.confidence >= $min_confidence
            """
            
            params = {
                "user_id": user_id,
                "min_confidence": min_confidence,
                "limit": limit
            }
            
            if category:
                query += " AND f.category = $category"
                params["category"] = category
            
            if context:
                query += """
                    WITH f
                    MATCH (f)-[:OCCURRED_IN]->(ctx:Context {id: $context})
                """
                params["context"] = context
            
            query += """
                RETURN f
                ORDER BY f.updated_at DESC
                LIMIT $limit
            """
            
            result = session.run(query, **params)
            
            facts = [dict(record["f"]) for record in result]
            
            logger.info(
                "Facts retrieved",
                user_id=user_id,
                count=len(facts)
            )
            
            return facts
    
    # ===== CONFLICT RESOLUTION =====
    
    async def detect_contradictions(
        self,
        user_id: str,
        new_fact_content: str
    ) -> List[Dict]:
        """
        Detect facts that contradict a new fact.
        
        This is a simplified version - in production, use LLM for semantic comparison.
        
        Args:
            user_id: User ID
            new_fact_content: New fact to check
            
        Returns:
            List of potentially contradicting facts
        """
        
        # Simple keyword-based contradiction detection
        # In production, use LLM to determine semantic contradictions
        
        with self.driver.session() as session:
            # Get all existing facts
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:KNOWS]->(f:Fact)
                WHERE f.deprecated = false
                RETURN f
            """, user_id=user_id)
            
            existing_facts = [dict(record["f"]) for record in result]
        
        # Simple heuristic: check for negation keywords
        contradictions = []
        new_lower = new_fact_content.lower()
        
        negation_pairs = [
            ("like", "dislike"),
            ("love", "hate"),
            ("prefer", "avoid"),
            ("yes", "no"),
            ("true", "false")
        ]
        
        for fact in existing_facts:
            fact_lower = fact["content"].lower()
            
            # Check for direct negation pairs
            for pos, neg in negation_pairs:
                if (pos in new_lower and neg in fact_lower) or \
                   (neg in new_lower and pos in fact_lower):
                    contradictions.append(fact)
                    break
        
        if contradictions:
            logger.info(
                "Contradictions detected",
                count=len(contradictions)
            )
        
        return contradictions
    
    async def resolve_contradiction(
        self,
        old_fact_id: str,
        new_fact_id: str,
        resolution: str = "new_wins"
    ) -> bool:
        """
        Resolve contradiction between facts.
        
        Args:
            old_fact_id: Old fact ID
            new_fact_id: New fact ID
            resolution: "new_wins", "old_wins", or "coexist"
            
        Returns:
            True if successful
        """
        
        with self.driver.session() as session:
            if resolution == "new_wins":
                # Deprecate old fact
                session.run("""
                    MATCH (old:Fact {id: $old_id})
                    MATCH (new:Fact {id: $new_id})
                    SET old.deprecated = true
                    CREATE (new)-[:CONTRADICTS {
                        resolved: true,
                        resolution_date: datetime(),
                        winning_fact_id: $new_id
                    }]->(old)
                """, old_id=old_fact_id, new_id=new_fact_id)
                
            elif resolution == "old_wins":
                # Deprecate new fact
                session.run("""
                    MATCH (old:Fact {id: $old_id})
                    MATCH (new:Fact {id: $new_id})
                    SET new.deprecated = true
                    CREATE (old)-[:CONTRADICTS {
                        resolved: true,
                        resolution_date: datetime(),
                        winning_fact_id: $old_id
                    }]->(new)
                """, old_id=old_fact_id, new_id=new_fact_id)
                
            elif resolution == "coexist":
                # Mark as contradicting but both active
                session.run("""
                    MATCH (old:Fact {id: $old_id})
                    MATCH (new:Fact {id: $new_id})
                    CREATE (new)-[:CONTRADICTS {
                        resolved: false,
                        resolution_date: datetime()
                    }]->(old)
                """, old_id=old_fact_id, new_id=new_fact_id)
            
            logger.info(
                "Contradiction resolved",
                resolution=resolution,
                old_fact=old_fact_id,
                new_fact=new_fact_id
            )
            
            return True
    
    # ===== CONTEXT-AWARE RETRIEVAL =====
    
    async def get_relevant_context(
        self,
        user_id: str,
        query_entities: List[str],
        current_context: Optional[str] = None,
        max_hops: int = 2,
        limit: int = 10
    ) -> Dict:
        """
        Multi-hop graph traversal to find relevant context.
        
        Args:
            user_id: User ID
            query_entities: Entity names to start from
            current_context: Current context ID
            max_hops: Maximum traversal depth
            limit: Max results per query
            
        Returns:
            Dict with facts, entities, and relationships
        """
        
        with self.driver.session() as session:
            all_facts = []
            all_entities = []
            all_relationships = []
            
            for entity_name in query_entities:
                # Multi-hop traversal
                query = f"""
                    MATCH (e:Entity {{name: $entity_name}})
                    -[*1..{max_hops}]-(related)
                """
                
                if current_context:
                    query += """
                        -[:OCCURRED_IN]->(ctx:Context {id: $context})
                    """
                
                query += """
                    RETURN related, labels(related) as labels
                    LIMIT $limit
                """
                
                result = session.run(
                    query,
                    entity_name=entity_name,
                    context=current_context,
                    limit=limit
                )
                
                for record in result:
                    node = dict(record["related"])
                    labels = record["labels"]
                    
                    if "Fact" in labels:
                        all_facts.append(node)
                    elif "Entity" in labels:
                        all_entities.append(node)
        
        # Remove duplicates
        unique_facts = {f["id"]: f for f in all_facts}.values()
        unique_entities = {e.get("id", e.get("name")): e for e in all_entities}.values()
        
        result = {
            "facts": list(unique_facts),
            "entities": list(unique_entities),
            "total_results": len(unique_facts) + len(unique_entities)
        }
        
        logger.info(
            "Context retrieved",
            facts=len(unique_facts),
            entities=len(unique_entities)
        )
        
        return result
    
    # ===== PREFERENCE MANAGEMENT =====
    
    async def create_preference(
        self,
        user_id: str,
        key: str,
        value: str,
        strength: float = 1.0
    ) -> str:
        """
        Create or update a user preference.
        
        Args:
            user_id: User ID
            key: Preference key
            value: Preference value
            strength: Strength (0.0-1.0)
            
        Returns:
            preference_id
        """
        
        pref_id = f"pref_{uuid.uuid4().hex[:16]}"
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})
                MERGE (p:Preference {key: $key})
                ON CREATE SET
                    p.id = $pref_id,
                    p.value = $value,
                    p.strength = $strength,
                    p.confirmed = false,
                    p.last_confirmed = datetime()
                ON MATCH SET
                    p.value = $value,
                    p.strength = $strength,
                    p.last_confirmed = datetime()
                MERGE (u)-[r:HAS_PREFERENCE]->(p)
                ON CREATE SET r.since = datetime()
                ON MATCH SET r.strength = $strength
                RETURN p.id as pref_id
            """,
                user_id=user_id,
                pref_id=pref_id,
                key=key,
                value=value,
                strength=strength
            )
            
            actual_id = result.single()["pref_id"]
            
            logger.info(
                "Preference created/updated",
                key=key,
                value=value,
                strength=strength
            )
            
            return actual_id
    
    async def get_preferences(
        self,
        user_id: str,
        min_strength: float = 0.5
    ) -> Dict[str, str]:
        """
        Get user preferences.
        
        Args:
            user_id: User ID
            min_strength: Minimum strength threshold
            
        Returns:
            Dict of key-value preferences
        """
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})-[r:HAS_PREFERENCE]->(p:Preference)
                WHERE r.strength >= $min_strength
                RETURN p.key as key, p.value as value
                ORDER BY r.strength DESC
            """,
                user_id=user_id,
                min_strength=min_strength
            )
            
            preferences = {
                record["key"]: record["value"]
                for record in result
            }
            
            logger.info(
                "Preferences retrieved",
                count=len(preferences)
            )
            
            return preferences
    
    # ===== STATISTICS & UTILITIES =====
    
    def get_statistics(self, user_id: str) -> Dict:
        """
        Get graph statistics for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Statistics dict
        """
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})
                OPTIONAL MATCH (u)-[:KNOWS]->(f:Fact)
                OPTIONAL MATCH (u)-[:HAS_PREFERENCE]->(p:Preference)
                OPTIONAL MATCH (u)-[:HAS_RULE]->(r:UserRule)
                RETURN 
                    count(DISTINCT f) as fact_count,
                    count(DISTINCT p) as preference_count,
                    count(DISTINCT r) as rule_count
            """, user_id=user_id)
            
            record = result.single()
            
            return {
                "facts": record["fact_count"],
                "preferences": record["preference_count"],
                "rules": record["rule_count"]
            }
    
    async def export_graph(self, user_id: str) -> Dict:
        """
        Export user's entire graph for backup.
        
        Args:
            user_id: User ID
            
        Returns:
            Complete graph export
        """
        
        with self.driver.session() as session:
            # Export facts
            facts = session.run("""
                MATCH (u:User {id: $user_id})-[:KNOWS]->(f:Fact)
                RETURN f
            """, user_id=user_id)
            
            # Export preferences
            prefs = session.run("""
                MATCH (u:User {id: $user_id})-[:HAS_PREFERENCE]->(p:Preference)
                RETURN p
            """, user_id=user_id)
            
            # Export entities
            entities = session.run("""
                MATCH (u:User {id: $user_id})-[:KNOWS]->(f:Fact)-[:RELATES_TO]->(e:Entity)
                RETURN DISTINCT e
            """, user_id=user_id)
            
            export = {
                "user_id": user_id,
                "export_date": datetime.now().isoformat(),
                "facts": [dict(record["f"]) for record in facts],
                "preferences": [dict(record["p"]) for record in prefs],
                "entities": [dict(record["e"]) for record in entities]
            }
            
            logger.info(
                "Graph exported",
                facts=len(export["facts"]),
                preferences=len(export["preferences"]),
                entities=len(export["entities"])
            )
            
            return export
