"""
SEO Research Service - External research when no existing blog exists.

Uses web search to analyze top-ranking content and determine optimal
content angle, structure, and keywords.
"""

import os
import re
from typing import List, Dict, Optional
from src.config import TAVILY_API_KEY
from src.models.schemas import SEOAnalysis


class SEOResearchService:
    """
    Service for external SEO research using web search APIs.
    
    Primary: Tavily Search API (free tier: 1000 credits/month)
    Fallback: Mock research for demonstration/testing
    
    Research Pipeline:
    1. Search for target keyword/topic
    2. Analyze top results for content structure
    3. Extract common headings, word counts, content angles
    4. Identify gaps and recommend approach
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or TAVILY_API_KEY
        self.has_api_key = bool(self.api_key)
    
    def research_topic(self, title: str) -> SEOAnalysis:
        """
        Perform SEO research on a topic.
        
        If Tavily API key is available, performs real web search.
        Otherwise, returns mock research for demonstration.
        """
        if self.has_api_key:
            try:
                return self._real_research(title)
            except Exception as e:
                print(f"Real research failed ({e}), falling back to mock")
                return self._mock_research(title)
        else:
            print("No Tavily API key configured, using mock research")
            return self._mock_research(title)
    
    def _real_research(self, title: str) -> SEOAnalysis:
        """Perform real SEO research using Tavily API."""
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.api_key)
            
            # Search for the topic
            response = client.search(
                query=title,
                search_depth="advanced",
                max_results=10,
                include_answer=True
            )
            
            results = response.get('results', [])
            
            # Analyze top results
            top_rankings = []
            word_counts = []
            all_headings = []
            competitor_structures = []
            
            for result in results[:5]:
                content = result.get('content', '')
                url = result.get('url', '')
                result_title = result.get('title', '')
                
                # Estimate word count from content snippet
                wc = len(content.split())
                word_counts.append(wc)
                
                # Extract headings if content is substantial
                headings = self._extract_headings_from_text(content)
                all_headings.extend(headings)
                
                top_rankings.append({
                    'url': url,
                    'title': result_title,
                    'content_snippet': content[:500] if content else '',
                    'score': result.get('score', 0)
                })
                
                competitor_structures.append({
                    'title': result_title,
                    'url': url,
                    'word_count': wc,
                    'headings': headings[:5]  # Top 5 headings
                })
            
            # Calculate averages and find patterns
            avg_word_count = int(sum(word_counts) / len(word_counts)) if word_counts else 1500
            common_headings = self._find_common_patterns(all_headings)
            
            # Generate content gaps
            content_gaps = self._identify_gaps(title, common_headings)
            
            # Recommended angle
            recommended_angle = self._determine_angle(title, results)
            
            return SEOAnalysis(
                target_keyword=title,
                top_rankings=top_rankings,
                avg_word_count=avg_word_count,
                common_headings=common_headings,
                content_gaps=content_gaps,
                recommended_angle=recommended_angle,
                competitor_structures=competitor_structures
            )
            
        except ImportError:
            print("tavily package not installed, falling back to mock")
            return self._mock_research(title)
        except Exception as e:
            print(f"Error in real research: {e}")
            return self._mock_research(title)
    
    def _mock_research(self, title: str) -> SEOAnalysis:
        """Generate mock SEO research for demonstration purposes."""
        # Create plausible research based on the title
        keywords = title.lower().split()
        
        mock_rankings = [
            {
                'url': 'https://example.com/comprehensive-guide',
                'title': f'The Complete Guide to {title}',
                'content_snippet': f'Learn everything about {title}. This comprehensive guide covers all aspects...',
                'score': 0.92
            },
            {
                'url': 'https://techblog.com/best-practices',
                'title': f'{title}: Best Practices for 2024',
                'content_snippet': f'In this article, we explore the best practices for {title}...',
                'score': 0.88
            },
            {
                'url': 'https://howtogeek.com/tutorial',
                'title': f'How to Master {title} - Step by Step',
                'content_snippet': f'A step-by-step tutorial on mastering {title}...',
                'score': 0.85
            }
        ]
        
        common_headings = [
            f'Introduction to {title}',
            'Why This Matters',
            'Key Concepts and Terminology',
            'Step-by-Step Implementation',
            'Common Pitfalls to Avoid',
            'Best Practices and Tips',
            'Tools and Resources',
            'Conclusion'
        ]
        
        content_gaps = [
            f'Beginner-friendly explanation of {title}',
            'Real-world case studies and examples',
            'Performance benchmarks and comparisons',
            'Integration with other technologies'
        ]
        
        return SEOAnalysis(
            target_keyword=title,
            top_rankings=mock_rankings,
            avg_word_count=1800,
            common_headings=common_headings,
            content_gaps=content_gaps,
            recommended_angle=f'A comprehensive, practical guide to {title} that bridges theory and implementation, targeting intermediate practitioners.',
            competitor_structures=[
                {
                    'title': mock_rankings[0]['title'],
                    'url': mock_rankings[0]['url'],
                    'word_count': 2200,
                    'headings': common_headings[:4]
                },
                {
                    'title': mock_rankings[1]['title'],
                    'url': mock_rankings[1]['url'],
                    'word_count': 1500,
                    'headings': common_headings[2:6]
                }
            ]
        )
    
    def _extract_headings_from_text(self, text: str) -> List[str]:
        """Extract heading-like patterns from text snippets."""
        lines = text.split('\n')
        headings = []
        
        for line in lines:
            line = line.strip()
            # Look for bold text that looks like headings
            if line.startswith('**') and line.endswith('**') and len(line) < 100:
                headings.append(line.strip('*'))
            # Look for numbered sections
            elif re.match(r'^\d+\.\s+\w+', line) and len(line) < 100:
                headings.append(line)
        
        return headings[:10]  # Limit to top 10
    
    def _find_common_patterns(self, headings: List[str]) -> List[str]:
        """Find common heading patterns from a list."""
        if not headings:
            return []
        
        # Simple frequency-based extraction
        from collections import Counter
        # Normalize headings
        normalized = [h.lower().strip() for h in headings if len(h) > 3]
        common = Counter(normalized).most_common(8)
        return [h.title() for h, _ in common]
    
    def _identify_gaps(self, title: str, common_headings: List[str]) -> List[str]:
        """Identify potential content gaps."""
        gaps = []
        
        title_lower = title.lower()
        
        # Check for common gaps
        if 'beginner' not in ' '.join(common_headings).lower():
            gaps.append(f'Beginner-friendly introduction to {title}')
        if 'example' not in ' '.join(common_headings).lower():
            gaps.append('Practical examples and code snippets')
        if 'tool' not in ' '.join(common_headings).lower():
            gaps.append('Tool comparisons and recommendations')
        if 'troubleshoot' not in ' '.join(common_headings).lower() and 'error' not in ' '.join(common_headings).lower():
            gaps.append('Troubleshooting common issues')
        if 'future' not in ' '.join(common_headings).lower() and 'trend' not in ' '.join(common_headings).lower():
            gaps.append('Future trends and predictions')
        
        # Always add some default gaps
        if len(gaps) < 3:
            gaps.extend([
                f'Integration of {title} with existing workflows',
                'Cost-benefit analysis and ROI considerations',
                'Security implications and best practices'
            ])
        
        return gaps[:5]
    
    def _determine_angle(self, title: str, results: List[Dict]) -> str:
        """Determine the best content angle based on research."""
        # Analyze what type of content ranks well
        listicles = sum(1 for r in results if any(w in r.get('title', '').lower() 
                        for w in ['top', 'best', '10', '5', 'guide']))
        
        if listicles > len(results) / 2:
            return f'A structured, list-based approach to {title} that provides actionable takeaways for each point.'
        else:
            return f'A comprehensive, in-depth guide to {title} that covers fundamentals through advanced topics with practical examples.'
