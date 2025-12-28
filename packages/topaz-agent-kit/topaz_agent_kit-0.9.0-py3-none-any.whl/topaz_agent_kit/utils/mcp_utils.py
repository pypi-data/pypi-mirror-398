"""MCP utility helpers.

This module centralizes common MCP-related helpers to avoid duplication across
framework-specific agent implementations.
"""

from typing import List
from typing import Any
import fnmatch


def matches_tool_patterns(tool_name: str, patterns: List[str], toolkits: List[str] | None = None) -> bool:
    """Return True if a tool name matches any provided wildcard pattern.

    Matching behavior:
    - Supports '*' wildcards (via fnmatchcase)
    - Handles toolkit patterns by converting dots to underscores (e.g., 'math.*' -> 'math_*')
    - Direct pattern matching for custom patterns

    Examples:
    - patterns=['*'] -> allow all
    - patterns=['math.*'] -> allow any tool starting with 'math_'
    - patterns=['search.*'] -> allow any tool starting with 'search_'
    - patterns=['sanitize_*'] -> allow tools whose name matches 'sanitize_*'
    """
    if not patterns:
        return False

    for pattern in patterns:
        if pattern == "*":
            return True

        # Direct match against the full tool name
        if fnmatch.fnmatchcase(tool_name, pattern):
            return True

        # Handle toolkit patterns (e.g., 'math.*' should match 'math_*' tools)
        if '.' in pattern and '*' in pattern:
            # Convert dot pattern to underscore pattern (e.g., 'math.*' -> 'math_*')
            underscore_pattern = pattern.replace('.', '_')
            if fnmatch.fnmatchcase(tool_name, underscore_pattern):
                return True

    return False

def invoke_llm(llm: Any, prompt_text: str) -> str:
    """
    Invoke an LLM with the given prompt text.

    Args:
        llm: The LLM to invoke.
        prompt_text: The prompt text to invoke the LLM with.

    Returns:
        The response from the LLM.

    Raises:
        RuntimeError: If the LLM is not configured or the LLM type is unsupported.
        RuntimeError: If the response from the LLM is empty.
        RuntimeError: If the response from the LLM is not a string.
        RuntimeError: If the response from the LLM is not a valid JSON.
        RuntimeError: If the response from the LLM is not a valid JSON.
    """
    if llm is None:
        raise RuntimeError("LLM is not configured")

    content = None
    if hasattr(llm, "invoke"):
        # LangChain-style model
        msg = llm.invoke(prompt_text)
        content = getattr(msg, "content", None) if msg is not None else None
    elif hasattr(llm, "chat") and hasattr(llm.chat, "completions"):
        # OpenAI client (Azure)
        resp = llm.chat.completions.create(
            model=getattr(llm, "_azure_deployment", None) or getattr(llm, "model", None),
            messages=[{"role": "user", "content": prompt_text}],
        )
        if resp and getattr(resp, "choices", None):
            content = resp.choices[0].message.content
    else:
        raise RuntimeError(f"Unsupported LLM type: {type(llm)}")

    text = (content or "").strip()
    if not text:
        raise RuntimeError("Empty response from LLM")
    return text
