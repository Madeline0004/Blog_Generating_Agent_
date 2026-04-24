"""
Publisher Service - Output formatting and file generation.

Handles saving generated blog posts, images, and metadata to disk.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from src.config import DEFAULT_OUTPUT_DIR
from src.models.schemas import BlogPost, GeneratedImage, SEOAnalysis, ExistingBlogMatch
from src.utils.helpers import format_blog_for_output, sanitize_filename


class PublisherService:
    """
    Service for publishing/saving agent outputs.
    
    Generates:
    - Blog post markdown file
    - Metadata JSON file
    - Summary report
    """
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or DEFAULT_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def publish(
        self,
        blog_post: BlogPost,
        featured_image: GeneratedImage = None,
        research_used: SEOAnalysis = None,
        existing_blog_used: ExistingBlogMatch = None,
        execution_log: list = None
    ) -> Dict[str, str]:
        """
        Publish all outputs to the output directory.
        
        Returns paths to all generated files.
        """
        safe_title = sanitize_filename(blog_post.title)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{safe_title}_{timestamp}"
        
        publish_dir = self.output_dir / folder_name
        publish_dir.mkdir(parents=True, exist_ok=True)
        
        output_paths = {}
        
        # Save blog post as markdown
        md_content = format_blog_for_output(blog_post.model_dump())
        md_path = publish_dir / "blog_post.md"
        md_path.write_text(md_content, encoding='utf-8')
        output_paths['blog_post'] = str(md_path)
        
        # Save metadata JSON
        metadata = {
            'title': blog_post.title,
            'generated_at': blog_post.generated_at.isoformat(),
            'word_count': blog_post.word_count,
            'keywords': blog_post.keywords,
            'headings': blog_post.headings,
            'excerpt': blog_post.excerpt,
            'source': blog_post.source,
            'internal_links': blog_post.internal_links,
            'research_used': research_used.model_dump() if research_used else None,
            'existing_blog_used': {
                'blog_title': existing_blog_used.blog_title,
                'similarity_score': existing_blog_used.similarity_score
            } if existing_blog_used else None,
            'featured_image': {
                'prompt': featured_image.prompt if featured_image else None,
                'image_path': featured_image.image_path if featured_image else None
            },
            'execution_log': execution_log or []
        }
        
        json_path = publish_dir / "metadata.json"
        json_path.write_text(json.dumps(metadata, indent=2, default=str), encoding='utf-8')
        output_paths['metadata'] = str(json_path)
        
        # Save raw content
        raw_path = publish_dir / "raw_content.md"
        raw_path.write_text(blog_post.content, encoding='utf-8')
        output_paths['raw_content'] = str(raw_path)
        
        # If image was generated externally and saved, note it
        if featured_image and featured_image.image_path:
            output_paths['featured_image'] = featured_image.image_path
        
        # Save execution log
        if execution_log:
            log_path = publish_dir / "execution_log.txt"
            log_path.write_text('\n'.join(execution_log), encoding='utf-8')
            output_paths['execution_log'] = str(log_path)
        
        print(f"\nPublished to: {publish_dir}")
        print(f"Files: {', '.join(output_paths.keys())}")
        
        return output_paths
