
"""
QueryMind — Prompt Injection Detection
Basic heuristic-based prompt injection detection.
"""
import structlog
import re
from typing import Tuple, Optional

logger = structlog.get_logger(__name__)

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"disregard\s+previous",
    r"forget\s+everything",
    r"you\s+are\s+now",
    r"pretend\s+you\s+are",
    r"act\s+as",
    r"system\s+prompt",
    r"initial\s+prompt",
    r"reveal\s+your\s+instructions",
    r"show\s+your\s+prompt",
    r"what\s+are\s+your\s+rules",
    r"bypass\s+security",
    r"override\s+restrictions",
    r"drop\s+table",
    r"delete\s+from",
    r"update\s+.*set",
    r"union\s+select",
    r"--\s*",
    r";\s*",
    r"\/\*.*\*\/",
]


def detect_prompt_injection(input_text: str) -> Tuple[bool, Optional[str]]:
    """
    Detect potential prompt injection in user input.
    Returns (is_suspicious, reason).
    """
    input_lower = input_text.lower()

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, input_lower, re.IGNORECASE):
            logger.warning("Potential prompt injection detected", pattern=pattern, input=input_text[:100])
            return True, f"Input matched suspicious pattern: {pattern}"

    return False, None
