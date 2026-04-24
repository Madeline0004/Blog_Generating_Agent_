"""
Agent Orchestrator - Core decision logic and state management.

Implements a state machine that:
1. Validates input
2. Checks blog library for similar content
3. Branches to appropriate path (existing blog vs SEO research)
4. Generates blog post with proper context
5. Optionally generates featured image
6. Returns complete output with execution log

Error Handling:
- Each state has fallback logic
- LLM failures fall back to mock generation
- Search failures fall back to SEO research branch
- All errors are logged in execution_log
"""

from typing import List, Optional
from enum import Enum

from src.config import SIMILARITY_THRESHOLD
from src.models.schemas import AgentOutput, BlogPost, GeneratedImage, SEOAnalysis, ExistingBlogMatch
from src.services.blog_retrieval import BlogRetrievalService
from src.services.seo_research import SEOResearchService
from src.services.blog_generator import BlogGeneratorService
from src.services.image_generator import ImageGeneratorService
from src.services.publisher import PublisherService


class AgentState(Enum):
    INIT = "init"
    CHECK_LIBRARY = "check_library"
    BRANCH = "branch"
    USE_EXISTING = "use_existing"
    SEO_RESEARCH = "seo_research"
    GENERATE = "generate"
    GENERATE_IMAGE = "generate_image"
    OUTPUT = "output"
    ERROR = "error"


