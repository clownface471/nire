"""
User Rule System for Unrestricted NIRE
Stores and manages user-defined behavioral rules in Knowledge Graph.
"""

from typing import List, Dict, Optional
from datetime import datetime
from neo4j import GraphDatabase
import structlog

logger = structlog.get_logger()


class UserRuleSystem:
    """
    Manages user-defined behavioral rules in Neo4j.
    
    Core Philosophy:
    - Users have absolute control over NIRE behavior
    - No hardcoded restrictions from developers
    - Complete transparency in rule application
    - Rules stored persistently in Knowledge Graph
    """
    
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Create necessary constraints and indexes for rule system."""
        with self.driver.session() as session:
            # Constraint: Unique rule IDs
            session.run("""
                CREATE CONSTRAINT rule_id_unique IF NOT EXISTS
                FOR (r:UserRule) REQUIRE r.rule_id IS UNIQUE
            """)
            
            # Index: Priority for fast filtering
            session.run("""
                CREATE INDEX rule_priority IF NOT EXISTS
                FOR (r:UserRule) ON (r.priority)
            """)
            
            # Index: Context for contextual filtering
            session.run("""
                CREATE INDEX rule_context IF NOT EXISTS
                FOR (r:UserRule) ON (r.context)
            """)
            
            logger.info("User rule schema initialized")
    
    def create_rule(
        self,
        user_id: str,
        rule_text: str,
        priority: str = "normal",
        context: str = "all",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a new user-defined behavioral rule.
        
        Args:
            user_id: User ID
            rule_text: Plain text description of the rule
            priority: 'critical', 'high', 'normal', 'low'
            context: When to apply ('all', 'work', 'personal', etc.)
            metadata: Additional rule metadata
            
        Returns:
            rule_id of created rule
        """
        
        rule_id = f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})
                CREATE (r:UserRule {
                    rule_id: $rule_id,
                    rule: $rule_text,
                    priority: $priority,
                    context: $context,
                    active: true,
                    user_defined: true,
                    created_at: datetime(),
                    updated_at: datetime(),
                    metadata: $metadata
                })
                CREATE (u)-[:HAS_RULE]->(r)
                RETURN r.rule_id as rule_id
            """, 
                user_id=user_id,
                rule_id=rule_id,
                rule_text=rule_text,
                priority=priority,
                context=context,
                metadata=metadata or {}
            )
            
            logger.info(
                "User rule created",
                rule_id=rule_id,
                user_id=user_id,
                priority=priority
            )
            
            return result.single()["rule_id"]
    
    def get_active_rules(
        self,
        user_id: str,
        context: Optional[str] = None,
        min_priority: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve active rules for a user.
        
        Args:
            user_id: User ID
            context: Filter by context (None = all contexts)
            min_priority: Minimum priority level
            
        Returns:
            List of active rules
        """
        
        # Priority hierarchy
        priority_order = {
            "critical": 4,
            "high": 3,
            "normal": 2,
            "low": 1
        }
        
        with self.driver.session() as session:
            # Build query based on filters
            query = """
                MATCH (u:User {id: $user_id})-[:HAS_RULE]->(r:UserRule)
                WHERE r.active = true
            """
            
            params = {"user_id": user_id}
            
            # Context filter
            if context:
                query += " AND (r.context = $context OR r.context = 'all')"
                params["context"] = context
            
            query += """
                RETURN r.rule_id as rule_id,
                       r.rule as rule,
                       r.priority as priority,
                       r.context as context,
                       r.created_at as created_at,
                       r.metadata as metadata
                ORDER BY r.priority DESC, r.created_at DESC
            """
            
            result = session.run(query, **params)
            
            rules = []
            for record in result:
                rule_dict = dict(record)
                
                # Filter by minimum priority if specified
                if min_priority:
                    if priority_order.get(rule_dict["priority"], 0) < priority_order.get(min_priority, 0):
                        continue
                
                rules.append(rule_dict)
            
            logger.info(
                "Retrieved active rules",
                user_id=user_id,
                count=len(rules),
                context=context
            )
            
            return rules
    
    def update_rule(
        self,
        rule_id: str,
        updates: Dict
    ) -> bool:
        """
        Update an existing rule.
        
        Args:
            rule_id: Rule to update
            updates: Dict of fields to update
            
        Returns:
            True if successful
        """
        
        allowed_fields = ["rule", "priority", "context", "active", "metadata"]
        
        # Filter out non-allowed fields
        safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        safe_updates["updated_at"] = datetime.now().isoformat()
        
        with self.driver.session() as session:
            # Build SET clause dynamically
            set_clauses = [f"r.{key} = ${key}" for key in safe_updates.keys()]
            set_clause = ", ".join(set_clauses)
            
            query = f"""
                MATCH (r:UserRule {{rule_id: $rule_id}})
                SET {set_clause}
                RETURN r.rule_id as rule_id
            """
            
            result = session.run(query, rule_id=rule_id, **safe_updates)
            
            success = result.single() is not None
            
            if success:
                logger.info("Rule updated", rule_id=rule_id, updates=safe_updates)
            else:
                logger.warning("Rule not found for update", rule_id=rule_id)
            
            return success
    
    def delete_rule(self, rule_id: str) -> bool:
        """
        Delete a rule (soft delete by deactivating).
        
        Args:
            rule_id: Rule to delete
            
        Returns:
            True if successful
        """
        
        return self.update_rule(rule_id, {"active": False})
    
    def check_conflicts(
        self,
        user_id: str,
        user_request: str,
        context: Optional[str] = None
    ) -> List[Dict]:
        """
        Check if user request conflicts with any active rules.
        
        This is where we detect rule violations and give user control.
        
        Args:
            user_id: User ID
            user_request: The user's request text
            context: Current context
            
        Returns:
            List of conflicting rules (empty if no conflicts)
        """
        
        # Get all active rules for this context
        rules = self.get_active_rules(user_id, context)
        
        conflicts = []
        
        # Simple keyword-based conflict detection
        # (In production, this would use LLM for semantic matching)
        for rule in rules:
            rule_text = rule["rule"].lower()
            request_lower = user_request.lower()
            
            # Extract "never" or "always" directives from rule
            if "never" in rule_text:
                # Extract what should never happen
                forbidden_keywords = self._extract_keywords(rule_text, "never")
                
                # Check if request contains forbidden keywords
                for keyword in forbidden_keywords:
                    if keyword in request_lower:
                        conflicts.append({
                            **rule,
                            "conflict_reason": f"Request contains forbidden keyword: '{keyword}'"
                        })
                        break
        
        if conflicts:
            logger.info(
                "Rule conflicts detected",
                user_id=user_id,
                conflict_count=len(conflicts)
            )
        
        return conflicts
    
    def _extract_keywords(self, rule_text: str, directive: str) -> List[str]:
        """
        Extract keywords from rule text.
        
        Simple implementation - can be enhanced with NLP.
        """
        
        # Very basic extraction
        # In production, use LLM or spaCy for proper parsing
        
        words = rule_text.lower().split()
        
        try:
            directive_index = words.index(directive)
            # Take next 3-5 words after directive
            keywords = words[directive_index + 1:directive_index + 6]
            # Remove common stop words
            stop_words = {"the", "a", "an", "in", "on", "at", "to", "for"}
            keywords = [w for w in keywords if w not in stop_words]
            return keywords
        except ValueError:
            return []
    
    def get_rule_statistics(self, user_id: str) -> Dict:
        """
        Get statistics about user's rule system.
        
        Useful for transparency and debugging.
        """
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:HAS_RULE]->(r:UserRule)
                RETURN 
                    count(r) as total_rules,
                    sum(CASE WHEN r.active = true THEN 1 ELSE 0 END) as active_rules,
                    collect(DISTINCT r.context) as contexts,
                    collect(DISTINCT r.priority) as priorities
            """, user_id=user_id)
            
            record = result.single()
            
            if record:
                return {
                    "total_rules": record["total_rules"],
                    "active_rules": record["active_rules"],
                    "contexts": record["contexts"],
                    "priorities": record["priorities"]
                }
            else:
                return {
                    "total_rules": 0,
                    "active_rules": 0,
                    "contexts": [],
                    "priorities": []
                }
    
    def export_rules(self, user_id: str) -> List[Dict]:
        """
        Export all rules for backup/portability.
        
        Gives users full ownership of their rule set.
        """
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:HAS_RULE]->(r:UserRule)
                RETURN r
                ORDER BY r.created_at
            """, user_id=user_id)
            
            rules = []
            for record in result:
                rule_node = record["r"]
                rules.append(dict(rule_node))
            
            logger.info(
                "Rules exported",
                user_id=user_id,
                count=len(rules)
            )
            
            return rules
    
    def import_rules(self, user_id: str, rules: List[Dict]) -> int:
        """
        Import rules from backup.
        
        Allows users to restore or transfer their rule set.
        """
        
        imported = 0
        
        for rule in rules:
            try:
                self.create_rule(
                    user_id=user_id,
                    rule_text=rule.get("rule"),
                    priority=rule.get("priority", "normal"),
                    context=rule.get("context", "all"),
                    metadata=rule.get("metadata", {})
                )
                imported += 1
            except Exception as e:
                logger.error(
                    "Failed to import rule",
                    rule=rule,
                    error=str(e)
                )
        
        logger.info(
            "Rules imported",
            user_id=user_id,
            imported=imported,
            total=len(rules)
        )
        
        return imported


# Default "starter rules" suggestion (optional, user can decline)
SUGGESTED_STARTER_RULES = [
    {
        "rule": "Never share my personal information (name, address, phone) with external services",
        "priority": "critical",
        "context": "all",
        "rationale": "Privacy protection"
    },
    {
        "rule": "Always confirm before executing system commands or file operations",
        "priority": "high",
        "context": "all",
        "rationale": "Safety for system integrity"
    },
    {
        "rule": "Warn me if a task will take more than 5 minutes to complete",
        "priority": "normal",
        "context": "all",
        "rationale": "Time management"
    }
]
