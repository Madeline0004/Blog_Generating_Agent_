"""Configuration management for the blog generation agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_BLOGS_DIR = DATA_DIR / "sample_blogs"
GENERATED_DIR = DATA_DIR / "generated"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"

# Ensure directories exist
for d in [DATA_DIR, SAMPLE_BLOGS_DIR, GENERATED_DIR, VECTOR_STORE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# Model Configuration
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Agent Configuration
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.75"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "128"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Vector Store
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", str(VECTOR_STORE_DIR))
INDEX_REFRESH_HOURS = int(os.getenv("INDEX_REFRESH_HOURS", "24"))

# Output
DEFAULT_OUTPUT_DIR = os.getenv("DEFAULT_OUTPUT_DIR", str(GENERATED_DIR))
