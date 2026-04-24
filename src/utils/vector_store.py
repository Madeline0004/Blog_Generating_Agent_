"""Vector store implementation for blog retrieval."""

import os
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from src.config import VECTOR_STORE_PATH
from src.utils.embeddings import get_embedding_model

# Try to import FAISS, fallback to pure numpy
try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    print("Warning: faiss not installed. Using pure NumPy fallback.")
    print("For production speed, install with: pip install faiss-cpu")


class VectorStore:
    """
    Vector store for dense semantic search.
    
    Primary: FAISS IndexFlatIP (fast, optimized)
    Fallback: Pure NumPy + sklearn (no extra dependencies)
    
    Uses L2-normalized embeddings for cosine similarity search.
    """
    
    def __init__(self, store_path: str = None):
        self.store_path = Path(store_path or VECTOR_STORE_PATH)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        self.index = None  # FAISS index
        self.vectors = []  # Fallback: list of numpy arrays
        self.metadata: List[Dict] = []
        self.dimension = None
        
        # Try to load existing
        self._load()
    
    def _get_index_file(self) -> Path:
        return self.store_path / ("faiss.index" if HAS_FAISS else "vectors.pkl")
    
    def _get_metadata_file(self) -> Path:
        return self.store_path / "metadata.pkl"
    
    def _load(self):
        """Load existing index from disk if available."""
        index_file = self._get_index_file()
        metadata_file = self._get_metadata_file()
        
        if index_file.exists() and metadata_file.exists():
            try:
                if HAS_FAISS:
                    self.index = faiss.read_index(str(index_file))
                    self.dimension = self.index.d
                else:
                    with open(index_file, 'rb') as f:
                        self.vectors = pickle.load(f)
                    if self.vectors:
                        self.dimension = self.vectors[0].shape[0]
                
                with open(metadata_file, 'rb') as f:
                    self.metadata = pickle.load(f)
                print(f"Loaded existing index with {len(self.metadata)} vectors")
            except Exception as e:
                print(f"Failed to load existing index: {e}")
                self.index = None
                self.vectors = []
                self.metadata = []
    
    def _save(self):
        """Save index and metadata to disk."""
        if self.metadata:
            if HAS_FAISS and self.index is not None:
                faiss.write_index(self.index, str(self._get_index_file()))
            elif self.vectors:
                with open(self._get_index_file(), 'wb') as f:
                    pickle.dump(self.vectors, f)
            
            with open(self._get_metadata_file(), 'wb') as f:
                pickle.dump(self.metadata, f)
    
    def _init_index(self, dimension: int):
        """Initialize index with given dimension."""
        self.dimension = dimension
        if HAS_FAISS:
            self.index = faiss.IndexFlatIP(dimension)
    
    def add_chunks(self, chunks: List[Dict]):
        """Add blog chunks to the vector store."""
        if not chunks:
            return
        
        texts = [chunk['content'] for chunk in chunks]
        embedding_model = get_embedding_model()
        
        embeddings = embedding_model.encode(texts)
        
        # Normalize for cosine similarity
        if HAS_FAISS:
            faiss.normalize_L2(embeddings)
        else:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            embeddings = embeddings / norms
        
        # Initialize if needed
        if self.index is None and self.dimension is None:
            self._init_index(embedding_model.dimension)
        
        # Add to index
        if HAS_FAISS and self.index is not None:
            self.index.add(embeddings.astype(np.float32))
        else:
            self.vectors.extend([e.astype(np.float32) for e in embeddings])
        
        # Store metadata
        for chunk in chunks:
            self.metadata.append({
                'content': chunk['content'],
                'blog_title': chunk.get('blog_title', 'Unknown'),
                'blog_url': chunk.get('blog_url', ''),
                'chunk_index': chunk.get('chunk_index', 0),
                'total_chunks': chunk.get('total_chunks', 1),
                'metadata': chunk.get('metadata', {})
            })
        
        self._save()
        print(f"Added {len(chunks)} chunks. Total: {len(self.metadata)}")
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[float, Dict]]:
        """Search for most similar chunks to query."""
        if len(self.metadata) == 0:
            return []
        
        embedding_model = get_embedding_model()
        query_embedding = embedding_model.encode([query])
        
        if HAS_FAISS and self.index is not None:
            faiss.normalize_L2(query_embedding)
            scores, indices = self.index.search(query_embedding.astype(np.float32), 
                                                 min(top_k, len(self.metadata)))
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.metadata):
                    results.append((float(score), self.metadata[idx]))
            return results
        else:
            # Fallback: pure numpy cosine similarity
            query_vec = query_embedding[0].astype(np.float32)
            query_norm = np.linalg.norm(query_vec)
            query_norm = 1.0 if query_norm == 0 else query_norm
            query_vec = query_vec / query_norm
            
            all_vectors = np.array(self.vectors)
            similarities = np.dot(all_vectors, query_vec)
            
            # Get top-k
            top_indices = np.argsort(similarities)[::-1][:min(top_k, len(similarities))]
            return [(float(similarities[idx]), self.metadata[idx]) for idx in top_indices]
    
    def clear(self):
        """Clear all data."""
        self.index = None
        self.vectors = []
        self.metadata = []
        self.dimension = None
        
        for f in [self._get_index_file(), self._get_metadata_file()]:
            if f.exists():
                f.unlink()
    
    def get_stats(self) -> Dict:
        """Get statistics."""
        return {
            'total_vectors': len(self.metadata),
            'dimension': self.dimension,
            'store_path': str(self.store_path),
            'unique_blogs': len(set(m['blog_title'] for m in self.metadata))
        }
