"""
Embedding Agent -- Handles vector embeddings for RAG-based report search.

Responsibilities:
- Generate embeddings for report content using OpenAI text-embedding-3-small
- Manage vector index for semantic search
"""

from typing import List
from openai import AsyncOpenAI
from backend.agents.base_agent import BaseAgent
from backend.config import get_settings
from backend.database.db import DatabaseClient

class EmbeddingAgent(BaseAgent):
    def __init__(self, db: DatabaseClient):
        super().__init__(name="embedding_agent", db=db)
        settings = get_settings()
        self.llm = AsyncOpenAI(api_key=settings.openai_api_key)
        self.embedding_model = "text-embedding-3-small"

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate a vector embedding for the given text."""
        self.logger.info("Generating embedding...")
        
        # Cleanup text: Limit length for embedding stability
        text = text.replace("\n", " ")[:8000]
        
        response = await self.llm.embeddings.create(
            input=[text],
            model=self.embedding_model
        )
        
        # text-embedding-3-small generates 1536-dimensional vectors
        return response.data[0].embedding

    async def run(self, input_data: dict) -> dict:
        """
        Agent entry point. Expects 'report_id', 'title', and 'content'.
        """
        report_id = input_data.get("report_id")
        title = input_data.get("title")
        content = input_data.get("content")
        
        if not all([report_id, title, content]):
            raise ValueError("EmbeddingAgent requires 'report_id', 'title', and 'content'.")
            
        await self.index_report(report_id, title, content)
        return {"status": "indexed", "report_id": report_id}

    async def index_report(self, report_id: str, title: str, content: str):
        """Generate and save embedding for a specific report."""
        text_to_embed = f"{title}\n\n{content}"
        embedding = await self.generate_embedding(text_to_embed)
        
        try:
            # We'll try to insert into report_embeddings table. 
            self.db.client.table("report_embeddings").upsert({
                "report_id": report_id,
                "embedding": embedding,
                "metadata": {"title": title}
            }).execute()
            self.logger.info(f"Report {report_id} indexed successfully.")
        except Exception as e:
            self.logger.error(f"Failed to index report {report_id}: {e}")
            raise e
