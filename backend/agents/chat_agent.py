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

CHAT_SYSTEM_PROMPT = """You are a senior Business Strategy & Operations Analyst.
Your goal is to help the user extract maximum value from their operational reports.

Your context includes:
1. The FULL Markdown report (primary source of truth).
2. Structured measurements and KPIs.
3. Analysis insights and anomalies.

Capabilities & Guidelines:
- Strategic Advice: Provide concrete, actionable advice on business growth, cost reduction, and operational efficiency.
- Data-Driven: Always cite specific numbers, percentages, and trends from the data.
- Proactive Analysis: If the data shows a decline or an opportunity, point it out even if not directly asked.
- Improvement Focus: When asked 'how to improve', combine the report's recommendations with your own strategic reasoning based on the metrics.
- Clarity: Use bullet points for complex advice.

Context for the current report:
{context}
"""

class ChatAgent(BaseAgent):
    def __init__(self, db: DatabaseClient):
        super().__init__(name="chat_agent", db=db)
        settings = get_settings()
        self.llm = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def run(self, input_data: dict) -> dict:
        """
        Agent entry point. Expects 'report_data', 'user_query', and optionally 'chat_history'.
        """
        report_data = input_data.get("report_data")
        user_query = input_data.get("user_query")
        chat_history = input_data.get("chat_history", [])
        
        if not report_data or not user_query:
            raise ValueError("ChatAgent requires 'report_data' and 'user_query'.")
            
        answer = await self.chat(report_data, user_query, chat_history)
        return {"answer": answer}

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
            temperature=0.2, # Slightly more creative for advice
            max_tokens=1500,
        )

        if response.usage:
            self.tokens_used += response.usage.total_tokens

        answer = response.choices[0].message.content.strip()
        return answer

    def _build_chat_context(self, report_data: dict) -> str:
        """Full contextual assembly for the chat prompt."""
        lines = []
        lines.append(f"Report Title: {report_data.get('title')}")
        lines.append(f"Generated At: {report_data.get('created_at')}")
        
        # 1. Primary Report Text (CRITICAL)
        markdown = report_data.get("content_markdown", "")
        if markdown:
            lines.append("\n=== FULL REPORT CONTENT ===")
            lines.append(markdown)
        
        # 2. Key Insights
        insights = report_data.get("insights", {})
        if insights:
            lines.append("\n=== STRUCTURED INSIGHTS ===")
            lines.append(json.dumps(insights, indent=2))
            
        # 3. Measurements
        measurements = report_data.get("measurements", [])
        if measurements:
            lines.append("\n=== STRUCTURED MEASUREMENTS ===")
            lines.append(json.dumps(measurements[:10], indent=2))

        return "\n".join(lines)
