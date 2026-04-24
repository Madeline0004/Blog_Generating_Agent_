"""Embedding model wrapper for semantic search."""

import numpy as np
from typing import List

from src.config import EMBEDDING_MODEL

# Try to import sentence-transformers, fallback to simple encoding
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    print("Warning: sentence-transformers not installed. Using simple hash-based fallback.")
    print("For production, install with: pip install sentence-transformers")


class EmbeddingModel:
    """
    Wrapper for embedding models.
    
    Primary: sentence-transformers/all-MiniLM-L6-v2 (384 dims)
    Fallback: Simple hash-based embeddings (deterministic, consistent dims)
    
    The fallback uses a simple but effective approach:
    - Hash words to fixed positions in a 384-dim vector
    - Use word frequency as weight
    - Normalize to unit length
    
    This is not as semantically powerful as neural embeddings, but:
    - Always produces consistent dimensions
    - No dependencies beyond numpy
    - Works for basic similarity matching
    """
    
    _instance = None
    _model = None
    _dimension = 384
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None and HAS_SENTENCE_TRANSFORMERS:
            self._model = SentenceTransformer(EMBEDDING_MODEL)
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts to embeddings."""
        if isinstance(texts, str):
            texts = [texts]
        
        if HAS_SENTENCE_TRANSFORMERS and self._model is not None:
            return self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        
        # Fallback: simple hash-based encoding
        return self._hash_encode(texts)
    
    def _hash_encode(self, texts: List[str]) -> np.ndarray:
        """Deterministic hash-based text encoding."""
        embeddings = []
        for text in texts:
            vec = np.zeros(self._dimension, dtype=np.float32)
            words = text.lower().split()
            
            for word in words:
                # Simple hash to position
                h = hash(word) % self._dimension
                # Use word length as a simple weight signal
                vec[h] += 1.0 + (len(word) * 0.1)
                
                # Also use character n-grams for subword info
                for i in range(len(word) - 1):
                    bigram = word[i:i+2]
                    h2 = hash(bigram) % self._dimension
                    vec[h2] += 0.5
            
            # Normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            
            embeddings.append(vec)
        
        return np.array(embeddings)
    
    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        if HAS_SENTENCE_TRANSFORMERS and self._model is not None:
            return self._model.get_sentence_embedding_dimension()
        return self._dimension


def get_embedding_model() -> EmbeddingModel:
    """Get or create singleton embedding model instance."""
    return EmbeddingModel()
