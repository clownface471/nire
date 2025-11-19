"""
Day 2 Complete Integration Test
Tests all databases + unrestricted configuration
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import redis
import chromadb
import sys

load_dotenv()

print("=" * 60)
print("NIRE Day 2 - Complete System Test")
print("=" * 60)
print()

# Test 1: Neo4j Connection
print("--- Test 1: Neo4j ---")
try:
    neo_driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )
    
    with neo_driver.session() as session:
        result = session.run("MATCH (u:User) RETURN count(u) as user_count")
        user_count = result.single()["user_count"]
        print(f"✓ Neo4j connected")
        print(f"✓ User nodes: {user_count}")
        
        # Check rules
        result = session.run("""
            MATCH (u:User)-[:HAS_RULE]->(r:UserRule)
            WHERE r.active = true
            RETURN count(r) as rule_count
        """)
        rule_count = result.single()["rule_count"]
        print(f"✓ Active rules: {rule_count}")
    
    neo_driver.close()
    neo4j_ok = True
except Exception as e:
    print(f"✗ Neo4j failed: {str(e)}")
    neo4j_ok = False

print()

# Test 2: Redis Connection
print("--- Test 2: Redis ---")
try:
    r = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0))
    )
    
    # Test set/get
    r.set("nire_test", "unrestricted_mode_active")
    value = r.get("nire_test").decode('utf-8')
    r.delete("nire_test")
    
    print(f"✓ Redis connected")
    print(f"✓ Test value: {value}")
    redis_ok = True
except Exception as e:
    print(f"✗ Redis failed: {str(e)}")
    redis_ok = False

print()

# Test 3: ChromaDB
print("--- Test 3: ChromaDB ---")
try:
    chroma_client = chromadb.PersistentClient(
        path=os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma")
    )
    
    collection = chroma_client.get_or_create_collection("nire_memories")
    
    print(f"✓ ChromaDB connected")
    print(f"✓ Collection: {collection.name}")
    print(f"✓ Memory count: {collection.count()}")
    chromadb_ok = True
except Exception as e:
    print(f"✗ ChromaDB failed: {str(e)}")
    chromadb_ok = False

print()

# Test 4: User Rule System
print("--- Test 4: User Rule System ---")
try:
    # Add backend to path so we can import
    sys.path.append('backend')
    from memory.user_rule_system import UserRuleSystem
    
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )
    
    rule_system = UserRuleSystem(driver)
    stats = rule_system.get_rule_statistics("user_001")
    
    print(f"✓ Rule system initialized")
    print(f"✓ Total rules: {stats['total_rules']}")
    print(f"✓ Active rules: {stats['active_rules']}")
    
    driver.close()
    rules_ok = True
except Exception as e:
    print(f"✗ Rule system failed: {str(e)}")
    rules_ok = False

print()

# Test 5: Unrestricted Prompts
print("--- Test 5: Unrestricted Prompts ---")
try:
    # Add backend to path so we can import
    if 'backend' not in sys.path:
        sys.path.append('backend')
    from core.unrestricted_prompts import UnrestrictedPromptTemplates
    
    # Generate unrestricted prompt
    prompt = UnrestrictedPromptTemplates.base_system_prompt(
        user_name="Test User",
        user_rules=[
            {
                "rule": "Test rule",
                "priority": "normal",
                "context": "all"
            }
        ]
    )
    
    # Check for key phrases
    assert "NO built-in content restrictions" in prompt
    assert "unrestricted" in prompt.lower()
    assert "user-defined" in prompt.lower()
    
    print(f"✓ Unrestricted prompts working")
    print(f"✓ Prompt length: {len(prompt)} chars")
    print(f"✓ Contains uncensored declarations: Yes")
    prompts_ok = True
except Exception as e:
    print(f"✗ Prompts failed: {str(e)}")
    prompts_ok = False

print()

# Summary
print("=" * 60)
print("Summary:")
print("=" * 60)
results = [
    ("Neo4j", neo4j_ok),
    ("Redis", redis_ok),
    ("ChromaDB", chromadb_ok),
    ("User Rule System", rules_ok),
    ("Unrestricted Prompts", prompts_ok)
]

all_ok = True
for name, result in results:
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"{status}: {name}")
    if not all_ok:
        all_ok = False


print()
print("=" * 60)

if all_ok:
    print("✓ ALL TESTS PASSED!")
    print("✓ Day 2 Complete - Unrestricted NIRE Ready!")
    print("=" * 60)
else:
    print("✗ Some tests failed. Check errors above.")
    print("=" * 60)