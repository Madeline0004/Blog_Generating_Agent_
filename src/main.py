"""
Main entry point for the Blog Generation Agent.

CLI Usage:
    python -m src.main "How to Build a RAG Pipeline"
    python -m src.main "AI Agent Orchestration" --generate-image
    python -m src.main "Vector Databases Guide" --output-dir ./my_blogs
"""

import argparse
import sys
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.orchestrator import AgentOrchestrator
from src.services.blog_retrieval import BlogRetrievalService
from src.config import SAMPLE_BLOGS_DIR


def setup_sample_library():
    """Ingest sample blogs to populate the library for demonstration."""
    retrieval = BlogRetrievalService()
    stats = retrieval.get_blog_stats()
    
    if stats['total_vectors'] == 0:
        print("Ingesting sample blogs into library...")
        result = retrieval.ingest_blogs(SAMPLE_BLOGS_DIR)
        print(f"Ingested {result['ingested']} blogs ({result['chunks']} chunks)")
    else:
        print(f"Library already has {stats['total_vectors']} chunks from {stats['unique_blogs']} blogs")


def main():
    parser = argparse.ArgumentParser(
        description="Blog Generation Agent - AI-powered blog post creation"
    )
    parser.add_argument(
        "title",
        help="Blog title/topic to generate"
    )
    parser.add_argument(
        "--generate-image", "-i",
        action="store_true",
        help="Generate a featured image (requires OpenAI API key)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=None,
        help="Custom output directory for generated blog"
    )
    parser.add_argument(
        "--ingest-only",
        action="store_true",
        help="Only ingest sample blogs, don't generate"
    )
    
    args = parser.parse_args()
    
    # Setup library
    setup_sample_library()
    
    if args.ingest_only:
        print("Ingestion complete. Exiting.")
        return
    
    # Run agent
    print(f"\n{'='*60}")
    print(f"Generating blog: '{args.title}'")
    print(f"{'='*60}\n")
    
    orchestrator = AgentOrchestrator()
    output = orchestrator.run(
        title=args.title,
        generate_image=args.generate_image,
        output_dir=args.output_dir
    )
    
    # Print summary
    print(f"\n{'='*60}")
    print("GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"Title: {output.blog_post.title}")
    print(f"Word Count: {output.blog_post.word_count}")
    print(f"Source: {output.blog_post.source}")
    print(f"Headings: {len(output.blog_post.headings)}")
    print(f"\nExecution Log:")
    for entry in output.execution_log:
        print(f"  - {entry}")
    
    if output.existing_blog_used:
        print(f"\nExisting blog used: {output.existing_blog_used.blog_title}")
    
    if output.featured_image:
        if output.featured_image.image_path:
            print(f"\nFeatured image: {output.featured_image.image_path}")
        else:
            print(f"\nImage prompt: {output.featured_image.prompt}")
    
    print(f"\nKeywords: {', '.join(output.blog_post.keywords)}")
    print(f"\nExcerpt:")
    print(output.blog_post.excerpt[:300] + "..." if len(output.blog_post.excerpt) > 300 else output.blog_post.excerpt)


if __name__ == "__main__":
    main()
