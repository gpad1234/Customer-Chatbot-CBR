"""LLM refinement layer: uses OpenAI to polish the CBR-retrieved answer.

The CBR answer is passed as grounded context — the LLM is instructed to
rephrase it naturally without adding new information.  Falls back to the
raw CBR answer if OPENAI_API_KEY is not set or the call fails.
"""
from __future__ import annotations

import os

from chatbot.orchestrator import CBRResponse

_SYSTEM_PROMPT = """\
You are a friendly, professional customer support agent.
You will be given a verified solution retrieved from our knowledge base.
Your job is to rephrase it as a warm, clear, first-person reply to the customer.
IMPORTANT: Do NOT add any information that is not present in the verified solution.
Keep the reply concise (2–4 sentences max). Do not mention "verified solution" or "knowledge base".\
"""


def refine(problem: str, cbr_result: CBRResponse) -> str:
    """Return a polished reply, using OpenAI if available.

    Parameters
    ----------
    problem:
        The original customer query.
    cbr_result:
        The result from the CBR orchestrator.

    Returns
    -------
    A natural-language response string.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return cbr_result.answer  # graceful fallback

    try:
        from openai import OpenAI  # lazy import

        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            max_tokens=200,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Customer message: {problem}\n\n"
                        f"Verified solution: {cbr_result.answer}"
                    ),
                },
            ],
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        return cbr_result.answer  # fallback on any error