class AgentOrchestrator:
    """
    Orchestrates the blog generation workflow.
    
    State Machine:
    
    INIT → CHECK_LIBRARY → BRANCH
                              │
                    ┌─────────┴─────────┐
                    │                   │
            Similar Found        No Match
                    │                   │
                    ▼                   ▼
              USE_EXISTING      SEO_RESEARCH
                    │                   │
                    └─────────┬─────────┘
                              │
                              ▼
                         GENERATE → GENERATE_IMAGE → OUTPUT
    
    Branching Logic:
    - If similarity score >= threshold: USE_EXISTING
    - If similarity score < threshold or no results: SEO_RESEARCH
    - If retrieval fails entirely: fallback to SEO_RESEARCH
    """
    
    def __init__(
        self,
        blog_retrieval: BlogRetrievalService = None,
        seo_research: SEOResearchService = None,
        blog_generator: BlogGeneratorService = None,
        image_generator: ImageGeneratorService = None,
        publisher: PublisherService = None
    ):
        self.blog_retrieval = blog_retrieval or BlogRetrievalService()
        self.seo_research = seo_research or SEOResearchService()
        self.blog_generator = blog_generator or BlogGeneratorService()
        self.image_generator = image_generator or ImageGeneratorService()
        self.publisher = publisher or PublisherService()
        
        self.execution_log: List[str] = []
    
    def run(
        self,
        title: str,
        generate_image: bool = False,
        output_dir: str = None
    ) -> AgentOutput:
        """
        Run the complete blog generation pipeline.
        
        Args:
            title: Blog title/topic
            generate_image: Whether to generate featured image
            output_dir: Custom output directory
        
        Returns:
            AgentOutput with blog post, metadata, and execution log
        """
        self.execution_log = []
        self._log(f"Starting blog generation for: '{title}'")
        
        try:
            # Step 1: Check existing blog library
            existing_blog = self._check_library(title)
            
            # Step 2: Branch based on result
            if existing_blog:
                blog_post = self._generate_from_existing(title, existing_blog)
            else:
                blog_post = self._generate_from_research(title)
            
            # Step 3: Optional image generation
            featured_image = None
            if generate_image:
                featured_image = self._generate_image(blog_post)
            
            # Step 4: Publish output
            research_used = None if existing_blog else self.seo_research.research_topic(title)
            
            # Create publisher with custom output dir if specified
            publisher = PublisherService(output_dir) if output_dir else self.publisher
            
            output_paths = publisher.publish(
                blog_post=blog_post,
                featured_image=featured_image,
                research_used=research_used,
                existing_blog_used=existing_blog,
                execution_log=self.execution_log
            )
            
            self._log(f"Blog generation complete. Published to: {output_paths.get('blog_post', 'N/A')}")
            
            return AgentOutput(
                blog_post=blog_post,
                featured_image=featured_image,
                research_used=research_used,
                existing_blog_used=existing_blog,
                execution_log=self.execution_log
            )
            
        except Exception as e:
            self._log(f"CRITICAL ERROR: {str(e)}")
            # Return best-effort output even on failure
            return AgentOutput(
                blog_post=BlogPost(title=title, content=f"Error generating blog: {str(e)}"),
                execution_log=self.execution_log
            )
    
    def _check_library(self, title: str) -> Optional[ExistingBlogMatch]:
        """Step 1: Search for similar existing blogs."""
        self._log("State: CHECK_LIBRARY - Searching existing blog library")
        
        try:
            stats = self.blog_retrieval.get_blog_stats()
            self._log(f"Library stats: {stats}")
            
            match = self.blog_retrieval.find_similar_blog(title)
            
            if match:
                self._log(
                    f"Found similar blog: '{match.blog_title}' "
                    f"(score: {match.similarity_score:.3f} >= {SIMILARITY_THRESHOLD})"
                )
                return match
            else:
                self._log(f"No similar blog found (threshold: {SIMILARITY_THRESHOLD})")
                return None
                
        except Exception as e:
            self._log(f"Library check failed: {e}")
            return None
    
    def _generate_from_existing(
        self,
        title: str,
        existing_blog: ExistingBlogMatch
    ) -> BlogPost:
        """Step 2A: Generate using existing blog as reference."""
        self._log("State: USE_EXISTING - Generating from existing blog reference")
        
        try:
            blog_post = self.blog_generator.generate_from_existing_blog(title, existing_blog)
            self._log(
                f"Generated blog from existing reference: "
                f"{blog_post.word_count} words, {len(blog_post.headings)} headings"
            )
            return blog_post
            
        except Exception as e:
            self._log(f"Generation from existing failed: {e}")
            # Fallback: try SEO research path
            self._log("Falling back to SEO research path")
            return self._generate_from_research(title)
    
    def _generate_from_research(self, title: str) -> BlogPost:
        """Step 2B: Generate using external SEO research."""
        self._log("State: SEO_RESEARCH - Performing external research")
        
        try:
            seo_analysis = self.seo_research.research_topic(title)
            self._log(
                f"Research complete: avg word count {seo_analysis.avg_word_count}, "
                f"angle: {seo_analysis.recommended_angle[:50]}..."
            )
            
            blog_post = self.blog_generator.generate_from_seo_research(title, seo_analysis)
            self._log(
                f"Generated blog from research: "
                f"{blog_post.word_count} words, {len(blog_post.headings)} headings"
            )
            return blog_post
            
        except Exception as e:
            self._log(f"Research/generation failed: {e}")
            # Final fallback: mock generation
            self._log("Using fallback generation")
            from src.models.schemas import SEOAnalysis
            mock_seo = SEOAnalysis(
                target_keyword=title,
                recommended_angle="Comprehensive guide"
            )
            return self.blog_generator.generate_from_seo_research(title, mock_seo)
    
    def _generate_image(self, blog_post: BlogPost) -> Optional[GeneratedImage]:
        """Step 4: Generate featured image."""
        self._log("State: GENERATE_IMAGE - Creating featured image")
        
        try:
            image = self.image_generator.generate_featured_image(
                blog_title=blog_post.title,
                keywords=blog_post.keywords
            )
            
            if image.image_path:
                self._log(f"Image generated: {image.image_path}")
            else:
                self._log(f"Image prompt created (no API key): {image.prompt[:80]}...")
            
            return image
            
        except Exception as e:
            self._log(f"Image generation failed: {e}")
            return None
    
    def _log(self, message: str):
        """Add message to execution log."""
        self.execution_log.append(message)
        print(f"[AGENT] {message}")
