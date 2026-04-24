# Blog Generation Agent

An AI-powered agent that automates end-to-end blog generation workflow including semantic search over existing content, SEO research, blog writing, and featured image generation.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BLOG GENERATION AGENT                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  INPUT: Blog Title                                                  │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────────┐     ┌──────────────────────┐                       │
│  │   Step 1     │────▶│  Semantic Search     │                       │
│  │ Check Existing│    │  Over Blog Library   │                       │
│  │    Blogs     │    └──────────────────────┘                       │
│  └──────────────┘              │                                    │
│                                │                                    │
│                    ┌───────────┴───────────┐                       │
│                    │                       │                       │
│                    ▼                       ▼                       │
│           Similar Found           No Similar Found                  │
│                │                       │                           │
│                ▼                       ▼                           │
│      ┌─────────────────┐    ┌──────────────────┐                    │
│      │    Step 2A      │    │     Step 2B      │                    │
│      │ Use Existing Blog│    │  External SEO    │                    │
│      │   as Reference   │    │    Research      │                    │
│      │                  │    │  (Web Search +   │                    │
│      │ • Structure      │    │   Scraping)      │                    │
│      │ • Tone           │    │                  │                    │
│      │ • Keywords       │    │ • Top Rankings   │                    │
│      │ • Internal Links │    │ • Content Struct │                    │
│      └────────┬────────┘    │ • Word Count     │                    │
│               │              │ • Keyword Usage  │                    │
│               │              └────────┬─────────┘                    │
│               │                       │                             │
│               └───────────┬───────────┘                             │
│                           │                                        │
│                           ▼                                        │
│                  ┌─────────────────┐                              │
│                  │    Step 3       │                              │
│                  │  Generate Blog  │                              │
│                  │                 │                              │
│                  │ • SEO Optimized │                              │
│                  │ • H1, H2 Structure│                            │
│                  │ • Competitive Length│                          │
│                  │ • Company Tone  │                              │
│                  └────────┬────────┘                              │
│                           │                                       │
│                           ▼                                       │
│                  ┌─────────────────┐                              │
│                  │   Step 4        │                              │
│                  │ Generate Image  │                              │
│                  │   (Optional)    │                              │
│                  └────────┬────────┘                              │
│                           │                                       │
│                           ▼                                       │
│  OUTPUT: Publication-ready Blog Post + Featured Image               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Blog Retrieval Pipeline (RAG)

**Ingestion Flow:**
```
Raw Blog Markdown
      │
      ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Chunking  │───▶│  Embedding  │───▶│   FAISS     │───▶│  Metadata   │
│  (512/128)  │    │  (all-MiniLM)│    │   Index     │    │   Store     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

**Chunking Strategy:**
- **Chunk Size:** 512 tokens (approximately 400-500 words)
- **Overlap:** 128 tokens (25% overlap)
- **Why:** This preserves semantic context at paragraph boundaries while keeping chunks small enough for precise retrieval. The overlap ensures no critical context is lost at chunk boundaries.
- **Indexing Trigger:** Index is built on-demand when blogs are ingested, and can be refreshed incrementally

**Retrieval:**
- Dense retrieval using cosine similarity on sentence embeddings
- Top-k chunks retrieved and re-ranked by relevance score
- Metadata includes: blog title, URL, publish date, section headings

### 2. Agent Orchestration

State machine with these states:
- `INIT`: Receive title, validate input
- `CHECK_LIBRARY`: Perform semantic search
- `BRANCH`: Decision point
  - `USE_EXISTING`: Retrieve and analyze existing blog
  - `SEO_RESEARCH`: Perform external research
- `GENERATE`: Create blog post with appropriate context
- `GENERATE_IMAGE`: Create featured image (optional)
- `OUTPUT`: Return final blog post

Error handling at each state with graceful fallbacks.

### 3. SEO Research

Uses web search API to:
1. Search for top-ranking content on target keyword
2. Scrape/analyze content structure (headings, word count)
3. Identify content gaps and optimal angles

### 4. LLM Integration

Prompt management system with:
- System prompts for each step
- Context window management (chunked context, token counting)
- Temperature and parameter tuning per step

## Setup Instructions

### Prerequisites
- Python 3.9+
- OpenAI API key (or Anthropic/Gemini)
- Tavily API key (for SEO research)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd blog_generation_agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running the Agent

```bash
# Basic usage
python -m src.main "How to Build a RAG Pipeline"

