"""Pydantic data models for the blog generation agent."""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class BlogChunk(BaseModel):
    """A chunk of blog content with metadata."""
    content: str = Field(description="The text content of the chunk")
    blog_title: str = Field(description="Title of the source blog")
    blog_url: Optional[str] = Field(default=None, description="URL of source blog")
    chunk_index: int = Field(description="Index of this chunk in the blog")
    total_chunks: int = Field(description="Total number of chunks")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class SearchResult(BaseModel):
    """Result of semantic search over blog library."""
    chunk: BlogChunk
    score: float = Field(description="Similarity score")


class ExistingBlogMatch(BaseModel):
    """Result when a similar existing blog is found."""
    blog_title: str
    similarity_score: float
    matched_chunks: List[SearchResult]
    full_content: Optional[str] = None


class SEOAnalysis(BaseModel):
    """SEO research analysis of top-ranking content."""
    target_keyword: str
    top_rankings: List[dict] = Field(default_factory=list, description="Top search results")
    avg_word_count: int = Field(default=0)
    common_headings: List[str] = Field(default_factory=list)
    content_gaps: List[str] = Field(default_factory=list)
    recommended_angle: str = Field(default="")
    competitor_structures: List[dict] = Field(default_factory=list)


class BlogPost(BaseModel):
    """Generated blog post output."""
    title: str
    content: str = Field(description="Full markdown content")
    excerpt: str = Field(default="", description="SEO meta description")
    keywords: List[str] = Field(default_factory=list)
    headings: List[str] = Field(default_factory=list)
    word_count: int = Field(default=0)
    generated_at: datetime = Field(default_factory=datetime.now)
    source: str = Field(default="", description="existing_blog or seo_research")
    internal_links: List[dict] = Field(default_factory=list)


class GeneratedImage(BaseModel):
    """Generated featured image."""
    prompt: str
    image_path: Optional[str] = None
    image_url: Optional[str] = None


class AgentOutput(BaseModel):
    """Final output from the blog generation agent."""
    blog_post: BlogPost
    featured_image: Optional[GeneratedImage] = None
    research_used: Optional[SEOAnalysis] = None
    existing_blog_used: Optional[ExistingBlogMatch] = None
    execution_log: List[str] = Field(default_factory=list)
