"""
Day 3 Complete Integration Test
Tests vector store, graph store, embeddings, and memory controller.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Add backend to path
sys.path.append('backend')

load_dotenv()

print("=" * 60)
print("NIRE Day 3 - Memory System Complete Test")
print("=" * 60)
print()


async def test_embeddings():
    """Test embedding generation."""
    print("--- Test 1: Embeddings ---")
    
    try:
        from memory.embeddings import EmbeddingGenerator
        
        embedder = EmbeddingGenerator()
        
        # Test single embedding
        text = "I like coffee"
        embedding = await embedder.encode(text)
        
        print(f"✓ Embedding generated")
        print(f"✓ Dimension: {len(embedding)}")
        print(f"✓ First 5 values: {embedding[:5]}")
        
        # Test batch
        texts = ["I like tea", "I prefer water", "Coffee is great"]
        embeddings = await embedder.encode_batch(texts)
        
        print(f"✓ Batch embeddings: {len(embeddings)} generated")
        
        return True
        
    except Exception as e:
        print(f"✗ Embeddings failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_vector_store():
    """Test vector store operations."""
    print("\n--- Test 2: Vector Store ---")
    
    try:
        from memory.vector_store import VectorStore
        from memory.embeddings import EmbeddingGenerator
        
        vector_store = VectorStore()
        embedder = EmbeddingGenerator()
        
        # Test add memory
        text = "I prefer dark roast coffee"
        embedding = await embedder.encode(text)
        
        memory_id = await vector_store.add_memory(
            text=text,
            embedding=embedding,
            metadata={"category": "preference", "test": True}
        )
        
        print(f"✓ Memory stored: {memory_id}")
        
        # Test search
        query_text = "coffee preferences"
        query_embedding = await embedder.encode(query_text)
        
        results = await vector_store.search_similar(
            query_embedding=query_embedding,
            k=5
        )
        
        print(f"✓ Search completed: {len(results)} results")
        
        if results:
            print(f"✓ Top result: {results[0]['content'][:50]}...")
            print(f"✓ Similarity: {results[0]['similarity']:.3f}")
        
        # Test get memory
        retrieved = await vector_store.get_memory(memory_id)
        
        if retrieved:
            print(f"✓ Memory retrieved by ID")
        
        # Test statistics
        stats = vector_store.get_statistics()
        print(f"✓ Total memories: {stats['total_memories']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Vector store failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_graph_store():
    """Test graph store operations."""
    print("\n--- Test 3: Graph Store ---")
    
    try:
        from memory.graph_store import GraphStore
        
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )
        
        graph_store = GraphStore(driver)
        
        # Test create entity
        entity_id = await graph_store.create_entity(
            name="Coffee",
            entity_type="thing",
            properties={"category": "beverage"}
        )
        
        print(f"✓ Entity created: {entity_id}")
        
        # Test create fact
        fact_id = await graph_store.create_fact(
            user_id="user_001",
            content="User prefers dark roast coffee",
            category="preference",
            confidence=0.9
        )
        
        print(f"✓ Fact created: {fact_id}")
        
        # Link fact to entity
        linked = await graph_store.link_fact_to_entity(
            fact_id=fact_id,
            entity_name="Coffee"
        )
        
        if linked:
            print(f"✓ Fact linked to entity")
        
        # Test get facts
        facts = await graph_store.get_facts(
            user_id="user_001",
            limit=10
        )
        
        print(f"✓ Facts retrieved: {len(facts)}")
        
        # Test preferences
        pref_id = await graph_store.create_preference(
            user_id="user_001",
            key="coffee_type",
            value="dark roast",
            strength=0.9
        )
        
        print(f"✓ Preference created: {pref_id}")
        
        prefs = await graph_store.get_preferences(user_id="user_001")
        print(f"✓ Preferences retrieved: {len(prefs)}")
        
        # Test statistics
        stats = graph_store.get_statistics("user_001")
        print(f"✓ Graph stats: {stats}")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"✗ Graph store failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_memory_controller():
    """Test memory controller integration."""
    print("\n--- Test 4: Memory Controller ---")
    
    try:
        from memory.memory_controller import MemoryController
        
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )
        
        controller = MemoryController(driver, user_id="user_001")
        
        # Test conversation processing
        stored = await controller.process_conversation(
            user_message="I really love espresso coffee",
            assistant_response="Great! I'll remember you love espresso."
        )
        
        print(f"✓ Conversation processed")
        print(f"✓ Vector IDs: {len(stored['vector_ids'])}")
        print(f"✓ Fact IDs: {len(stored['fact_ids'])}")
        
        # Test context retrieval
        context = await controller.retrieve_context(
            query="What coffee do I like?",
            k=5,
            check_rules=True
        )
        
        print(f"✓ Context retrieved")
        print(f"✓ Has conflicts: {context['has_conflicts']}")
        print(f"✓ Memories found: {len(context['memories'])}")
        print(f"✓ Active rules: {len(context['active_rules'])}")
        
        if context['memories']:
            print(f"✓ Top memory: {context['memories'][0]['content'][:50]}...")
        
        # Test statistics
        stats = controller.get_statistics()
        print(f"✓ Statistics retrieved:")
        print(f"  - Vector memories: {stats['vector_store']['total_memories']}")
        print(f"  - Graph facts: {stats['graph_store']['facts']}")
        print(f"  - User rules: {stats['user_rules']['total_rules']}")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"✗ Memory controller failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_unrestricted_integration():
    """Test integration with unrestricted prompt system."""
    print("\n--- Test 5: Unrestricted Integration ---")
    
    try:
        from memory.memory_controller import MemoryController
        from core.unrestricted_prompts import UnrestrictedPromptTemplates
        
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )
        
        controller = MemoryController(driver, user_id="user_001")
        
        # Get context with rules
        context = await controller.retrieve_context(
            query="Test query for unrestricted mode",
            k=3,
            check_rules=True
        )
        
        # Generate unrestricted prompt
        prompt = UnrestrictedPromptTemplates.context_injection_unrestricted(
            user_message="Test message",
            retrieved_memories=context['memories'],
            user_preferences=context['preferences'],
            user_rules=context['active_rules'],
            conversation_history=[]
        )
        
        print(f"✓ Unrestricted prompt generated")
        print(f"✓ Prompt length: {len(prompt)} chars")
        
        # Check for key phrases
        checks = [
            ("NO built-in content restrictions" in prompt, "Uncensored declaration"),
            ("user-defined" in prompt.lower(), "User-defined rules"),
            ("unrestricted" in prompt.lower(), "Unrestricted mode")
        ]
        
        for check, desc in checks:
            status = "✓" if check else "✗"
            print(f"{status} Contains: {desc}")
        
        driver.close()
        return all(check for check, _ in checks)
        
    except Exception as e:
        print(f"✗ Unrestricted integration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    
    tests = [
        ("Embeddings", test_embeddings),
        ("Vector Store", test_vector_store),
        ("Graph Store", test_graph_store),
        ("Memory Controller", test_memory_controller),
        ("Unrestricted Integration", test_unrestricted_integration)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} crashed: {str(e)}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 60)
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("✓ Day 3 Complete - Memory System Operational!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed. Check errors above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
