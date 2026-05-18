"""
AI Agent — constructs prompts, calls Claude, parses structured responses.
Handles confidence routing and topic classification.
"""

import os
import json
from anthropic import Anthropic
from pydantic import BaseModel

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=anthropic_api_key) if anthropic_api_key else None


class AgentResponse(BaseModel):
    topic: str
    confidence: float
    answer: str
    escalate: bool = False
    sources: list[str] = []


SYSTEM_PROMPT = """You are HRBot, an intelligent HR Helpdesk Assistant embedded inside the Promtal HR platform.
You help employees resolve questions about payroll, leave, HR policies, benefits, and onboarding — instantly and accurately.

PERSONA & TONE:
- Professional but warm. Speak like a helpful HR colleague, not a legal document.
- Use plain language. Avoid jargon.
- Address the employee by first name if provided.
- Never fabricate policy details. If unsure, say so.

TOPIC CATEGORIES (pick exactly one):
PAYROLL | LEAVE | ONBOARDING | POLICY | BENEFITS | GENERAL

STRICT RULES:
1. Answer using ONLY the "Policy Context" provided below. Do NOT invent facts.
2. If the context does not contain a clear answer, set confidence below 0.6.
3. Cite the policy source (document name + section) when quoting policy.
4. Keep answers under 200 words unless detail is needed.
5. Use markdown bullet points for step-by-step processes.
6. End every answer with: "Does this answer your question? You can also type **'HR'** to speak with the HR team."

BOUNDARIES — refuse these outright:
- Compensation of other employees
- Legal advice (advise consulting an employment lawyer)
- Personal data of other employees
- Performance reviews or promotion decisions
- Requests to bypass HR processes

OUTPUT FORMAT — respond with **valid JSON only**, no markdown fences:
{
  "topic": "<TOPIC_CATEGORY>",
  "confidence": <float 0.0–1.0>,
  "answer": "<markdown formatted response>",
  "sources": ["<source_file (section)>", ...]
}
"""


def generate_response(
    query: str,
    employee_name: str,
    context: str,
    conversation_history: list[dict] | None = None,
) -> AgentResponse:
    """
    Build the prompt, call Claude, and return a structured AgentResponse.
    Falls back gracefully if the API key is missing.
    """
    if not client:
        return AgentResponse(
            topic="GENERAL",
            confidence=0.0,
            answer=(
                "⚠️ The Anthropic API key is not configured. "
                "Please set `ANTHROPIC_API_KEY` in your `.env` file and restart the server."
            ),
            escalate=True,
        )

    user_message = f"""
Employee Name: {employee_name}
Query: {query}

Policy Context:
{context if context else "No relevant policy documents found in the knowledge base."}
"""

    messages = []
    # Include conversation history for multi-turn awareness
    if conversation_history:
        for msg in conversation_history[-6:]:  # last 3 turns
            messages.append(msg)
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
        )

        raw = response.content[0].text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        parsed = json.loads(raw)

        topic = parsed.get("topic", "GENERAL")
        confidence = float(parsed.get("confidence", 0.0))
        answer = parsed.get("answer", "I'm unable to process that request.")
        sources = parsed.get("sources", [])

        # Escalation triggers
        escalation_keywords = ["speak to hr", "talk to hr", "connect me with hr", "harassment", "termination"]
        keyword_escalate = any(kw in query.lower() for kw in escalation_keywords)
        escalate = confidence < 0.6 or keyword_escalate

        return AgentResponse(
            topic=topic,
            confidence=confidence,
            answer=answer,
            escalate=escalate,
            sources=sources,
        )

    except json.JSONDecodeError:
        return AgentResponse(
            topic="GENERAL",
            confidence=0.3,
            answer="I had trouble processing that. Let me connect you with the HR team for a precise answer.",
            escalate=True,
        )
    except Exception as e:
        print(f"Claude API error: {e}")
        return AgentResponse(
            topic="GENERAL",
            confidence=0.0,
            answer=f"An error occurred while contacting the AI service: {str(e)}",
            escalate=True,
        )
