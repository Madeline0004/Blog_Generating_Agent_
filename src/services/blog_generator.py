"""
Blog Generator Service - LLM-powered blog post generation.

Uses OpenAI or Anthropic APIs to generate SEO-optimized, well-structured
blog posts based on research context.
"""

import os
from typing import Optional, Dict, List

from src.config import (
    OPENAI_API_KEY, ANTHROPIC_API_KEY, DEFAULT_LLM_MODEL,
    MAX_TOKENS, TEMPERATURE
)
from src.models.schemas import BlogPost, SEOAnalysis, ExistingBlogMatch
from src.utils.helpers import count_words, extract_headings, estimate_tokens, truncate_to_tokens

# Try imports
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class BlogGeneratorService:
    """
    Service for generating blog posts using LLM APIs.
    
    Supports OpenAI and Anthropic models.
    Handles prompt construction, context window management, and
    output formatting.
    
    If no API keys are configured, falls back to high-quality mock generation
    that demonstrates the prompt structure and output format.
    """
    
    def __init__(self):
        self.openai_key = OPENAI_API_KEY
        self.anthropic_key = ANTHROPIC_API_KEY
        self.model = DEFAULT_LLM_MODEL
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE
        
        self.client = None
        self.provider = None
        
        if self.openai_key and HAS_OPENAI:
            try:
                self.client = openai.OpenAI(api_key=self.openai_key)
                self.provider = "openai"
            except Exception:
                pass
        
        if not self.client and self.anthropic_key and HAS_ANTHROPIC:
            try:
                self.client = anthropic.Anthropic(api_key=self.anthropic_key)
                self.provider = "anthropic"
                self.model = "claude-3-haiku-20240307"
            except Exception:
                pass
    
    def generate_from_existing_blog(self, title: str, existing_blog: ExistingBlogMatch) -> BlogPost:
        """Generate using existing blog as reference."""
        context = truncate_to_tokens(existing_blog.full_content or "", 2000)
        
        system_prompt = """You are an expert technical writer and content strategist.
Your task is to write a new, differentiated blog post on a topic that the company has covered before.

Guidelines:
- Study the existing blog's structure, tone, and depth
- Write a FRESH post that covers a different angle, updates information, or goes deeper
- Do NOT copy or paraphrase the existing content extensively
- Include proper H1, H2, H3 structure
- Write an SEO-optimized meta description/excerpt
- Suggest 2-3 internal links back to the existing post
- Match a professional, informative tone
- Be comprehensive but concise (aim for 1500-2500 words)"""

        user_prompt = f"""Title to write about: {title}

Existing blog for reference (STUDY but do NOT copy):
---
{context}
---

Please write a complete, publication-ready blog post in markdown format.
Include:
1. SEO-optimized H1 title
2. Engaging introduction
3. Well-structured body with H2/H3 headings
4. Actionable conclusion
5. An excerpt/meta description (2-3 sentences)
6. A list of target keywords
7. Suggested internal links to the existing post

Format as clean markdown without code block wrappers."""

        content = self._call_llm(system_prompt, user_prompt)
        return self._format_output(title, content, source="existing_blog")
    
    def generate_from_seo_research(self, title: str, seo_analysis: SEOAnalysis) -> BlogPost:
        """Generate using SEO research as context."""
        research_context = self._format_seo_context(seo_analysis)
        
        system_prompt = """You are an expert SEO-focused technical writer.
Your task is to write a blog post designed to rank well in search engines.

Guidelines:
- Analyze the competitive landscape provided
- Match or exceed the average word count of top-ranking posts
- Use the recommended content angle
- Include common headings/topics that competitors cover
- Fill identified content gaps with unique insights
- Write with proper H1, H2, H3 structure
- Include an SEO meta description
- Use target keywords naturally throughout
- Write in a professional, authoritative tone
- Include practical examples and actionable advice"""

        user_prompt = f"""Title to write about: {title}

SEO Research:
{research_context}

Please write a complete, publication-ready blog post in markdown format.
Include:
1. SEO-optimized H1 title
2. Engaging introduction that hooks readers
3. Well-structured body with H2/H3 headings
4. Data-backed or research-backed points where relevant
5. Actionable conclusion
6. An excerpt/meta description (2-3 sentences)
7. A list of target keywords

Format as clean markdown without code block wrappers."""

        content = self._call_llm(system_prompt, user_prompt)
        return self._format_output(title, content, source="seo_research")
    
    def _format_seo_context(self, analysis: SEOAnalysis) -> str:
        lines = [
            f"Target Keyword: {analysis.target_keyword}",
            f"Recommended Angle: {analysis.recommended_angle}",
            f"Competitive Word Count: ~{analysis.avg_word_count} words",
            "",
            "Common Headings from Top Performers:",
        ]
        for h in analysis.common_headings[:6]:
            lines.append(f"- {h}")
        
        lines.extend(["", "Content Gaps to Fill:"])
        for gap in analysis.content_gaps[:4]:
            lines.append(f"- {gap}")
        
        lines.extend(["", "Top Competitors:"])
        for comp in analysis.competitor_structures[:3]:
            lines.append(f"- {comp['title']} ({comp['word_count']} words)")
        
        return "\n".join(lines)
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call LLM or return mock output."""
        if not self.client:
            return self._mock_generate(user_prompt)
        
        try:
            if self.provider == "openai":
                return self._call_openai(system_prompt, user_prompt)
            elif self.provider == "anthropic":
                return self._call_anthropic(system_prompt, user_prompt)
            else:
                return self._mock_generate(user_prompt)
        except Exception as e:
            print(f"LLM API call failed: {e}")
            return self._mock_generate(user_prompt)
    
    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        return response.choices[0].message.content
    
    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return response.content[0].text
    
    def _mock_generate(self, prompt: str) -> str:
        """High-quality mock blog for demonstration."""
        title_match = None
        for line in prompt.split('\n'):
            if line.startswith("Title to write about:"):
                title_match = line.replace("Title to write about:", "").strip()
                break
        
        title = title_match or "Understanding AI Agent Orchestration"
        
        return f"""# {title}

