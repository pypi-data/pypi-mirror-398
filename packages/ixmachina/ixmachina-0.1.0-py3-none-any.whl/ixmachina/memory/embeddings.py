"""
Embedding generation utilities for semantic search.

Uses sentence-transformers for free, local embeddings without API keys.
"""

from typing import Optional, List
import warnings


class EmbeddingGenerator:
    """
    Generates embeddings using sentence-transformers.
    
    Falls back gracefully if sentence-transformers is not installed.
    Uses the 'all-MiniLM-L6-v2' model by default (fast, good quality, local).
    
    Args:
        model_name: Name of the sentence-transformers model to use.
        enabled: Whether embedding generation is enabled. If False, returns None.
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        enabled: bool = True,
    ):
        self.model_name = model_name
        self.enabled = enabled
        self._model = None
        self._tried_loading = False
    
    def _load_model(self) -> bool:
        """
        Load the sentence-transformers model.
        
        Returns:
            True if model loaded successfully, False otherwise.
        """
        if self._tried_loading:
            return self._model is not None
        
        self._tried_loading = True
        
        if not self.enabled:
            return False
        
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            return True
        except ImportError:
            warnings.warn(
                "sentence-transformers not installed. "
                "Install it with: pip install sentence-transformers"
            )
            return False
        except Exception as e:
            warnings.warn(f"Failed to load embedding model: {e}")
            return False
    
    def embed(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed.
            
        Returns:
            Embedding vector as a list of floats, or None if embedding failed.
        """
        if not text:
            return None
        
        if not self._load_model():
            return None
        
        try:
            embedding = self._model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            warnings.warn(f"Failed to generate embedding: {e}")
            return None
    
    def embed_object(
        self,
        name: str,
        description: str = "",
    ) -> Optional[List[float]]:
        """
        Generate combined embedding for object name and description.
        
        Args:
            name: Object name.
            description: Object description.
            
        Returns:
            Combined embedding vector or None.
        """
        if not description:
            combined_text = name
        else:
            combined_text = f"{name}. {description}"
        
        return self.embed(text=combined_text)
    
    def embed_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Generate embeddings for multiple texts (more efficient than one-by-one).
        
        Args:
            texts: List of texts to embed.
            
        Returns:
            List of embedding vectors, or None if embedding failed.
        """
        if not texts:
            return None
        
        if not self._load_model():
            return None
        
        try:
            embeddings = self._model.encode(texts, convert_to_numpy=True)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            warnings.warn(f"Failed to generate embeddings: {e}")
            return None



