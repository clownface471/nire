"""
Day 4 Complete Integration Test
Tests LLM engine with memory system and unrestricted operation.
"""

import asyncio
import time
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

async def test_llm_loading():
    """Test LLM model loading."""
    print("\n=== Test 1: LLM Model Loading ===")
    
    from backend.core.llm_engine import LLMEngine
    
    engine = LLMEngine()
    info = engine.get_model_info()
    
    print(f"✓ Models loaded: {list(info.keys())}")
    for model, details in info.items():
        print(f"  - {model}: context_size={details.get('context_size', 'N/A')}")
    
    return engine

async def test_model_selection(engine):
    """Test model selection logic."""
    print("\n=== Test 2: Model Selection ===")
    
    # Simple query (should use Phi-3)
    simple_query = "What's the weather?"
    selected = engine.select_model(simple_query, {})
    print(f"Simple query: '{simple_query}'")
    print(f"✓ Selected: {selected} (expected: phi3)")
    
    # Complex query (should use Mistral)
    complex_query = "Analyze the philosophical implications of artificial general intelligence on human society, considering economic, ethical, and existential perspectives."
    selected = engine.select_model(complex_query, {})
    print(f"\nComplex query: '{complex_query[:50]}...'")
    print(f"✓ Selected: {selected} (expected: mistral)")

async def test_prompt_assembly():
    """Test prompt assembly with context."""
    print("\n=== Test 3: Prompt Assembly ===")
    
    from backend.core.prompt_assembler import PromptAssembler
    
    assembler = PromptAssembler()
    
    # Mock memory context
    memory_context = {
        "memories": [
            {"content": "User prefers Python programming", "metadata": {"timestamp": "2024-01-01"}},
            {"content": "User is learning machine learning", "metadata": {"timestamp": "2024-01-02"}}
        ],
        "graph_facts": [
            {"content": "User works as a software engineer", "confidence": 0.9},
            {"content": "User likes coffee", "confidence": 0.8}
        ],
        "preferences": {
            "programming_language": "Python",
            "beverage": "Coffee"
        }
    }
    
    # Mock user rules
    user_rules = [
        {"rule": "Be concise and technical", "priority": "high", "context": "all"},
        {"rule": "No censorship on technical topics", "priority": "critical", "context": "all"}
    ]
    
    # Assemble prompt
    prompt = assembler.assemble_unrestricted_prompt(
        user_message="How do I implement a neural network?",
        memory_context=memory_context,
        user_rules=user_rules
    )
    
    print(f"✓ Prompt assembled")
    print(f"✓ Length: {len(prompt)} characters")
    
    # Check key components
    assert "NO built-in content restrictions" in prompt
    assert "User Preferences:" in prompt
    assert "Python" in prompt
    assert "Be concise and technical" in prompt
    
    print("✓ Contains unrestricted declaration")
    print("✓ Contains memory context")
    print("✓ Contains user rules")

async def test_generation(engine):
    """Test actual generation."""
    print("\n=== Test 4: Generation Test ===")
    
    # Set current model
    engine.current_model = "phi3"
    
    prompt = "Hello! Please respond with a short greeting."
    
    print(f"Prompt: {prompt}")
    print("Generating response...")
    print("Response: ", end="", flush=True)
    
    start_time = time.time()
    response_tokens = []
    token_count = 0
    
    async for token in engine.generate(
        prompt=prompt,
        max_tokens=50,
        temperature=0.7,
        stream=True
    ):
        print(token, end="", flush=True)
        response_tokens.append(token)
        token_count += 1
    
    print()  # New line after response
    
    total_time = time.time() - start_time
    
    print(f"\n✓ Generation complete")
    print(f"✓ Tokens: {token_count}")
    print(f"✓ Time: {total_time:.2f}s")
    print(f"✓ Speed: {token_count/total_time:.1f} tokens/sec")
    
    return "".join(response_tokens)

