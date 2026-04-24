"""
Blog Retrieval Service - The core RAG pipeline.

This module implements the full retrieval pipeline:
1. Blog ingestion (reading files, extracting text)
2. Chunking (512 tokens, 128 overlap)
3. Embedding (all-MiniLM-L6-v2)
4. Indexing (FAISS, triggered on ingestion)
5. Retrieval (semantic search + re-ranking)

Index Freshness:
- Index is built when blogs are ingested via ingest_blogs()
- The index persists to disk (FAISS index + metadata pickle)
- To refresh: call clear() then re-ingest, or implement incremental updates
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Dict

from src.config import SAMPLE_BLOGS_DIR, SIMILARITY_THRESHOLD, CHUNK_SIZE, CHUNK_OVERLAP
from src.models.schemas import SearchResult, ExistingBlogMatch, BlogChunk
from src.utils.chunking import chunk_blog
from src.utils.vector_store import VectorStore


class BlogRetrievalService:
    """
    Service for ingesting, indexing, and retrieving blog content.
    
    Full RAG Pipeline Implementation:
    
    INGESTION:
    - Reads markdown/blog files from directory
    - Extracts text content and metadata
    
    CHUNKING:
    - Recursive character chunking
    - Chunk size: 512 tokens, Overlap: 128 tokens
    - Why: Preserves paragraph boundaries, 25% overlap maintains continuity
    
    EMBEDDING:
    - sentence-transformers/all-MiniLM-L6-v2
    - 384 dimensions, L2-normalized
    - Runs locally, no API dependency
    
    INDEXING:
    - FAISS IndexFlatIP (Inner Product = Cosine Similarity for normalized vectors)
    - Triggered on-demand during ingestion
    - Persisted to disk at VECTOR_STORE_PATH
    
    RETRIEVAL:
    - Encode query → search FAISS index → return top-k results
    - Results include similarity score and full metadata
    """
    
    def __init__(self, blogs_dir: str = None):
        self.blogs_dir = Path(blogs_dir or SAMPLE_BLOGS_DIR)
        self.vector_store = VectorStore()
    
    def ingest_blog_file(self, file_path: Path) -> List[Dict]:
        """Ingest a single blog file and return chunked data."""
        if not file_path.exists():
            raise FileNotFoundError(f"Blog file not found: {file_path}")
        
        content = file_path.read_text(encoding='utf-8')
        
        # Extract title from first H1 or filename
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else file_path.stem.replace('-', ' ').title()
        
        # Create URL-like identifier
        url = f"/blog/{file_path.stem}"
        
        # Chunk the blog
        chunks = chunk_blog(content, blog_title=title, blog_url=url)
        
        return chunks
    
    def ingest_blogs(self, directory: str = None) -> Dict:
        """
        Ingest all blog files from directory and build search index.
        
        This is the indexing trigger - call this to add blogs to the vector store.
        For keeping the index fresh, you could:
        1. Watch for file changes and re-ingest modified files
        2. Run on a schedule (cron job)
        3. Trigger via CI/CD when new blogs are published
        """
        target_dir = Path(directory or self.blogs_dir)
        
        if not target_dir.exists():
            return {"ingested": 0, "chunks": 0, "error": f"Directory not found: {target_dir}"}
        
        all_chunks = []
        files_processed = 0
        
        # Support .md and .txt files
        for ext in ['*.md', '*.txt', '*.markdown']:
            for file_path in target_dir.glob(ext):
                try:
                    chunks = self.ingest_blog_file(file_path)
                    all_chunks.extend(chunks)
                    files_processed += 1
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
        
        # Add to vector store
        if all_chunks:
            self.vector_store.add_chunks(all_chunks)
        
        return {
            "ingested": files_processed,
            "chunks": len(all_chunks),
            "vector_store_stats": self.vector_store.get_stats()
        }
    
    def search_similar_blogs(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        Search for blogs similar to the query.
        
        Returns top-k most similar chunks with their scores.
        Score is cosine similarity (0 to 1, higher = more similar).
        """
        results = self.vector_store.search(query, top_k=top_k)
        
        search_results = []
        for score, metadata in results:
            chunk = BlogChunk(
                content=metadata['content'],
                blog_title=metadata['blog_title'],
                blog_url=metadata['blog_url'],
                chunk_index=metadata['chunk_index'],
                total_chunks=metadata['total_chunks'],
                metadata=metadata.get('metadata', {})
            )
            search_results.append(SearchResult(chunk=chunk, score=score))
        
        return search_results
    
    def find_similar_blog(self, title: str, threshold: float = None) -> Optional[ExistingBlogMatch]:
        """
        Determine if a similar blog already exists.
        
        'Similar' is defined as semantic similarity using dense embeddings.
        If any chunk scores above threshold, we consider it a match.
        
        We then retrieve all chunks from that blog to get full context.
        """
        threshold = threshold or SIMILARITY_THRESHOLD
        
        # Search for similar content
        results = self.search_similar_blogs(title, top_k=10)
        
        if not results:
            return None
        
        # Find the best match across all results
        best_result = max(results, key=lambda r: r.score)
        
        if best_result.score < threshold:
            return None  # No sufficiently similar blog found
        
        matched_blog_title = best_result.chunk.blog_title
        
        # Retrieve all chunks from this blog for full context
        blog_chunks = [
            r for r in results 
            if r.chunk.blog_title == matched_blog_title
        ]
        
        # Sort by chunk_index to reconstruct order
        blog_chunks.sort(key=lambda r: r.chunk.chunk_index)
        
        # Reconstruct full content
        full_content = "\n\n".join([r.chunk.content for r in blog_chunks])
        
        return ExistingBlogMatch(
            blog_title=matched_blog_title,
            similarity_score=best_result.score,
            matched_chunks=blog_chunks,
            full_content=full_content
        )
    
    def get_blog_stats(self) -> Dict:
        """Get statistics about the blog library."""
        return self.vector_store.get_stats()
    
    def clear_library(self):
        """Clear all ingested blogs and rebuild from scratch."""
        self.vector_store.clear()
