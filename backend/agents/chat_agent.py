"""
Chat Agent -- Enables Conversational BI (Chat with your Data) over report context.

Responsibilities:
- Answer natural language questions about specific reports
- Use report measurements and findings as context
- Provide concise, data-driven responses
"""

import json
from openai import AsyncOpenAI
from backend.agents.base_agent import BaseAgent
from backend.config import get_settings
from backend.database.db import DatabaseClient

CHAT_SYSTEM_PROMPT = """You are an expert business analyst chat assistant. 
You are helping a user understand a specific operational report.

Your context includes:
1. The full Markdown report content.
2. Structured measurements (aggregations).
3. AI Insights (findings, anomalies, recommendations).

Rules:
- Answer ONLY based on the provided data. If the data doesn't contain the answer, say so.
- Be concise and professional.
- Use numbers and specific trends from the data.
- If the user asks for a chart description, explain what the data shows.
- If the user asks about an anomaly, explain why it was flagged.

Context for the current report:
{context}
"""

class ChatAgent(BaseAgent):
    def __init__(self, db: DatabaseClient):
        super().__init__(name="chat_agent", db=db)
        settings = get_settings()
        self.llm = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def chat(self, report_data: dict, user_query: str, chat_history: list = []) -> str:
        self.logger.info(f"Processing chat query for report: {report_data.get('title')}")

        # 1. Build context
        context = self._build_chat_context(report_data)

        # 2. Prepare messages
        messages = [
            {"role": "system", "content": CHAT_SYSTEM_PROMPT.format(context=context)},
        ]
        
        # Add history
        for msg in chat_history[-6:]:  # Keep last 3 exchanges
            messages.append(msg)
            
        # Add current query
        messages.append({"role": "user", "content": user_query})

        # 3. Get LLM response
        response = await self.llm.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0,  # Factual response
            max_tokens=1000,
        )

        if response.usage:
            self.tokens_used += response.usage.total_tokens

        answer = response.choices[0].message.content.strip()
        
        # Log the interaction
        await self.log_agent_run(
            run_id="chat-" + str(report_data.get("id")), 
            step="chat_query",
            status="completed",
            input_data={"query": user_query},
            output_data={"answer": answer}
        )

        return answer

    def _build_chat_context(self, report_data: dict) -> str:
        """Condensed report context for the chat prompt."""
        lines = []
        lines.append(f"Report Title: {report_data.get('title')}")
        lines.append(f"Generated At: {report_data.get('created_at')}")
        
        # Summary
        insights = report_data.get("insights", {})
        if insights.get("executive_summary"):
            lines.append(f"Executive Summary: {insights['executive_summary']}")
            
        # Top 5 Measurements
        measurements = report_data.get("measurements", [])
        if measurements:
            lines.append("--- KEY MEASUREMENTS (TOP 5) ---")
            for m in measurements[:5]:
                lines.append(f"  {json.dumps(m)}")
        
        # Detection Feed
        anomalies = insights.get("anomalies_detected", [])
        if anomalies:
            lines.append("--- DETECTED ANOMALIES ---")
            for a in anomalies:
                lines.append(f"  {a.get('severity').upper()}: {a.get('description')}")

        return "\n".join(lines)
