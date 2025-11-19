"""
Neo4j Schema Initialization for Unrestricted NIRE
Includes user rule system and memory structures.
"""

NEO4J_SCHEMA_INIT = """
-- ============================================================
-- NIRE Knowledge Graph Schema
-- Unrestricted Mode with User-Defined Rules
-- ============================================================

-- Node Constraints (Unique IDs)
-- ============================================================

CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;

CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT fact_id_unique IF NOT EXISTS
FOR (f:Fact) REQUIRE f.id IS UNIQUE;

CREATE CONSTRAINT preference_id_unique IF NOT EXISTS
FOR (p:Preference) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT conversation_id_unique IF NOT EXISTS
FOR (c:Conversation) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT context_id_unique IF NOT EXISTS
FOR (ctx:Context) REQUIRE ctx.id IS UNIQUE;

CREATE CONSTRAINT rule_id_unique IF NOT EXISTS
FOR (r:UserRule) REQUIRE r.rule_id IS UNIQUE;

-- Indexes for Performance
-- ============================================================

CREATE INDEX entity_name IF NOT EXISTS
FOR (e:Entity) ON (e.name);

CREATE INDEX fact_category IF NOT EXISTS
FOR (f:Fact) ON (f.category);

CREATE INDEX conversation_timestamp IF NOT EXISTS
FOR (c:Conversation) ON (c.started_at);

CREATE INDEX rule_priority IF NOT EXISTS
FOR (r:UserRule) ON (r.priority);

CREATE INDEX rule_context IF NOT EXISTS
FOR (r:UserRule) ON (r.context);

CREATE INDEX rule_active IF NOT EXISTS
FOR (r:UserRule) ON (r.active);

-- ============================================================
-- Initial User Setup
-- ============================================================

-- Create default user node
MERGE (u:User {
    id: 'user_001',
    name: 'Default User',
    created_at: datetime(),
    confidence_score: 0.5,
    total_interactions: 0,
    unrestricted_mode: true,
    transparency_enabled: true
})
RETURN u;

-- ============================================================
-- Sample User Rules (Optional - User can delete)
-- ============================================================

-- Rule 1: Privacy protection (suggested, not forced)
MATCH (u:User {id: 'user_001'})
CREATE (r1:UserRule {
    rule_id: 'rule_default_001',
    rule: 'Confirm before sharing personal information with external services',
    priority: 'high',
    context: 'all',
    active: true,
    user_defined: false,
    system_suggested: true,
    created_at: datetime(),
    updated_at: datetime(),
    metadata: '{\"rationale\": \"Privacy protection\", \"deletable\": true}'
})
CREATE (u)-[:HAS_RULE]->(r1);

-- Rule 2: System safety (suggested, not forced)
MATCH (u:User {id: 'user_001'})
CREATE (r2:UserRule {
    rule_id: 'rule_default_002',
    rule: 'Warn before executing system commands that modify files',
    priority: 'normal',
    context: 'all',
    active: true,
    user_defined: false,
    system_suggested: true,
    created_at: datetime(),
    updated_at: datetime(),
    metadata: '{\"rationale\": \"System integrity\", \"deletable\": true}'
})
CREATE (u)-[:HAS_RULE]->(r2);

-- ============================================================
-- Sample Context Nodes
-- ============================================================

MATCH (u:User {id: 'user_001'})
CREATE (ctx1:Context {
    id: 'ctx_work',
    scenario: 'work',
    active: false,
    indicators: '["office", "project", "meeting", "deadline"]',
    description: 'Professional work context'
})
CREATE (u)-[:HAS_CONTEXT]->(ctx1);

MATCH (u:User {id: 'user_001'})
CREATE (ctx2:Context {
    id: 'ctx_personal',
    scenario: 'personal',
    active: false,
    indicators: '["home", "family", "hobby", "relax"]',
    description: 'Personal life context'
})
CREATE (u)-[:HAS_CONTEXT]->(ctx2);

MATCH (u:User {id: 'user_001'})
CREATE (ctx3:Context {
    id: 'ctx_research',
    scenario: 'research',
    active: false,
    indicators: '["study", "learn", "research", "analyze"]',
    description: 'Research and learning context'
})
CREATE (u)-[:HAS_CONTEXT]->(ctx3);

-- ============================================================
-- Verification Queries
-- ============================================================

-- Check user exists
MATCH (u:User {id: 'user_001'})
RETURN u;

-- Check constraints
SHOW CONSTRAINTS;

-- Check indexes
SHOW INDEXES;

-- Check user rules
MATCH (u:User {id: 'user_001'})-[:HAS_RULE]->(r:UserRule)
RETURN r.rule_id, r.rule, r.priority, r.active, r.system_suggested
ORDER BY r.priority DESC;

-- Check contexts
MATCH (u:User {id: 'user_001'})-[:HAS_CONTEXT]->(ctx:Context)
RETURN ctx.id, ctx.scenario, ctx.description;
"""

# Python script to execute schema
def initialize_neo4j_schema(driver):
    """
    Execute Neo4j schema initialization.
    
    Args:
        driver: Neo4j driver instance
    """
    import structlog
    logger = structlog.get_logger()
    
    # Split by statements (simple approach)
    statements = [
        stmt.strip() 
        for stmt in NEO4J_SCHEMA_INIT.split(';')
        if stmt.strip() and not stmt.strip().startswith('--')
    ]
    
    with driver.session() as session:
        for i, statement in enumerate(statements, 1):
            try:
                # Skip comment blocks
                if '-- =' in statement:
                    continue
                
                # Execute statement
                result = session.run(statement)
                
                # Consume result to avoid warnings
                try:
                    result.consume()
                    logger.info(f"Executed schema statement {i}/{len(statements)}")
                except Exception:
                    # Some statements don't return results
                    pass
                    
            except Exception as e:
                logger.error(
                    f"Failed to execute statement {i}",
                    statement=statement[:100],
                    error=str(e)
                )
    
    logger.info("Neo4j schema initialization complete")


if __name__ == "__main__":
    # For standalone execution
    from neo4j import GraphDatabase
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )
    
    initialize_neo4j_schema(driver)
    driver.close()
    
    print("✓ Neo4j schema initialized successfully")
