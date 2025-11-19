"""
Conversation Manager (Enhanced)
Orchestrates conversation with context, error handling, and performance tracking.
"""

import asyncio
from typing import AsyncGenerator, Dict
from datetime import datetime
import structlog

from backend.core.llm_engine import LLMEngine
from backend.memory.memory_controller import MemoryController
from backend.memory.user_rule_system import UserRuleSystem
from backend.services.context_manager import ContextManager
from backend.services.error_handler import ErrorHandler
from backend.services.performance_monitor import PerformanceMonitor

logger = structlog.get_logger()

class ConversationManager:
    
    def __init__(self, neo4j_driver):
        self.llm_engine = LLMEngine()
        self.memory_controller = MemoryController(neo4j_driver, user_id="user_001")
        self.rule_system = UserRuleSystem(neo4j_driver)
        
        # New Services
        self.context_manager = ContextManager()
        self.error_handler = ErrorHandler()
        self.monitor = PerformanceMonitor()
        
        self.history = []
        logger.info("Conversation Manager (Enhanced) initialized")
    
    async def process_message(
        self, 
        user_msg: str, 
        explicit_context: str = None,
        stream: bool = True,
        check_rules: bool = True
    ) -> AsyncGenerator[str, None]:
        
        self.monitor.start("total_process")
        
        # 1. Detect Context
        context = explicit_context
        if not context:
            ctx, conf = self.context_manager.detect_context(user_msg)
            context = ctx
            if conf > 0.5:
                logger.info(f"Context auto-detected: {context} ({conf:.2f})")

        # 2. Retrieve Memory (Safe Retry)
        try:
            mem_ctx = await self.error_handler.retry_async(
                self.memory_controller.retrieve_context,
                retries=2,
                query=user_msg,
                context=context,
                check_rules=check_rules
            )
        except Exception:
            logger.error("Memory retrieval failed, proceeding without memory")
            mem_ctx = {}

        # 3. Get Rules
        rules = []
        if check_rules:
            rules = self.rule_system.get_active_rules("user_001", context=context)

        # 4. Check Conflicts (Fix Async Loop)
        if mem_ctx.get("has_conflicts"):
            conflict_msg = ""
            async for msg in self._handle_rule_conflict(user_msg, mem_ctx, rules):
                yield msg
                conflict_msg += msg
            
            if "not overriding" in conflict_msg.lower():
                return

        # 5. Generate Response (Stream)
        full_response = ""
        self.monitor.start("generation")
        token_count = 0
        
        try:
            # Convert rule dicts to expected format if needed
            formatted_rules = [
                {"rule": r["rule"], "priority": r["priority"], "context": r["context"]}
                for r in rules
            ]
            
            async for token in self.llm_engine.generate_with_context(
                user_msg, mem_ctx, formatted_rules, stream=stream
            ):
                full_response += token
                token_count += 1
                yield token
                
        except Exception as e:
            yield f"\n[System Error: {str(e)}]"
            logger.error("Generation failed", error=str(e))
            
        self.monitor.stop("generation", token_count)

        # 6. Store Memory (Async & Safe)
        asyncio.create_task(self._safe_store(user_msg, full_response, context))
        
        # Update History
        self._update_history(user_msg, full_response)
        
        self.monitor.stop("total_process")

    async def _handle_rule_conflict(self, msg, ctx, rules):
        # Simplified conflict handler
        yield "⚠️ RULE CONFLICT. Overriding...\n\n"

    async def _safe_store(self, user, assistant, context):
        try:
            await self.memory_controller.process_conversation(user, assistant, context)
        except Exception as e:
            logger.error("Failed to store conversation", error=str(e))

    def _update_history(self, user, assistant):
        self.history.append({"role": "user", "content": user})
        self.history.append({"role": "assistant", "content": assistant})
        if len(self.history) > 20: self.history = self.history[-20:]

    async def get_conversation_stats(self) -> Dict:
        memory_stats = self.memory_controller.get_statistics()
        llm_info = self.llm_engine.get_model_info()
        rule_stats = self.rule_system.get_rule_statistics("user_001")
        
        return {
            "history_len": len(self.history),
            "memory_stats": memory_stats,
            "context": self.context_manager.get_current_context(),
            "active_rules": rule_stats,     
            "llm_models": llm_info         
        }