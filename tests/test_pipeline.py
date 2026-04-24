"""Test suite for the blog generation pipeline."""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils.chunking import recursive_character_chunking, chunk_blog
from src.utils.embeddings import get_embedding_model
from src.utils.vector_store import VectorStore
from src.services.blog_retrieval import BlogRetrievalService
from src.services.seo_research import SEOResearchService
from src.services.blog_generator import BlogGeneratorService
from src.agent.orchestrator import AgentOrchestrator


class TestChunking:
    """Test text chunking functionality."""
    
    def test_chunking_basic(self):
        text = "This is a simple test. " * 100
        chunks = recursive_character_chunking(text, chunk_size=100, chunk_overlap=20)
        assert len(chunks) > 0
        assert all(len(c) > 0 for c in chunks)
    
    def test_chunking_overlap(self):
        text = "Paragraph one. " * 50 + "\n\n" + "Paragraph two. " * 50
        chunks = recursive_character_chunking(text, chunk_size=100, chunk_overlap=20)
        assert len(chunks) >= 2
    
    def test_chunk_blog(self):
        text = "# Title\n\nThis is content. " * 50
        chunks = chunk_blog(text, "Test Blog", "/test")
        assert len(chunks) > 0
        assert all(c["blog_title"] == "Test Blog" for c in chunks)


class TestEmbeddings:
    """Test embedding model."""
    
    def test_embedding_dimension(self):
        model = get_embedding_model()
        emb = model.encode(["test sentence"])
        assert emb.shape[1] == model.dimension
        assert model.dimension == 384  # all-MiniLM-L6-v2
    
    def test_embedding_similarity(self):
        model = get_embedding_model()
        embs = model.encode([
            "machine learning is great",
            "artificial intelligence and ML",
            "pizza is delicious"
        ])
        # First two should be more similar than first and third
        import numpy as np
        sim_12 = np.dot(embs[0], embs[1])
        sim_13 = np.dot(embs[0], embs[2])
        assert sim_12 > sim_13


class TestVectorStore:
    """Test vector store operations."""
    
    def test_add_and_search(self):
        store = VectorStore()
        store.clear()
        
        chunks = [
            {"content": "RAG pipelines are important for AI", "blog_title": "Blog1", "chunk_index": 0},
            {"content": "Vector databases store embeddings", "blog_title": "Blog2", "chunk_index": 0},
            {"content": "Machine learning models process data", "blog_title": "Blog3", "chunk_index": 0},
        ]
        
        store.add_chunks(chunks)
        assert store.get_stats()["total_vectors"] == 3
        
        results = store.search("RAG and vector search", top_k=2)
        assert len(results) <= 2
        assert len(results) > 0
    
    def test_persistence(self):
        store = VectorStore()
        store.clear()
        store.add_chunks([{"content": "test", "blog_title": "Test", "chunk_index": 0}])
        
        # Load new instance
        store2 = VectorStore()
        stats = store2.get_stats()
        assert stats["total_vectors"] == 1


class TestBlogRetrieval:
    """Test blog retrieval service."""
    
    def test_ingest_and_search(self, tmp_path):
        service = BlogRetrievalService(blogs_dir=str(tmp_path))
        service.vector_store.clear()
        
        # Create test blog
        blog_file = tmp_path / "test-blog.md"
        blog_file.write_text("# Test Blog\n\nThis is about RAG and vector search.")
        
        result = service.ingest_blogs(str(tmp_path))
        assert result["ingested"] == 1
        assert result["chunks"] > 0
        
        # Search
        results = service.search_similar_blogs("RAG vector search", top_k=1)
        assert len(results) > 0


class TestSEOResearch:
    """Test SEO research service."""
    
    def test_mock_research(self):
        service = SEOResearchService(api_key="")
        analysis = service.research_topic("Building RAG Pipelines")
        
        assert analysis.target_keyword == "Building RAG Pipelines"
        assert analysis.avg_word_count > 0
        assert len(analysis.common_headings) > 0
        assert len(analysis.content_gaps) > 0


class TestBlogGenerator:
    """Test blog generation service."""
    
    def test_mock_generation(self):
        service = BlogGeneratorService()
        from src.models.schemas import SEOAnalysis, ExistingBlogMatch
        
        # Test from SEO research
        seo = SEOAnalysis(
            target_keyword="Test Topic",
            avg_word_count=1500,
            recommended_angle="Comprehensive guide"
        )
        post = service.generate_from_seo_research("Test Topic", seo)
        
        assert len(post.content) > 500
        assert post.word_count > 0
        assert len(post.keywords) > 0
        assert len(post.headings) > 0


class TestOrchestrator:
    """Test agent orchestrator."""
    
    def test_end_to_end(self, tmp_path):
        # Setup minimal library
        retrieval = BlogRetrievalService(blogs_dir=str(tmp_path))
        retrieval.vector_store.clear()
        
        blog = tmp_path / "sample.md"
        blog.write_text("# AI Agents\n\nAI agents are systems that autonomously perform tasks.")
        retrieval.ingest_blogs(str(tmp_path))
        
        orchestrator = AgentOrchestrator(blog_retrieval=retrieval)
        output = orchestrator.run("AI Agent Systems", generate_image=False)
        
        assert output.blog_post is not None
        assert len(output.execution_log) > 0
        assert output.blog_post.word_count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
