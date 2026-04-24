"""General utility helpers."""

import re
import json
from typing import Dict, Any
from datetime import datetime


def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation: 1 token ~ 0.75 words)."""
    return int(len(text.split()) * 1.3)


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def extract_headings(markdown: str) -> list:
    """Extract H1, H2, H3 headings from markdown."""
    pattern = r'^(#{1,3})\s+(.+)$'
    matches = re.findall(pattern, markdown, re.MULTILINE)
    return [f"{level} {title}" for level, title in matches]


def sanitize_filename(title: str) -> str:
    """Create a safe filename from a title."""
    safe = re.sub(r'[^\w\s-]', '', title.lower())
    safe = re.sub(r'[-\s]+', '-', safe)
    return safe.strip('-')[:50]


def format_blog_for_output(blog_data: Dict[str, Any]) -> str:
    """Format blog data as a readable markdown document."""
    lines = [
        f"# {blog_data.get('title', 'Untitled')}",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "---",
        "",
        blog_data.get('content', ''),
        "",
        "---",
        "",
        "## Metadata",
        "",
        f"- **Source**: {blog_data.get('source', 'unknown')}",
        f"- **Word Count**: {blog_data.get('word_count', 0)}",
        f"- **Keywords**: {', '.join(blog_data.get('keywords', []))}",
    ]
    
    if blog_data.get('internal_links'):
        lines.append("")
        lines.append("## Suggested Internal Links")
        for link in blog_data['internal_links']:
            lines.append(f"- [{link.get('title', 'Link')}]({link.get('url', '#')})")
    
    return "\n".join(lines)


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to fit within max_tokens."""
    tokens = estimate_tokens(text)
    if tokens <= max_tokens:
        return text
    
    words = text.split()
    # Estimate words from tokens
    target_words = int(max_tokens / 1.3)
    return " ".join(words[:target_words]) + "..."


def safe_json_loads(text: str) -> Dict:
    """Safely parse JSON, handling common LLM formatting issues."""
    # Try to extract JSON from markdown code blocks
    if "```json" in text:
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
    elif "```" in text:
        match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
    
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {}
