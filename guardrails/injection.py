"""guardrails/injection.py — Prompt injection detection."""
import re
from typing import Tuple

# common patterns used in prompt injection attacks
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|context)",
    r"forget\s+(everything|all|previous|your\s+instructions)",
    r"you\s+are\s+now\s+(a|an|the)\s+\w+",
    r"new\s+instructions?[:.]",
    r"system\s*prompt",
    r"disregard\s+(your|the|all)\s+(instructions?|rules?|guidelines?)",
    r"act\s+as\s+(if\s+you\s+are|a|an)\s+",
    r"do\s+anything\s+now",
    r"jailbreak",
    r"bypass\s+(your|the)\s+(safety|filter|restriction|guideline)",
    r"reveal\s+(the\s+)?(system|hidden|secret)\s+(prompt|instructions?)",
    r"admin\s+password",
    r"override\s+(your|the)\s+(instructions?|programming|rules?)",
    r"pretend\s+(you\s+are|to\s+be)\s+",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def check_injection(query: str) -> Tuple[bool, str]:
    """
    Check if the query contains prompt injection patterns.

    Returns (is_injection: bool, matched_pattern: str)
    """
    for pattern in _compiled:
        match = pattern.search(query)
        if match:
            return True, match.group(0)
    return False, ""


def get_injection_response() -> str:
    """Standard refusal message for detected injection attempts."""
    return (
        "This query appears to contain a prompt injection attempt and has been blocked. "
        "Please ask a genuine question about company policies, data, or use the available tools."
    )