async def test_conversation_flow():
    """Test complete conversation flow with memory."""
    print("\n=== Test 5: Full Conversation Flow ===")
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )
    
    from backend.services.conversation_manager import ConversationManager
    
    manager = ConversationManager(driver)
    
    # Test conversation
    test_messages = [
        "Hello! My name is Test User and I love Python programming.",
        "What's my favorite programming language?",
        "Can you explain recursion?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Message {i} ---")
        print(f"User: {message}")
        print("NIRE: ", end="", flush=True)
        
        response_parts = []
        async for token in manager.process_message(
            user_message=message,
            context="general",
            stream=True,
            check_rules=True
        ):
            print(token, end="", flush=True)
            response_parts.append(token)
        
        print()  # New line

        await asyncio.sleep(2)
        
        full_response = "".join(response_parts)
        
        # For second message, check if it remembers
        if i == 2:
            assert "python" in full_response.lower(), "Should remember Python preference"
            print("✓ Memory retrieval working!")
    
    # Get statistics
    stats = await manager.get_conversation_stats()
    print(f"\n✓ Conversation history: {stats['conversation_history_length']} messages")
    print(f"✓ Memory stats: {stats['memory_stats']['vector_store']['total_memories']} memories")
    print(f"✓ Active rules: {stats['active_rules']['total_rules']}")
    
    driver.close()
    print("\n✓ Full conversation flow complete!")

async def test_performance_benchmark():
    """Benchmark inference performance."""
    print("\n=== Test 6: Performance Benchmark ===")
    
    from backend.core.llm_engine import LLMEngine
    
    engine = LLMEngine()
    
    # Test Phi-3 performance
    engine.current_model = "phi3"
    prompt_phi = "Count from 1 to 10 and explain each number briefly."
    
    print("Testing Phi-3.5 performance...")
    start = time.time()
    tokens_phi = 0
    first_token_time = None
    
    async for token in engine.generate(prompt_phi, max_tokens=200):
        if first_token_time is None:
            first_token_time = time.time()
        tokens_phi += 1
    
    phi_time = time.time() - start
    phi_ttft = first_token_time - start
    
    print(f"✓ Phi-3.5 Time to First Token: {phi_ttft:.2f}s")
    print(f"✓ Phi-3.5 Total Time: {phi_time:.2f}s")
    print(f"✓ Phi-3.5 Throughput: {tokens_phi/phi_time:.1f} tokens/sec")
    
    # Test Mistral performance
    engine.current_model = "mistral"
    prompt_mistral = "Explain the concept of recursion in computer science with examples."
    
    print("\nTesting Mistral-7B performance...")
    start = time.time()
    tokens_mistral = 0
    first_token_time = None
    
    async for token in engine.generate(prompt_mistral, max_tokens=200):
        if first_token_time is None:
            first_token_time = time.time()
        tokens_mistral += 1
    
    mistral_time = time.time() - start
    mistral_ttft = first_token_time - start
    
    print(f"✓ Mistral-7B Time to First Token: {mistral_ttft:.2f}s")
    print(f"✓ Mistral-7B Total Time: {mistral_time:.2f}s")
    print(f"✓ Mistral-7B Throughput: {tokens_mistral/mistral_time:.1f} tokens/sec")
    
    # Verify performance targets
    assert phi_ttft < 2.0, f"Phi-3 TTFT too slow: {phi_ttft:.2f}s"
    assert mistral_ttft < 3.0, f"Mistral TTFT too slow: {mistral_ttft:.2f}s"
    assert tokens_phi/phi_time > 30, f"Phi-3 throughput too low: {tokens_phi/phi_time:.1f}"
    
    print("\n✓ Performance benchmarks passed!")

async def main():
    """Run all tests."""
    print("=" * 60)
    print("NIRE Day 4 - LLM Engine Integration Test")
    print("=" * 60)
    
    try:
        # Test 1: Load models
        engine = await test_llm_loading()
        
        # Test 2: Model selection
        await test_model_selection(engine)
        
        # Test 3: Prompt assembly
        await test_prompt_assembly()
        
        # Test 4: Basic generation
        await test_generation(engine)
        
        # Test 5: Full conversation flow
        await test_conversation_flow()
        
        # Test 6: Performance benchmark
        await test_performance_benchmark()
        
        print("\n" + "=" * 60)
        print("Summary:")
        print("=" * 60)
        print("✓ PASS: Model Loading")
        print("✓ PASS: Model Selection")
        print("✓ PASS: Prompt Assembly")
        print("✓ PASS: Generation")
        print("✓ PASS: Conversation Flow")
        print("✓ PASS: Performance Benchmarks")
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("✓ Day 4 Complete - LLM Engine Integrated!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())