In today's rapidly evolving technological landscape, {title.lower()} has become a critical consideration for organizations seeking to maintain competitive advantage. This comprehensive guide explores the fundamentals, advanced strategies, and practical implementation approaches that define success in this domain.

## What Is {title.split(':')[0].strip()}?

At its core, {title.lower()} represents a paradigm shift in how we approach complex problem-solving. Rather than relying on monolithic systems, modern practitioners are embracing modular, intelligent approaches that adapt to changing requirements.

The concept emerged from early research in distributed systems and has since evolved to incorporate machine learning, semantic understanding, and autonomous decision-making capabilities. Today's implementations leverage decades of accumulated knowledge while pushing boundaries in unprecedented directions.

## Why {title.split(':')[0].strip()} Matters Now

Several converging factors have elevated {title.lower()} from niche consideration to strategic imperative:

**1. Data Proliferation**
Organizations now generate petabytes of structured and unstructured data daily. Traditional approaches struggle to extract value at this scale, necessitating more sophisticated methodologies.

**2. Real-Time Requirements**
Customer expectations and competitive pressures demand near-instantaneous responses. Legacy batch-processing approaches cannot meet these requirements, driving adoption of streaming and event-driven architectures.

**3. Complexity Management**
Modern systems comprise thousands of interconnected services. Maintaining coherence across such complexity requires intelligent orchestration and automated governance.

## Core Concepts and Architecture

Understanding {title.lower()} requires familiarity with several foundational concepts:

### Semantic Layer
The semantic layer bridges raw data and meaningful interpretation. By encoding context, relationships, and intent, systems can reason about information rather than merely process it.

### Retrieval Mechanisms
Effective retrieval combines dense vector search with sparse keyword matching. This hybrid approach ensures both conceptual relevance and exact term matching, addressing diverse query patterns.

### Generation Pipeline
Modern generation pipelines employ multi-stage refinement. Initial drafts undergo iterative improvement through critique models, fact-checking layers, and style alignment processes.

## Implementation Best Practices

### Start with Clear Objectives
Before implementing any solution, articulate specific success criteria. Are you optimizing for latency, accuracy, cost, or some combination? These objectives guide architectural decisions.

### Invest in Data Quality
Even the most sophisticated algorithms cannot overcome poor input data. Establish rigorous preprocessing pipelines, validation rules, and monitoring systems to maintain quality standards.

### Design for Observability
Complex systems fail in complex ways. Comprehensive logging, tracing, and metric collection enable rapid diagnosis when issues arise. Build observability in from the beginning, not as an afterthought.

