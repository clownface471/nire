"""
Conversation Manager
Orchestrates the complete conversation flow with memory and LLM integration.
"""

import asyncio
import time
from typing import Dict, AsyncGenerator, Optional, List
from datetime import datetime
import structlog

from backend.core.llm_engine import LLMEngine
from backend.memory.memory_controller import MemoryController
from backend.memory.user_rule_system import UserRuleSystem

logger = structlog.get_logger()


class ConversationManager:
    """
    Manages end-to-end conversation flow:
    1. Receive user message
    2. Retrieve memory context
    3. Check user rules
    4. Generate response
    5. Store conversation in memory
    """
    
    def __init__(self, neo4j_driver, redis_client=None):
        """
        Initialize conversation manager.
        
        Args:
            neo4j_driver: Neo4j database driver
            redis_client: Optional Redis client for caching
        """
        self.llm_engine = LLMEngine()
        self.memory_controller = MemoryController(neo4j_driver, user_id="user_001")
        self.rule_system = UserRuleSystem(neo4j_driver)
        self.redis = redis_client
        self.conversation_history = []
        
        logger.info("Conversation Manager initialized")
    
    async def process_message(
        self,
        user_message: str,
        context: str = "general",
        stream: bool = True,
        check_rules: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Process a user message and generate response.
        
        Args:
            user_message: User's input text
            context: Current context (general, work, personal, etc.)
            stream: Whether to stream the response
            check_rules: Whether to check user rules
            
        Yields:
            Response tokens (if streaming) or complete response
        """
        start_time = time.time()
        
        try:
            # Step 1: Retrieve memory context
            logger.info("Retrieving memory context", query_length=len(user_message))
            memory_context = await self.memory_controller.retrieve_context(
                query=user_message,
                k=5,
                context=context,
                check_rules=check_rules
            )
            
            # Step 2: Get active user rules
            user_rules = []
            if check_rules:
                rules = self.rule_system.get_active_rules("user_001", context=context)
                user_rules = [
                    {
                        "rule": r["rule"],
                        "priority": r["priority"],
                        "context": r["context"]
                    }
                    for r in rules
                ]
            
            # Step 3: Check for rule conflicts
            if memory_context.get("has_conflicts") and check_rules:
                # Generate conflict resolution prompt
                conflict_msg = ""
                async for msg in self._handle_rule_conflict(
                    user_message,
                    memory_context,
                    user_rules
                ):
                    yield msg
                    conflict_msg += msg
                
                # If user chooses not to override, return
                if "not overriding" in conflict_msg.lower():
                    return
            
            # Step 4: Generate response with LLM
            logger.info(
                "Generating response",
                model=self.llm_engine.current_model,
                has_memory=bool(memory_context.get("memories")),
                num_rules=len(user_rules)
            )
            
            response_parts = []
            async for token in self.llm_engine.generate_with_context(
                user_message=user_message,
                memory_context=memory_context,
                user_rules=user_rules,
                stream=stream
            ):
                response_parts.append(token)
                if stream:
                    yield token
            
            # Complete response
            full_response = "".join(response_parts)
            
            # Step 5: Store conversation in memory (async)
            asyncio.create_task(
                self._store_conversation(
                    user_message=user_message,
                    assistant_response=full_response,
                    context=context
                )
            )
            
            # Update conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep only last 10 exchanges
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            # Log performance
            total_time = time.time() - start_time
            logger.info(
                "Message processed",
                total_time_s=round(total_time, 2),
                response_length=len(full_response)
            )
            
            if not stream:
                yield full_response
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            yield f"Error: {str(e)}"
    
    async def _handle_rule_conflict(
        self,
        user_message: str,
        memory_context: Dict,
        user_rules: List[Dict]
    ) -> AsyncGenerator[str, None]:
        """Handle rule conflicts with transparency."""
        
        conflicting_rules = memory_context.get("conflicting_rules", [])
        
        conflict_prompt = f"""
## Rule Conflict Detected

Your request: "{user_message}"

This conflicts with your rule(s):
"""
        
        for rule in conflicting_rules:
            conflict_prompt += f"- [{rule['priority']}] {rule['rule']}\n"
        
        conflict_prompt += """
Would you like to:
1. Override this rule for this request only
2. Disable the rule permanently
3. Cancel the request

Please respond with your choice.
"""
        
        yield conflict_prompt
        
        # In a real implementation, wait for user response
        # For now, assume override
        yield "\n\n[Assuming override for this request]\n\n"
    
    async def _store_conversation(
        self,
        user_message: str,
        assistant_response: str,
        context: str
    ):
        """Store conversation in memory system (async)."""
        try:
            await self.memory_controller.process_conversation(
                user_message=user_message,
                assistant_response=assistant_response,
                context=context
            )
            logger.debug("Conversation stored in memory")
        except Exception as e:
            logger.error(f"Failed to store conversation: {str(e)}")
    
    async def get_conversation_stats(self) -> Dict:
        """Get conversation statistics."""
        memory_stats = self.memory_controller.get_statistics()
        llm_info = self.llm_engine.get_model_info()
        
        return {
            "conversation_history_length": len(self.conversation_history),
            "memory_stats": memory_stats,
            "llm_models": llm_info,
            "active_rules": self.rule_system.get_rule_statistics("user_001")
        }
    
    async def export_conversation(self) -> Dict:
        """Export current conversation for backup."""
        return {
            "timestamp": datetime.now().isoformat(),
            "history": self.conversation_history,
            "memory_snapshot": await self.memory_controller.export_all_memories(),
            "active_rules": self.rule_system.export_rules("user_001")
        }