"""Heuristic-based AI call detection.

Finds "AI footprints" in code that don't use known SDKs, such as
custom internal wrappers, niche providers, or LangChain/LlamaIndex.
"""

import re
from pathlib import Path
from typing import Optional

from flightline.discover.detect import DetectedCall
from flightline.discover.schema import CallType, Location, Provider

# =============================================================================
# SIGNATURES - The "DNA" of an LLM call
# =============================================================================

# Patterns that strongly indicate an LLM message structure
MESSAGE_PATTERNS = [
    r"role",
    r"content",
]

# Patterns for common LLM parameters
PARAM_PATTERNS = [
    r"temperature",
    r"max_tokens",
    r"model",
    r"top_p",
    r"presence_penalty",
    r"frequency_penalty",
    r"stop_sequences",
    r"system_prompt",
]

# Combined patterns for a "Footprint Cluster"
ALL_PATTERNS = MESSAGE_PATTERNS + PARAM_PATTERNS


# =============================================================================
# DETECTION LOGIC
# =============================================================================


def detect_heuristic_calls(file_path: Path) -> list[DetectedCall]:
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
    detected_calls: list[DetectedCall] = []

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
            # to give a more accurate location than just the start of the window.
            match_offset = 0
            for j, line in enumerate(lines[i : i + window_size]):
                if any(re.search(pattern, line, re.IGNORECASE) for pattern in ALL_PATTERNS):
                    match_offset = j
                    break

            line_num = i + match_offset + 1
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


def _get_function_context(lines: list[str], line_num: int) -> Optional[str]:
    """Find the function name containing a line (simple heuristic)."""
    # Simple regex for function definitions in Python and JS/TS
    func_pattern = re.compile(
        r"(?:def\s+|function\s+|async\s+function\s+|const\s+\w+\s*=\s*(?:async\s+)?(?:\([^)]*\)|[\w]+)\s*=>)\s*(\w+)"
    )

    for i in range(line_num - 1, -1, -1):
        if i >= len(lines):
            continue
        match = func_pattern.search(lines[i])
        if match:
            return match.group(1)

    return None
