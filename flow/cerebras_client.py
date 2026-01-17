"""Direct Cerebras integration for fast inference."""
import os
import json
from typing import Optional
from cerebras.cloud.sdk import Cerebras
from pydantic import BaseModel

client = Cerebras(api_key=os.environ.get("CEREBRAS_API_KEY"))


class CapturedContext(BaseModel):
    summary: str
    hypothesis: Optional[str] = None
    next_steps: list[str]
    complexity: str
    key_files: list[str]


CAPTURE_PROMPT = """Analyze this developer's current working context and extract key information.

Git State:
- Branch: {branch}
- Modified files: {modified_files}
- Recent commits: {recent_commits}
- Uncommitted changes: {diff_summary}

Respond in JSON format:
{{
    "summary": "One sentence: what they're working on",
    "hypothesis": "Their current theory/approach (null if unclear)",
    "next_steps": ["Likely next action 1", "Likely next action 2"],
    "complexity": "simple|medium|complex",
    "key_files": ["most_important_file.py"]
}}

Be concise and actionable."""


def analyze_context(
    branch: str,
    modified_files: list[str],
    recent_commits: list[str],
    diff_summary: str
) -> CapturedContext:
    """Analyze current context using Cerebras."""

    prompt = CAPTURE_PROMPT.format(
        branch=branch,
        modified_files=", ".join(modified_files) or "None",
        recent_commits="\n".join(recent_commits[-5:]) or "None",
        diff_summary=diff_summary[:2000]
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=500,
        temperature=0.3
    )

    result = response.choices[0].message.content
    return CapturedContext.model_validate_json(result)


RESTORE_PROMPT = """Generate a welcome-back message for a developer.

Their last context:
{context}

What changed while away:
{changes}

Respond in JSON:
{{
    "context_summary": "What you were doing (1 sentence)",
    "hypothesis": "Your working theory (null if none)",
    "changes_impact": "How changes affect your work",
    "suggested_action": "Recommended next step"
}}

Be direct. No fluff."""


def generate_restoration(context: dict, changes: str) -> dict:
    """Generate restoration message."""

    prompt = RESTORE_PROMPT.format(
        context=json.dumps(context, indent=2),
        changes=changes or "No changes detected"
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=300,
        temperature=0.3
    )

    return json.loads(response.choices[0].message.content)