# With options
python -m src.main "AI Agent Orchestration" --generate-image --output-dir ./data/generated
```

### Running Tests

```bash
pytest tests/
```

## Project Structure

```
blog_generation_agent/
├── README.md                     # This file
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── src/
│   ├── __init__.py
│   ├── config.py                 # Configuration management
│   ├── main.py                   # CLI entry point
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py            # Pydantic data models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── blog_retrieval.py     # RAG: ingestion, indexing, retrieval
│   │   ├── seo_research.py       # Web search and content analysis
│   │   ├── blog_generator.py     # LLM blog generation
│   │   ├── image_generator.py    # Featured image generation
│   │   └── publisher.py          # Output formatting
│   ├── agent/
│   │   ├── __init__.py
│   │   └── orchestrator.py       # Agent state machine
│   └── utils/
│       ├── __init__.py
│       ├── chunking.py           # Text chunking utilities
│       ├── embeddings.py         # Embedding model wrapper
│       ├── vector_store.py       # FAISS vector store
│       └── helpers.py            # General utilities
├── data/
│   ├── sample_blogs/             # Sample existing blogs
│   └── generated/                # Generated blog outputs
└── tests/
    └── test_pipeline.py          # Pipeline tests
```

## Component Explanations

### Blog Retrieval Service (`blog_retrieval.py`)

This is the most critical component. It implements the full RAG pipeline:

1. **Ingestion**: Reads blog files, extracts text and metadata
2. **Chunking**: Uses recursive character chunking with 512 token chunks and 128 token overlap
3. **Embedding**: Uses `sentence-transformers/all-MiniLM-L6-v2` for dense embeddings (384 dimensions)
4. **Indexing**: Builds FAISS index (IndexFlatIP - Inner Product for cosine similarity)
5. **Retrieval**: Searches index with query embedding, returns top-k chunks with metadata

**Why FAISS?** FAISS is chosen for its simplicity, speed, and lack of external dependencies (no need for Pinecone/Weaviate accounts). For production, this can be swapped for a managed vector DB.

**Why all-MiniLM-L6-v2?** It provides excellent performance for semantic similarity at a small size (80MB), runs locally without API calls, and is well-suited for document retrieval.

**Index Freshness**: The index is built when blogs are ingested. A timestamp check can trigger re-indexing when blogs are updated.

### SEO Research Service (`seo_research.py`)

Uses Tavily API for research:
- Searches for top results on target topic
- Analyzes content structure from search results
- Returns competitive analysis: word counts, heading structures, content angles

### Blog Generator Service (`blog_generator.py`)

Uses OpenAI GPT-4 (or configured LLM) to:
- Construct detailed prompts based on research context
- Generate H1, H2s, introduction, body, conclusion
- Ensure SEO optimization and company tone matching
- Manage context window by passing only relevant chunks

### Agent Orchestrator (`orchestrator.py`)

Implements the decision logic:
1. Checks similarity score threshold (default 0.75) for existing blog match
2. Routes to appropriate branch based on match
3. Handles failures with fallback strategies
4. Composes final output from all steps

## Known Limitations

1. **LLM API Required**: You need a valid OpenAI API key (or alternative) to generate blogs. The retrieval pipeline works without it.
2. **SEO Research Rate Limits**: Tavily free tier has rate limits. For heavy usage, a paid plan is recommended.
3. **Image Generation Optional**: Featured image generation requires additional API credits.
4. **Vector Store In-Memory**: FAISS index is held in memory. For very large blog libraries, consider using FAISS with disk persistence or a managed vector DB.
5. **Web Scraping Fragility**: Content analysis depends on page structure which can change.

## Sample Output

See `data/generated/` for sample blog posts generated by the agent, including:
- Full markdown blog post
- Featured image
- Metadata JSON with SEO analysis

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Embeddings | all-MiniLM-L6-v2 | Local, fast, sufficient quality |
| Vector DB | FAISS | Simple, no external service needed |
| Chunking | 512/128 tokens | Balance of precision and context |
| LLM | OpenAI GPT-4 | Best quality for long-form content |
| Search | Tavily | Optimized for AI agent research |
| Image | DALL-E 3 | Best prompt adherence |

## License

MIT
