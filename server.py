from fastapi import FastAPI
from pydantic import BaseModel
import sys
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
import os

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.orchestrator import AgentOrchestrator
from src.services.blog_retrieval import BlogRetrievalService
from src.config import SAMPLE_BLOGS_DIR

app = FastAPI(title="Blog Generation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    title: str
    generate_image: bool = False

@app.on_event("startup")
def startup_event():
    # Setup library if not already populated
    try:
        retrieval = BlogRetrievalService()
        stats = retrieval.get_blog_stats()
        if stats['total_vectors'] == 0:
            print("Populating sample blog library...")
            retrieval.ingest_blogs(SAMPLE_BLOGS_DIR)
    except Exception as e:
        print(f"Error initializing library: {e}")

@app.post("/api/generate")
async def generate_blog(req: GenerateRequest):
    try:
        orchestrator = AgentOrchestrator()
        output = orchestrator.run(
            title=req.title,
            generate_image=req.generate_image,
        )
        return {"status": "success", "data": output.model_dump()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
