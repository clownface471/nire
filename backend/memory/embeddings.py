"""
Embedding Generator for NIRE
Converts text to vector embeddings for semantic search.
"""

from typing import List, Union
from sentence_transformers import SentenceTransformer
import structlog
import torch

from backend.config import settings

logger = structlog.get_logger()


class EmbeddingGenerator:
    """
    Generates embeddings using sentence-transformers.
    
    Uses all-MiniLM-L6-v2 for balance of speed and quality.
    """
    
    def __init__(self):
        """Initialize embedding model."""
        logger.info(
            "Loading embedding model",
            model=settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE
        )
        
        # Load model
        self.model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE
        )
        
        # Get embedding dimension
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        logger.info(
            "Embedding model loaded",
            dimension=self.dimension,
            device=settings.EMBEDDING_DEVICE
        )
    
    async def encode(
        self,
        text: Union[str, List[str]],
        normalize: bool = True
    ) -> Union[List[float], List[List[float]]]:
        """
        Generate embedding(s) for text.
        
        Args:
            text: Single text or list of texts
            normalize: Whether to normalize embeddings
            
        Returns:
            Single embedding or list of embeddings
        """
        
        is_single = isinstance(text, str)
        
        if is_single:
            text = [text]
        
        try:
            # Generate embeddings
            embeddings = self.model.encode(
                text,
                normalize_embeddings=normalize,
                convert_to_tensor=False,
                show_progress_bar=False
            )
            
            # Convert to list
            embeddings = embeddings.tolist()
            
            logger.debug(
                "Embeddings generated",
                count=len(embeddings),
                dimension=self.dimension
            )
            
            # Return single embedding if input was single text
            if is_single:
                return embeddings[0]
            
            return embeddings
            
        except Exception as e:
            logger.error(
                "Failed to generate embeddings",
                error=str(e),
                text_count=len(text)
            )
            raise
    
    async def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        normalize: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings in batches (more efficient for many texts).
        
        Args:
            texts: List of texts
            batch_size: Batch size for processing
            normalize: Whether to normalize embeddings
            
        Returns:
            List of embeddings
        """
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                convert_to_tensor=False,
                show_progress_bar=len(texts) > 100
            )
            
            embeddings = embeddings.tolist()
            
            logger.info(
                "Batch embeddings generated",
                count=len(embeddings),
                batch_size=batch_size
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(
                "Failed to generate batch embeddings",
                error=str(e),
                text_count=len(texts)
            )
            raise
    
    def get_dimension(self) -> int:
        """Return embedding dimension."""
        return self.dimension
    
    def get_model_info(self) -> dict:
        """Return model information."""
        return {
            "model_name": settings.EMBEDDING_MODEL,
            "dimension": self.dimension,
            "device": settings.EMBEDDING_DEVICE,
            "max_seq_length": self.model.max_seq_length
        }
