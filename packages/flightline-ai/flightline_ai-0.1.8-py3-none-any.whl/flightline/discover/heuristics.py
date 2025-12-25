"""Heuristic-based AI call detection.

Finds "AI footprints" in code that don't use known SDKs, such as
custom internal wrappers, niche providers, or LangChain/LlamaIndex.
"""

import re
from pathlib import Path
from typing import List, Optional

from flightline.discover.detect import DetectedCall
from flightline.discover.schema import CallType, Location, Provider

# =============================================================================
# SIGNATURES - The "DNA" of an LLM call
# =============================================================================

# Patterns that strongly indicate an LLM message structure
MESSAGE_PATTERNS = [
    r"role",
    r"content",
    r"system",
    r"assistant",
    r"user",
]

# Patterns for common LLM parameters
PARAM_PATTERNS = [
    r"temperature",
    r"max_tokens",
    r"top_p",
    r"frequency_penalty",
    r"presence_penalty",
    r"stop_sequences",
    r"logit_bias",
]

# Combined list for detection
ALL_PATTERNS = MESSAGE_PATTERNS + PARAM_PATTERNS


def detect_heuristic_calls(file_path: Path) -> List[DetectedCall]:
    """
    Detect AI calls using heuristic signatures.

    Args:
        file_path: Path to source file

    Returns:
        List of detected calls
    """
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    lines = source.splitlines()
    detected_calls: List[DetectedCall] = []

    # Use a sliding window to find clusters of AI signatures
    window_size = 20
    i = 0
    while i < len(lines):
        window = "\n".join(lines[i : i + window_size])

        matches = 0
        found_patterns = []
        for pattern in ALL_PATTERNS:
            if re.search(pattern, window, re.IGNORECASE):
                matches += 1
                found_patterns.append(pattern)

        # If we find 3 or more distinct signatures in a small window,
        # it's highly likely to be an AI operation.
        if matches >= 3:
            # Find the first line in the window that actually matches one of the patterns
            line_num = i + 1
            for j, line in enumerate(lines[i : i + window_size]):
                if any(re.search(p, line, re.IGNORECASE) for p in found_patterns):
                    line_num = i + j + 1
                    break

            detected_calls.append(
                DetectedCall(
                    location=Location(
                        file=str(file_path),
                        line=line_num,
                        function=_get_function_context(lines, line_num),
                    ),
                    provider=Provider.UNKNOWN,
                    call_type=CallType.CHAT,
                    method_chain="heuristic_match",
                    raw_args=window,
                    function_context=_get_function_context(lines, line_num),
                )
            )
            # Move index past this window to avoid duplicate detections
            i += window_size
        else:
            i += 1

    return detected_calls


def _get_function_context(lines: List[str], line_num: int) -> Optional[str]:
    """Look backwards from a line to find the containing function name."""
    # Matches def name(...) or function name(...) or const name = ... =>
    func_pattern = re.compile(
        r"(?:def\s+|function\s+|async\s+function\s+|const\s+\w+\s*=\s*(?:async\s+)?(?:\([^)]*\)|[\w]+)\s*=>)\s*(\w+)"
    )

    # Search backwards up to 50 lines
    start_idx = max(0, line_num - 1)
    for i in range(start_idx, max(-1, start_idx - 50), -1):
        line = lines[i]
        match = func_pattern.search(line)
        if match:
            return match.group(1)

    return None
