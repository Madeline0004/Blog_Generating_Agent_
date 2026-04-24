"""Text chunking utilities for the RAG pipeline."""

import re
from typing import List
from src.config import CHUNK_SIZE, CHUNK_OVERLAP


def recursive_character_chunking(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP
) -> List[str]:
    """
    Recursively chunk text by splitting on paragraph, then sentence boundaries.
    
    Strategy:
    1. First split by paragraphs (double newlines)
    2. If paragraph > chunk_size, split by sentences
    3. If sentence > chunk_size, split by words
    4. Maintain overlap between chunks to preserve context
    
    Why this chunk size and overlap:
    - 512 tokens (~400-500 words) provides enough context for semantic meaning
      while keeping chunks focused enough for precise retrieval
    - 128 tokens (25% overlap) ensures continuity at chunk boundaries so that
      concepts spanning two chunks aren't lost
    """
    if not text or not text.strip():
        return []
    
    # Clean text
    text = text.strip()
    
    # Split into paragraphs first
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    # Estimate tokens: roughly 1.3 tokens per word
    def estimate_tokens(text_segment: str) -> int:
        return int(len(text_segment.split()) * 1.3)
    
    for paragraph in paragraphs:
        para_tokens = estimate_tokens(paragraph)
        
        # If single paragraph exceeds chunk size, split by sentences
        if para_tokens > chunk_size:
            # Flush current chunk if it has content
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_length = 0
            
            # Split paragraph by sentences
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            
            for sentence in sentences:
                sent_tokens = estimate_tokens(sentence)
                
                if sent_tokens > chunk_size:
                    # Sentence too long, split by words with overlap
                    words = sentence.split()
                    word_chunk_size = int(chunk_size / 1.3)
                    word_overlap = int(chunk_overlap / 1.3)
                    
                    start = 0
                    while start < len(words):
                        end = min(start + word_chunk_size, len(words))
                        chunk_words = words[start:end]
                        chunks.append(" ".join(chunk_words))
                        start = end - word_overlap if end < len(words) else end
                else:
                    # Add sentence to current chunk if it fits
                    if current_length + sent_tokens <= chunk_size:
                        current_chunk.append(sentence)
                        current_length += sent_tokens
                    else:
                        # Flush and start new chunk
                        if current_chunk:
                            chunks.append(" ".join(current_chunk))
                        
                        # Carry over overlap from previous chunk
                        if current_chunk and chunk_overlap > 0:
                            overlap_text = get_overlap_text(current_chunk, chunk_overlap)
                            current_chunk = [overlap_text, sentence] if overlap_text else [sentence]
                            current_length = estimate_tokens(" ".join(current_chunk))
                        else:
                            current_chunk = [sentence]
                            current_length = sent_tokens
        else:
            # Try to add paragraph to current chunk
            if current_length + para_tokens <= chunk_size:
                current_chunk.append(paragraph)
                current_length += para_tokens
            else:
                # Flush current chunk
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                
                # Start new chunk with this paragraph
                current_chunk = [paragraph]
                current_length = para_tokens
    
    # Don't forget the last chunk
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
    
    return chunks


def get_overlap_text(chunk_parts: List[str], overlap_tokens: int) -> str:
    """Extract overlap text from the end of chunk parts."""
    overlap_text = []
    overlap_length = 0
    word_overlap = int(overlap_tokens / 1.3)
    
    # Work backwards through parts
    all_text = " ".join(chunk_parts)
    words = all_text.split()
    
    if len(words) <= word_overlap:
        return all_text
    
    overlap_words = words[-word_overlap:]
    return " ".join(overlap_words)


def chunk_blog(text: str, blog_title: str, blog_url: str = None) -> List[dict]:
    """
    Chunk a blog post and return chunks with metadata.
    """
    chunks = recursive_character_chunking(text)
    
    return [
        {
            "content": chunk,
            "blog_title": blog_title,
            "blog_url": blog_url or "",
            "chunk_index": i,
            "total_chunks": len(chunks),
            "metadata": {
                "source_type": "existing_blog",
                "chunk_size_tokens": CHUNK_SIZE,
                "overlap_tokens": CHUNK_OVERLAP,
            }
        }
        for i, chunk in enumerate(chunks)
    ]
