"""
Context Manager
Detects and manages conversation context (Work, Personal, Research, etc).
"""
from typing import Tuple, List
import structlog

logger = structlog.get_logger()

class ContextManager:
    
    def __init__(self):
        self.current_context = "general"
        self.context_history = []
        
        # Keywords for detection
        self.keywords = {
            "work": ["project", "deadline", "meeting", "code", "client", "report"],
            "personal": ["hobby", "family", "weekend", "game", "movie", "rest"],
            "research": ["analyze", "study", "paper", "theory", "investigate"],
            "coding": ["python", "bug", "error", "function", "api", "git"]
        }
    
    def detect_context(self, text: str) -> Tuple[str, float]:
        """Simple keyword-based context detection."""
        text_lower = text.lower()
        scores = {ctx: 0.0 for ctx in self.keywords}
        
        # Count keyword matches
        for ctx, keywords in self.keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    scores[ctx] += 1.0
        
        # Find best match
        best_ctx = max(scores, key=scores.get)
        max_score = scores[best_ctx]
        
        # Threshold
        if max_score > 0:
            confidence = min(max_score * 0.2, 1.0) # Cap at 1.0
            self.set_context(best_ctx)
            return best_ctx, confidence
            
        return "general", 0.0

    def set_context(self, context: str):
        if context != self.current_context:
            logger.info("Context switched", old=self.current_context, new=context)
            self.context_history.append(self.current_context)
            self.current_context = context

    def get_current_context(self) -> str:
        return self.current_context