### Plan for Scale
Initial prototypes often succeed under limited loads but falter at production scale. Design data structures, APIs, and workflows with growth trajectories in mind.

## Common Pitfalls to Avoid

**Over-Engineering Early**
Teams sometimes architect for hypothetical future requirements rather than present needs. Start simple, measure performance, and evolve based on empirical data.

**Neglecting Human Oversight**
Autonomous systems require human judgment for edge cases, ethical considerations, and strategic decisions. Maintain meaningful human control throughout the operational lifecycle.

**Underestimating Integration Complexity**
Connecting new capabilities with existing infrastructure often consumes more effort than building the capabilities themselves. Budget adequate time and resources for integration work.

## Tools and Technologies

The ecosystem supporting {title.lower()} has matured significantly. Key categories include:

- **Vector Databases**: Specialized storage for high-dimensional embeddings, enabling efficient similarity search at scale
- **Orchestration Frameworks**: Systems for coordinating multi-step workflows across heterogeneous services
- **Monitoring Platforms**: Tools for tracking performance, detecting anomalies, and alerting operators
- **Evaluation Suites**: Frameworks for systematically assessing output quality and system behavior

## Future Trends and Predictions

Looking ahead, several trends will likely shape {title.lower()}:

1. **Multimodal Integration**: Text, image, audio, and video processing will converge into unified pipelines
2. **Edge Deployment**: Processing will increasingly occur on edge devices, reducing latency and bandwidth requirements
3. **Federated Approaches**: Distributed learning and inference will enable collaboration without centralizing sensitive data
4. **Regulatory Evolution**: Emerging regulations will mandate transparency, accountability, and fairness in automated systems

## Conclusion

{title.split(':')[0].strip()} represents both significant opportunity and substantial complexity. Organizations that approach it strategically—building solid foundations, measuring rigorously, and iterating based on evidence—will capture disproportionate value.

The journey requires continuous learning, as the field evolves rapidly. However, the fundamentals outlined in this guide provide durable principles that will remain relevant regardless of specific technology choices.

By mastering these concepts and avoiding common pitfalls, teams can build systems that are not only technically sound but also aligned with business objectives and user needs.

---

*Want to learn more? Explore our related content on AI systems architecture, data engineering fundamentals, and modern application design patterns.*
"""
    
    def _format_output(self, title: str, content: str, source: str) -> BlogPost:
        import re
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        final_title = h1_match.group(1).strip() if h1_match else title
        
        content = re.sub(r'^```markdown\s*', '', content)
        content = re.sub(r'\s*```\s*$', '', content)
        
        excerpt = ""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) > 1:
            for p in paragraphs[1:]:
                if not p.startswith('#') and len(p) > 50:
                    excerpt = p[:250]
                    break
        
        keywords = self._extract_keywords(content, title)
        headings = extract_headings(content)
        wc = count_words(content)
        
        return BlogPost(
            title=final_title,
            content=content.strip(),
            excerpt=excerpt,
            keywords=keywords,
            headings=headings,
            word_count=wc,
            source=source,
            internal_links=[]
        )
    
    def _extract_keywords(self, content: str, title: str) -> List[str]:
        import re
        from collections import Counter
        
        text = (title + " " + content).lower()
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                      'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
                      'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
                      'through', 'during', 'before', 'after', 'above', 'below',
                      'between', 'under', 'and', 'but', 'or', 'yet', 'so', 'if',
                      'because', 'although', 'though', 'while', 'where', 'when',
                      'that', 'which', 'who', 'whom', 'whose', 'what', 'this',
                      'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
                      'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its',
                      'our', 'their', 'this', 'that', 'here', 'there', 'all', 'each',
                      'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
                      'no', 'not', 'only', 'own', 'same', 'than', 'too', 'very', 'just'}
        
        words = re.findall(r'\b[a-z]{4,}\b', text)
        filtered = [w for w in words if w not in stop_words]
        common = Counter(filtered).most_common(10)
        keywords = [word.title() for word, count in common]
        
        title_words = [w.title() for w in title.lower().split() 
                      if len(w) > 3 and w not in stop_words]
        
        all_keywords = title_words + keywords
        seen = set()
        deduped = []
        for k in all_keywords:
            kl = k.lower()
            if kl not in seen:
                seen.add(kl)
                deduped.append(k)
        
        return deduped[:8]
