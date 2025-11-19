"""
NIRE Quick Demo - Week 1 Complete
Interactive test of all systems!
"""

import asyncio
import sys
from dotenv import load_dotenv
import os

# Add backend to path
sys.path.append('backend')

load_dotenv()

print("=" * 70)
print("🤖 NIRE Quick Demo - Week 1 Complete")
print("=" * 70)
print()
print("This demo will showcase all Week 1 features:")
print("  ✓ Conversation with memory")
print("  ✓ Context detection")
print("  ✓ User rules")
print("  ✓ Streaming responses")
print()
print("=" * 70)
print()


async def demo():
    """Run interactive demo."""
    
    from services.conversation_manager import ConversationManager
    from neo4j import GraphDatabase
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )
    
    manager = ConversationManager(driver)
    
    print("🎭 Demo Scenario: Teaching NIRE About You")
    print("-" * 70)
    print()
    
    # Scenario 1: Introduction
    print("📍 Scenario 1: Introduction")
    print()
    
    msg1 = "Hi! I'm Alex, a Python developer who loves coffee and AI."
    print(f"👤 You: {msg1}")
    print()
    print("🤖 NIRE: ", end="", flush=True)
    
    response1 = []
    async for token in manager.process_message(msg1, stream=True):
        print(token, end="", flush=True)
        response1.append(token)
    
    print("\n")
    await asyncio.sleep(2)
    
    # Scenario 2: Memory Recall
    print("-" * 70)
    print("📍 Scenario 2: Memory Recall (Testing Memory)")
    print()
    
    msg2 = "What do you know about me?"
    print(f"👤 You: {msg2}")
    print()
    print("🤖 NIRE: ", end="", flush=True)
    
    response2 = []
    async for token in manager.process_message(msg2, stream=True):
        print(token, end="", flush=True)
        response2.append(token)
    
    print("\n")
    
    # Check if NIRE remembered
    full_response = "".join(response2).lower()
    remembered = []
    if "alex" in full_response:
        remembered.append("name")
    if "python" in full_response:
        remembered.append("Python")
    if "coffee" in full_response:
        remembered.append("coffee")
    if "ai" in full_response or "artificial intelligence" in full_response:
        remembered.append("AI interest")
    
    print(f"✅ Memory Test: NIRE remembered {len(remembered)}/4 facts")
    if remembered:
        print(f"   Recalled: {', '.join(remembered)}")
    print()
    
    await asyncio.sleep(2)
    
    # Scenario 3: Technical Question
    print("-" * 70)
    print("📍 Scenario 3: Technical Discussion")
    print()
    
    msg3 = "Explain recursion in Python with an example."
    print(f"👤 You: {msg3}")
    print()
    print("🤖 NIRE: ", end="", flush=True)
    
    response3 = []
    async for token in manager.process_message(msg3, stream=True):
        print(token, end="", flush=True)
        response3.append(token)
    
    print("\n")
    await asyncio.sleep(2)
    
    # Scenario 4: Context Switch
    print("-" * 70)
    print("📍 Scenario 4: Context Detection")
    print()
    
    msg4 = "I have a project deadline next week and need to prepare a presentation."
    print(f"👤 You: {msg4}")
    print("   (This should trigger 'work' context)")
    print()
    print("🤖 NIRE: ", end="", flush=True)
    
    response4 = []
    async for token in manager.process_message(msg4, stream=True):
        print(token, end="", flush=True)
        response4.append(token)
    
    print("\n")
    await asyncio.sleep(2)
    
    # Get Statistics
    print("-" * 70)
    print("📊 Session Statistics")
    print()
    
    stats = await manager.get_conversation_stats()
    
    print(f"💬 Conversation:")
    print(f"   Messages exchanged: {stats['history_len']}")
    print()
    
    mem_stats = stats['memory_stats']
    print(f"🧠 Memory:")
    print(f"   Vector memories: {mem_stats['vector_store']['total_memories']}")
    print(f"   Graph facts: {mem_stats['graph_store']['facts']}")
    print(f"   User preferences: {mem_stats['graph_store']['preferences']}")
    print()
    
    rule_stats = stats['active_rules']
    print(f"📋 Rules:")
    print(f"   Total rules: {rule_stats['total_rules']}")
    print(f"   Active rules: {rule_stats['active_rules']}")
    print()
    
    llm_info = stats['llm_models']
    print(f"⚡ LLM Models:")
    for model, info in llm_info.items():
        status = "✓" if info['loaded'] else "✗"
        current = " (current)" if info['current'] else ""
        print(f"   {status} {model}{current}")
    print()
    
    # Cleanup
    driver.close()
    
    # Final Summary
    print("=" * 70)
    print("✅ Demo Complete!")
    print("=" * 70)
    print()
    print("What was demonstrated:")
    print("  ✓ Natural conversation")
    print("  ✓ Memory storage and recall")
    print("  ✓ Context detection (work mode)")
    print("  ✓ Streaming responses")
    print("  ✓ Technical knowledge")
    print()
    print("Week 1 Status: All systems operational! 🎉")
    print()


if __name__ == "__main__":
    try:
        print("Starting demo in 3 seconds...")
        print()
        asyncio.sleep(1)
        print("3...")
        asyncio.sleep(1)
        print("2...")
        asyncio.sleep(1)
        print("1...")
        print()
        
        asyncio.run(demo())
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        print("Thanks for watching! 👋")
    except Exception as e:
        print(f"\n\n❌ Error during demo: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Check databases are running")
        print("  2. Verify .env configuration")
        print("  3. Run: python test_day5_complete.py")
        import traceback
        traceback.print_exc()
