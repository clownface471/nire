"""
LLM Engine Module
Handles model loading, inference, and GPU memory management.
Integrated with unrestricted mode and memory system.
"""

import os
import time
from typing import AsyncGenerator, Dict, Optional, List
from llama_cpp import Llama
import structlog
import asyncio
from concurrent.futures import ThreadPoolExecutor

from backend.config import settings
from backend.utils.exceptions import ModelLoadError, InferenceError

logger = structlog.get_logger()


class LLMEngine:
    """
    Wrapper for llama.cpp with support for multiple models and streaming.
    Now with memory integration and unrestricted mode support.
    """
    
    def __init__(self):
        self.models: Dict[str, Llama] = {}
        self.current_model: Optional[str] = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        logger.info("Initializing Unrestricted LLM Engine")
        self._load_models()
    
    def _load_models(self):
        """Load both primary and secondary models into memory."""
        model_configs = {
            "phi3": {
                "path": settings.LLM_MODEL_PRIMARY,
                "name": "Phi-3.5-mini",
                "ctx_size": 2048,
                "gpu_layers": -1  # Use all GPU layers
            },
            "mistral": {
                "path": settings.LLM_MODEL_SECONDARY,
                "name": "Mistral-7B",
                "ctx_size": 4096,
                "gpu_layers": -1
            }
        }
        
        for key, config in model_configs.items():
            try:
                logger.info(f"Loading {config['name']}...", model=key)
                
                if not os.path.exists(config["path"]):
                    raise ModelLoadError(f"Model file not found: {config['path']}")
                
                # Load model with optimized settings
                model = Llama(
                    model_path=config["path"],
                    n_gpu_layers=config["gpu_layers"],
                    n_ctx=config["ctx_size"],
                    n_batch=512,
                    n_threads=8,
                    verbose=False,
                    use_mlock=True,  # Keep in RAM
                    use_mmap=True,   # Memory-mapped for efficiency
                    rope_freq_scale=1.0,
                    seed=-1  # Random seed
                )
                
                self.models[key] = model
                logger.info(
                    f"Successfully loaded {config['name']}",
                    model=key,
                    context_size=config["ctx_size"]
                )
                
            except Exception as e:
                logger.error(f"Failed to load {config['name']}: {str(e)}")
                raise ModelLoadError(f"Could not load model {key}: {str(e)}")
    
    def select_model(self, prompt: str, context: Dict) -> str:
        """
        Select appropriate model based on query complexity and context size.
        
        Args:
            prompt: User input text
            context: Retrieved memory context
            
        Returns:
            Model name: "phi3" or "mistral"
        """
        # Complex reasoning keywords that need Mistral
        complex_keywords = [
            "analyze", "compare", "evaluate", "explain in detail",
            "comprehensive", "in-depth", "philosophical", "implications",
            "reasoning", "technical details", "algorithm", "architecture"
        ]
        
        # Check prompt complexity
        prompt_lower = prompt.lower()
        word_count = len(prompt.split())
        
        # Check for complex keywords
        has_complex = any(kw in prompt_lower for kw in complex_keywords)
        
        # Check context size (serialize to estimate)
        context_size = len(str(context)) if context else 0
        
        # Decision logic
        if word_count > 150 or has_complex or context_size > 2000:
            logger.debug(
                "Selecting Mistral for complex query",
                word_count=word_count,
                has_complex=has_complex,
                context_size=context_size
            )
            return "mistral"
        
        logger.debug("Selecting Phi-3 for quick response")
        return "phi3"
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stream: bool = True,
        stop_sequences: Optional[List[str]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate response from LLM with streaming support.
        
        Args:
            prompt: Complete prompt with context
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream tokens
            stop_sequences: Optional stop sequences
            
        Yields:
            Generated text tokens (if stream=True)
        """
        try:
            # Get the current model
            if not self.current_model or self.current_model not in self.models:
                raise InferenceError("No model selected or loaded")
            
            model = self.models[self.current_model]
            
            # Default stop sequences for conversation
            if stop_sequences is None:
                stop_sequences = ["User:", "Human:", "\n\n\n"]
            
            # Start generation timing
            start_time = time.time()
            first_token_time = None
            token_count = 0
            
            if stream:
                # Streaming generation in thread pool
                loop = asyncio.get_event_loop()
                
                # Create generator function for thread
                def generate_tokens():
                    return model(
                        prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stop=stop_sequences,
                        stream=True,
                        echo=False,
                        top_p=0.95,
                        repeat_penalty=1.1
                    )
                
                # Run in thread pool
                generator = await loop.run_in_executor(
                    self.executor,
                    generate_tokens
                )
                
                # Stream tokens
                for output in generator:
                    if first_token_time is None:
                        first_token_time = time.time()
                        ttft = first_token_time - start_time
                        logger.debug(f"Time to first token: {ttft:.2f}s")
                    
                    token = output['choices'][0]['text']
                    token_count += 1
                    yield token
                
                # Log performance
                total_time = time.time() - start_time
                logger.info(
                    "Generation complete",
                    model=self.current_model,
                    tokens=token_count,
                    total_time_s=round(total_time, 2),
                    tokens_per_sec=round(token_count / total_time, 1)
                )
            
            else:
                # Non-streaming generation
                loop = asyncio.get_event_loop()
                
                def generate_complete():
                    return model(
                        prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stop=stop_sequences,
                        stream=False,
                        echo=False,
                        top_p=0.95,
                        repeat_penalty=1.1
                    )
                
                output = await loop.run_in_executor(
                    self.executor,
                    generate_complete
                )
                
                response = output['choices'][0]['text']
                total_time = time.time() - start_time
                
                logger.info(
                    "Generation complete (non-streaming)",
                    model=self.current_model,
                    response_length=len(response),
                    total_time_s=round(total_time, 2)
                )
                
                yield response
        
        except Exception as e:
            logger.error(f"Generation error: {str(e)}")
            raise InferenceError(f"Generation failed: {str(e)}")
    
    async def generate_with_context(
        self,
        user_message: str,
        memory_context: Dict,
        user_rules: List[Dict],
        max_tokens: int = 512,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Generate response with memory context and user rules.
        
        This is the main method for conversation generation.
        """
        # Select model based on complexity
        self.current_model = self.select_model(user_message, memory_context)
        
        # Import prompt assembler
        from backend.core.prompt_assembler import PromptAssembler
        
        # Assemble prompt with context
        assembler = PromptAssembler()
        full_prompt = assembler.assemble_unrestricted_prompt(
            user_message=user_message,
            memory_context=memory_context,
            user_rules=user_rules
        )
        
        # Log prompt info
        logger.debug(
            "Prompt assembled",
            prompt_length=len(full_prompt),
            model=self.current_model,
            has_memory=bool(memory_context.get('memories')),
            num_rules=len(user_rules)
        )
        
        # Generate response
        async for token in self.generate(
            prompt=full_prompt,
            max_tokens=max_tokens,
            stream=stream
        ):
            yield token
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models."""
        info = {}
        for name, model in self.models.items():
            info[name] = {
                "loaded": True,
                "current": name == self.current_model,
                "context_size": model.n_ctx()
            }
        return info
    
    def __del__(self):
        """Cleanup models and thread pool."""
        self.executor.shutdown(wait=False)
        for model_name in list(self.models.keys()):
            del self.models[model_name]